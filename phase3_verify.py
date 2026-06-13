"""
Phase 3 — Verify: KataGo Chinese final query for eligible games.

For each eligible game not yet verified:
  - Query KataGo with Chinese rules on the final position
  - Compute chinese_score from ownership
  - Set verified=1 if abs(chinese_score - score_points) <= 1.5

Queries are pipelined: up to WINDOW games are in flight at once so the GPU
stays saturated (the analysis engine tags each response with the query id).
Resumable: skips games that already have chinese_score computed.

Usage: python phase3_verify.py [--max GAMES] [--visits V]
                               [--katago EXE] [--model BIN] [--config CFG]
"""
import sqlite3, json, time, os, sys, signal, argparse, queue
from collections import deque
from backend.migrations import apply_games_db
from backend.sgf import parse_moves
from katago_engine import Engine, add_engine_args, STDERR_LOG

DB = "games.db"
ROOT = "games"

THRESHOLD = 1.5
WINDOW = 64
COMMIT_EVERY = 20
MAX_RESTARTS = 5

INTERRUPTED = False


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


def build_query(game, max_visits):
    rel_path = game[0]
    filepath = os.path.join(ROOT, rel_path)

    try:
        with open(filepath, 'rb') as f:
            text = f.read().decode('utf-8', errors='replace')
    except OSError:
        return None
    moves = parse_moves(text)
    if not moves:
        return None

    return {
        'id': 'c|' + rel_path,
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


def chinese_score_from(resp):
    ownership = resp.get('ownership')
    if not ownership or len(ownership) != 361:
        return None
    area_diff = sum(ownership)
    return round((area_diff - 7.0) / 2) * 2


def main():
    global INTERRUPTED

    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, default=None, help='Max games this run')
    parser.add_argument('--visits', type=int, default=1000, help='KataGo visits for final query')
    parser.add_argument('--window', type=int, default=WINDOW, help='Game queries in flight at once')
    add_engine_args(parser)
    args = parser.parse_args()

    def on_signal(sig, frame):
        global INTERRUPTED
        INTERRUPTED = True
        print("\n*** Interrupt received, draining in-flight queries and exiting...")

    signal.signal(signal.SIGINT, on_signal)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    apply_games_db(DB)

    pending = deque(get_pending(con, max_games=args.max))
    total = len(pending)
    print("Eligible games awaiting verification: {}".format(total))
    print("KataGo: {}".format(args.katago))

    if not pending:
        con.close()
        print("Nothing to do.")
        return

    engine = Engine(args.katago, args.model, args.config)
    print("Starting KataGo (responses begin once the model is loaded)...\n")

    in_flight = {}
    done = verified = mismatch = failed = 0
    uncommitted = 0
    restarts = 0
    session_start = time.time()

    while pending or in_flight:
        while pending and len(in_flight) < args.window and not INTERRUPTED:
            game = pending.popleft()
            query = build_query(game, args.visits)
            if query is None:
                done += 1
                failed += 1
                print("[{:5d}/{}] {}  FAILED (no moves)".format(done, total, game[0]))
                continue
            in_flight[query['id']] = game
            try:
                engine.send(query)
            except OSError:
                break  # engine died; the None sentinel below handles resubmission

        if not in_flight:
            break

        try:
            line = engine.lines.get(timeout=1.0)
        except queue.Empty:
            continue

        if line is None:
            restarts += 1
            if restarts > MAX_RESTARTS:
                print("KataGo keeps dying; aborting. See {}".format(STDERR_LOG))
                break
            print("KataGo died; restarting and resubmitting {} games...".format(len(in_flight)))
            engine.restart()
            try:
                for game in in_flight.values():
                    query = build_query(game, args.visits)
                    if query is not None:
                        engine.send(query)
            except OSError:
                pass
            continue

        try:
            resp = json.loads(line)
        except json.JSONDecodeError:
            continue

        game = in_flight.pop(resp.get('id'), None)
        if game is None:
            continue
        restarts = 0

        rel_path, score_points, komi, num_moves = game
        done += 1

        if 'error' in resp:
            failed += 1
            print("[{:5d}/{}] {}  FAILED: {}".format(done, total, rel_path, str(resp['error'])[:100]))
            continue

        chinese = chinese_score_from(resp)
        if chinese is None:
            failed += 1
            print("[{:5d}/{}] {}  FAILED (no ownership)".format(done, total, rel_path))
            continue

        match = abs(chinese - score_points) <= THRESHOLD
        con.execute(
            "UPDATE games SET chinese_score = ?, verified = ? WHERE filepath = ?",
            (chinese, 1 if match else 0, rel_path),
        )
        uncommitted += 1
        if uncommitted >= COMMIT_EVERY:
            con.commit()
            uncommitted = 0

        if match:
            verified += 1
            status = "VERIFIED"
        else:
            mismatch += 1
            status = "MISMATCH"

        elapsed = time.time() - session_start
        rate = done / elapsed * 3600 if elapsed > 0 else 0
        print("[{:5d}/{}] {}  score={}  chinese={}  {}  ({:.0f} games/h)".format(
            done, total, rel_path, score_points, chinese, status, rate,
        ))
        sys.stdout.flush()

    con.commit()
    con.close()
    engine.stop()

    elapsed = time.time() - session_start
    print("\n=== Phase 3 Complete ===")
    print("Verified: {}  Mismatch: {}  Failed: {}".format(verified, mismatch, failed))
    print("Time: {:.1f} min".format(elapsed / 60))


if __name__ == '__main__':
    main()
