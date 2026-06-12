"""
Phase 3 — Verify: KataGo Chinese final query for eligible games.

For each eligible game not yet verified:
  - Query KataGo with Chinese rules on the final position
  - Compute chinese_score from ownership
  - Set verified=1 if abs(chinese_score - score_points) <= 1.5

This is cheap — one KataGo query per eligible game.
Resumable: skips games that already have chinese_score computed.

Usage: python phase3_verify.py [--max GAMES] [--visits V]
"""
import sqlite3, subprocess, json, time, os, sys, signal, argparse
from backend.migrations import apply_games_db
from backend.sgf import parse_moves

DB = "games.db"
ROOT = "games"
KATAGO = r"C:\Users\User\Documents\KaTrain\_internal\katrain\KataGo\katago.exe"
MODEL = r"C:\Users\User\Documents\KaTrain\_internal\katrain\models\kata1-b18c384nbt-s9996604416-d4316597426.bin.gz"
CONFIG = r"C:\Users\User\Documents\KaTrain\_internal\katrain\KataGo\analysis_config.cfg"

THRESHOLD = 1.5

INTERRUPTED = False


def start_katago():
    return subprocess.Popen(
        [KATAGO, 'analysis', '-config', CONFIG, '-model', MODEL],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )


def get_pending(con, max_games=None):
    sql = """
        SELECT g.filepath, g.score_points, g.komi, g.num_moves
        FROM games g
        WHERE g.eligible = 1
          AND g.chinese_score IS NULL
        ORDER BY g.filepath
    """
    params = []
    if max_games is not None:
        sql += " LIMIT ?"
        params.append(int(max_games))
    return con.execute(sql, params).fetchall()


def query_chinese_final(katago, game, max_visits):
    rel_path, score_points, komi, num_moves = game
    filepath = os.path.join(ROOT, rel_path)

    with open(filepath, 'rb') as f:
        text = f.read().decode('utf-8', errors='replace')
    moves = parse_moves(text)
    if not moves:
        return None

    query = {
        'id': 'c{}'.format(rel_path),
        'rules': 'chinese',
        'komi': 7.0,
        'boardXSize': 19, 'boardYSize': 19,
        'maxVisits': max_visits,
        'analyzeTurns': [len(moves)],
        'includeOwnership': True, 'includePolicy': False,
        'initialStones': [], 'initialPlayer': 'B',
        'moves': moves,
        'overrideSettings': {'reportAnalysisWinratesAs': 'BLACK'},
    }

    katago.stdin.write((json.dumps(query) + '\n').encode())
    katago.stdin.flush()

    line = katago.stdout.readline()
    if not line:
        return None

    try:
        resp = json.loads(line)
    except json.JSONDecodeError:
        return None

    if 'error' in resp:
        print("    Chinese query error: {}".format(resp['error'][:100]))
        return None

    ownership = resp.get('ownership')
    if not ownership or len(ownership) != 361:
        return None

    area_diff = sum(ownership)
    chinese_score = area_diff - 7.0
    return round(chinese_score / 2) * 2


def main():
    global INTERRUPTED

    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, default=None, help='Max games this run')
    parser.add_argument('--visits', type=int, default=1000, help='KataGo visits for final query')
    args = parser.parse_args()

    def on_signal(sig, frame):
        global INTERRUPTED
        INTERRUPTED = True
        print("\n*** Interrupt received, finishing current query and exiting...")

    signal.signal(signal.SIGINT, on_signal)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    apply_games_db(DB)

    pending = get_pending(con, max_games=args.max)
    print("Eligible games awaiting verification: {}".format(len(pending)))

    if not pending:
        con.close()
        print("Nothing to do.")
        return

    katago = start_katago()
    print("Starting KataGo...")
    time.sleep(5)
    print("Ready.\n")

    verified = 0
    mismatch = 0
    failed = 0
    session_start = time.time()

    for i, game in enumerate(pending):
        if INTERRUPTED:
            break

        rel_path, score_points, komi, num_moves = game

        chinese = query_chinese_final(katago, game, args.visits)
        if chinese is None:
            failed += 1
            print("[{:3d}/{}] {}  FAILED".format(i + 1, len(pending), rel_path))
            continue

        match = abs(chinese - score_points) <= THRESHOLD
        con.execute(
            "UPDATE games SET chinese_score = ?, verified = ? WHERE filepath = ?",
            (chinese, 1 if match else 0, rel_path),
        )
        con.commit()

        if match:
            verified += 1
            status = "VERIFIED"
        else:
            mismatch += 1
            status = "MISMATCH"

        print("[{:3d}/{}] {}  score={}  chinese={}  {}".format(
            i + 1, len(pending), rel_path, score_points, chinese, status,
        ))
        sys.stdout.flush()

    con.close()
    try:
        katago.terminate()
    except Exception:
        pass

    elapsed = time.time() - session_start
    print("\n=== Phase 3 Complete ===")
    print("Verified: {}  Mismatch: {}  Failed: {}".format(verified, mismatch, failed))
    print("Time: {:.1f} min".format(elapsed / 60))


if __name__ == '__main__':
    main()
