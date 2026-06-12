"""Phase 2: Batch-analyze every qualifying turn of every game for predictive positions.
Resumable. One KataGo query per batch of 50 turns.

Usage: python phase2_analyze.py [--max GAMES] [--visits V]
"""
import sqlite3, subprocess, json, time, re, os, sys, signal, argparse

DB = "games.db"
ROOT = "games"
KATAGO = r"C:\Users\User\Documents\KaTrain\_internal\katrain\KataGo\katago.exe"
MODEL = r"C:\Users\User\Documents\KaTrain\_internal\katrain\models\kata1-b18c384nbt-s9996604416-d4316597426.bin.gz"
CONFIG = r"C:\Users\User\Documents\KaTrain\_internal\katrain\KataGo\analysis_config.cfg"

BATCH_SIZE = 50
MIN_TURN = 76
MIN_FROM_END = 50

SGF_COLS = 'abcdefghijklmnopqrs'
GTP_COLS = 'ABCDEFGHJKLMNOPQRST'
S2G_COL = {SGF_COLS[i]: GTP_COLS[i] for i in range(19)}
S2G_ROW = {SGF_COLS[i]: 19 - i for i in range(19)}

INTERRUPTED = False


def sgf_to_gtp(s):
    if s in ('', 'tt'):
        return 'pass'
    return '{}{}'.format(S2G_COL[s[0]], S2G_ROW[s[1]])


def parse_moves(filepath):
    with open(filepath, 'rb') as f:
        text = f.read().decode('utf-8', errors='replace')
    moves = []
    for m in re.finditer(r';(B|W)\[([a-z]{2}|tt|)\]', text):
        moves.append([m.group(1), sgf_to_gtp(m.group(2))])
    return moves


def start_katago():
    return subprocess.Popen(
        [KATAGO, 'analysis', '-config', CONFIG, '-model', MODEL],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )


def get_pending_games(con, max_games=None):
    sql = """
        SELECT g.id, g.filepath, g.score_points, g.komi, g.num_moves
        FROM games g
        WHERE g.result_type = 'score'
          AND g.board_size = 19
          AND g.num_moves >= ?
        ORDER BY g.id
    """
    params = [MIN_TURN + MIN_FROM_END]
    if max_games is not None:
        sql += " LIMIT ?"
        params.append(int(max_games))
    return con.execute(sql, params).fetchall()


def get_pending_turns(con, game_id, num_moves):
    max_turn = num_moves - MIN_FROM_END
    all_turns = list(range(MIN_TURN, max_turn + 1))
    if not all_turns:
        return []

    existing = con.execute(
        "SELECT turn FROM game_positions WHERE game_id = ?",
        (game_id,),
    ).fetchall()
    existing_set = {e[0] for e in existing}

    return [t for t in all_turns if t not in existing_set]


def analyze_batch(katago, game, batch_turns, max_visits):
    game_id, rel_path, score_points, komi, num_moves = game
    filepath = os.path.join(ROOT, rel_path)

    moves = parse_moves(filepath)
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
        'id': str(game_id),
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
            results.append({
                'game_id': game_id,
                'turn': turn,
                'score_lead': score_lead,
                'visits': visits,
            })

    return results


def query_chinese_final(katago, game, max_visits):
    game_id, rel_path, score_points, komi, num_moves = game
    filepath = os.path.join(ROOT, rel_path)

    moves = parse_moves(filepath)
    if not moves:
        return None

    query = {
        'id': 'c{}'.format(game_id),
        'rules': 'chinese',
        'komi': 7.0,
        'boardXSize': 19, 'boardYSize': 19,
        'maxVisits': max_visits,
        'analyzeTurns': [len(moves)],
        'includeOwnership': False, 'includePolicy': False,
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

    ri = resp.get('rootInfo', {})
    return ri.get('scoreLead', 0)


def needs_chinese_score(con, game_id):
    row = con.execute(
        "SELECT chinese_score FROM games WHERE id = ?",
        (game_id,),
    ).fetchone()
    return row and row[0] is None


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
    con.execute("""
        CREATE TABLE IF NOT EXISTS game_positions (
            game_id INTEGER NOT NULL REFERENCES games(id),
            turn INTEGER NOT NULL,
            score_lead REAL,
            visits INTEGER,
            PRIMARY KEY (game_id, turn)
        )
    """)
    try:
        con.execute("ALTER TABLE games ADD COLUMN chinese_score REAL")
    except sqlite3.OperationalError:
        pass
    con.commit()

    pending = get_pending_games(con, max_games=args.max)
    print("Games to process: {}".format(len(pending)))
    print("Visits per turn: {}".format(args.visits))
    print("Batch size: {}".format(BATCH_SIZE))

    # Count total pending turns
    total_turns = 0
    for game in pending:
        turns = get_pending_turns(con, game[0], game[4])
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

    for game in pending:
        if INTERRUPTED:
            break

        game_id, rel_path, score_points, komi, num_moves = game
        turns = get_pending_turns(con, game_id, num_moves)
        if not turns:
            continue

        game_turns_done = 0
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
                    "INSERT OR IGNORE INTO game_positions (game_id, turn, score_lead, visits) VALUES (?, ?, ?, ?)",
                    (r['game_id'], r['turn'], r['score_lead'], r['visits']),
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
                game_id,
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

        if needs_chinese_score(con, game_id):
            chinese = query_chinese_final(katago, game, args.visits)
            if chinese is not None:
                con.execute(
                    "UPDATE games SET chinese_score = ? WHERE id = ?",
                    (chinese, game_id),
                )
                con.commit()
                print("  [G{} Chinese score: {:.1f}]".format(game_id, chinese))
                sys.stdout.flush()
            else:
                print("  [G{} Chinese query failed]".format(game_id))

    con.close()
    try:
        katago.terminate()
    except Exception:
        pass

    elapsed = time.time() - session_start
    print("\n=== Complete ===")
    print("Turns analyzed: {}".format(turns_done))
    print("Batches: {}".format(batches_done))
    print("Errors: {}".format(errors))
    print("Time: {:.1f} hours".format(elapsed / 3600))


if __name__ == '__main__':
    main()
