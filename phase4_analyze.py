"""
Phase 4 — Analyze: Per-turn KataGo analysis for verified games.

For each verified game:
  - Analyze turns in [MIN_TURN .. num_moves - MIN_FROM_END] via batch queries
  - Store score_lead in game_analysis
  - Set close_score=1 where abs(score_lead - chinese_score) <= 1.5

Resumable — skips turns already present in game_analysis.

Usage: python phase4_analyze.py [--max GAMES] [--visits V]
"""
import sqlite3, subprocess, json, time, os, sys, signal, argparse
from backend.migrations import apply_games_db
from backend.sgf import parse_moves

DB = "games.db"
ROOT = "games"
KATAGO = r"C:\Users\User\Documents\KaTrain\_internal\katrain\KataGo\katago.exe"
MODEL = r"C:\Users\User\Documents\KaTrain\_internal\katrain\models\kata1-b18c384nbt-s9996604416-d4316597426.bin.gz"
CONFIG = r"C:\Users\User\Documents\KaTrain\_internal\katrain\KataGo\analysis_config.cfg"

BATCH_SIZE = 50
MIN_TURN = 76
MIN_FROM_END = 50
CLOSE_THRESHOLD = 1.5

INTERRUPTED = False


def start_katago():
    return subprocess.Popen(
        [KATAGO, 'analysis', '-config', CONFIG, '-model', MODEL],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )


def get_verified_games(con, max_games=None):
    sql = """
        SELECT g.filepath, g.score_points, g.komi, g.num_moves, g.chinese_score
        FROM games g
        WHERE g.verified = 1
        ORDER BY g.filepath
    """
    params = []
    if max_games is not None:
        sql += " LIMIT ?"
        params.append(int(max_games))
    return con.execute(sql, params).fetchall()


def get_pending_turns(con, filepath, num_moves):
    max_turn = num_moves - MIN_FROM_END
    all_turns = list(range(MIN_TURN, max_turn + 1))
    if not all_turns:
        return []

    existing = con.execute(
        "SELECT turn FROM game_analysis WHERE filepath = ?",
        (filepath,),
    ).fetchall()
    existing_set = {e[0] for e in existing}

    return [t for t in all_turns if t not in existing_set]


def analyze_batch(katago, game, batch_turns, max_visits):
    rel_path, score_points, komi, num_moves, chinese_score = game
    filepath = os.path.join(ROOT, rel_path)

    with open(filepath, 'rb') as f:
        text = f.read().decode('utf-8', errors='replace')
    moves = parse_moves(text)
    if not moves:
        return None

    max_turn = max(batch_turns)
    if max_turn > len(moves):
        batch_turns = [t for t in batch_turns if t <= len(moves)]
        if not batch_turns:
            return None
        max_turn = max(batch_turns)

    moves_to_send = moves[:max_turn]

    query = {
        'id': str(rel_path),
        'rules': 'japanese',
        'komi': komi,
        'boardXSize': 19, 'boardYSize': 19,
        'maxVisits': max_visits,
        'analyzeTurns': batch_turns,
        'includeOwnership': False, 'includePolicy': False,
        'initialStones': [], 'initialPlayer': 'B',
        'moves': moves_to_send,
        'overrideSettings': {'reportAnalysisWinratesAs': 'BLACK'},
    }

    t0 = time.time()
    katago.stdin.write((json.dumps(query) + '\n').encode())
    katago.stdin.flush()

    results = []
    for _ in range(len(batch_turns)):
        line = katago.stdout.readline()
        elapsed = time.time() - t0
        if not line:
            break
        try:
            resp = json.loads(line)
        except json.JSONDecodeError:
            continue
        if 'error' in resp:
            print("    Error: {}".format(resp['error'][:100]))
            continue

        turn = resp.get('turnNumber')
        ri = resp.get('rootInfo', {})
        score_lead = ri.get('scoreLead', 0)
        visits = ri.get('visits', 0)

        if turn is not None:
            close = 1 if chinese_score is not None and abs(score_lead - chinese_score) <= CLOSE_THRESHOLD else 0
            results.append({
                'filepath': rel_path,
                'turn': turn,
                'score_lead': score_lead,
                'visits': visits,
                'close_score': close,
            })

    return results


def main():
    global INTERRUPTED

    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, default=None, help='Max games this run')
    parser.add_argument('--visits', type=int, default=1000, help='KataGo visits per turn')
    args = parser.parse_args()

    def on_signal(sig, frame):
        global INTERRUPTED
        INTERRUPTED = True
        print("\n*** Interrupt received, finishing current batch and exiting...")

    signal.signal(signal.SIGINT, on_signal)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    apply_games_db(DB)

    games = get_verified_games(con, max_games=args.max)
    print("Verified games to process: {}".format(len(games)))
    print("Visits per turn: {}".format(args.visits))
    print("Batch size: {}".format(BATCH_SIZE))

    total_turns = 0
    for game in games:
        turns = get_pending_turns(con, game[0], game[3])
        total_turns += len(turns)
    print("Pending turns total: {}".format(total_turns))
    print("Estimated batches: ~{}".format(-(-total_turns // BATCH_SIZE)))
    if total_turns > 0:
        est_hours = total_turns * (2.5 / BATCH_SIZE) * (args.visits / 500.0) / 3600
        print("Estimated time: ~{:.1f} hours".format(est_hours))

    katago = start_katago()
    print("Starting KataGo...")
    time.sleep(5)
    print("Ready.\n")

    turns_done = 0
    batches_done = 0
    errors = 0
    session_start = time.time()

    for game in games:
        if INTERRUPTED:
            break

        rel_path, score_points, komi, num_moves, chinese_score = game
        turns = get_pending_turns(con, rel_path, num_moves)

        game_turns_done = 0
        if turns:
            for batch_start in range(0, len(turns), BATCH_SIZE):
                if INTERRUPTED:
                    break

                batch_turns = turns[batch_start:batch_start + BATCH_SIZE]

                result = None
                for attempt in range(3):
                    try:
                        result = analyze_batch(katago, game, batch_turns, args.visits)
                        break
                    except (BrokenPipeError, OSError):
                        print("  KataGo process died, restarting...")
                        try:
                            katago.terminate()
                        except Exception:
                            pass
                        katago = start_katago()
                        time.sleep(5)

                if result is None:
                    errors += 1
                    continue

                batch_turns_done = 0
                for r in result:
                    con.execute(
                        "INSERT OR IGNORE INTO game_analysis (filepath, turn, score_lead, visits, close_score) VALUES (?, ?, ?, ?, ?)",
                        (r['filepath'], r['turn'], r['score_lead'], r['visits'], r['close_score']),
                    )
                    batch_turns_done += 1
                con.commit()

                game_turns_done += batch_turns_done
                turns_done += batch_turns_done
                batches_done += 1

                elapsed = time.time() - session_start
                rate = turns_done / elapsed * 3600 if elapsed > 0 else 0
                remaining = total_turns - turns_done
                eta = remaining / rate if rate > 0 else 0
                print("  [G{} batch {}/{}]  batch_turns={}  total_done={}/{}  {:.0f} t/h  ETA {:.1f}h".format(
                    rel_path,
                    batch_start // BATCH_SIZE + 1,
                    -(-len(turns) // BATCH_SIZE),
                    batch_turns_done,
                    turns_done,
                    total_turns,
                    rate,
                    eta,
                ))
                sys.stdout.flush()

        if INTERRUPTED:
            break

    con.close()
    try:
        katago.terminate()
    except Exception:
        pass

    elapsed = time.time() - session_start
    print("\n=== Phase 4 Complete ===")
    print("Turns analyzed: {}".format(turns_done))
    print("Batches: {}".format(batches_done))
    print("Errors: {}".format(errors))
    print("Time: {:.1f} hours".format(elapsed / 3600))


if __name__ == '__main__':
    main()
