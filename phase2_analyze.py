"""Phase 2: KataGo analysis of eligible games (resumable).
Usage: python phase2_analyze.py [--max N]"""
import sqlite3, subprocess, json, time, re, os, sys, signal, argparse

DB = "games.db"
ROOT = "games"
KATAGO = r"C:\Users\User\Documents\KaTrain\_internal\katrain\KataGo\katago.exe"
MODEL = r"C:\Users\User\Documents\KaTrain\_internal\katrain\models\kata1-b18c384nbt-s9996604416-d4316597426.bin.gz"
CONFIG = r"C:\Users\User\Documents\KaTrain\_internal\katrain\KataGo\analysis_config.cfg"
MAX_VISITS = 500
DEVIATION_THRESHOLD = 5.0

SGF_COLS = 'abcdefghijklmnopqrs'
GTP_COLS = 'ABCDEFGHJKLMNOPQRST'
S2G_COL = {SGF_COLS[i]: GTP_COLS[i] for i in range(19)}
S2G_ROW = {SGF_COLS[i]: 19 - i for i in range(19)}

INTERRUPTED = False

def sgf_to_gtp(s):
    if s in ('', 'tt'):
        return 'pass'
    return f'{S2G_COL[s[0]]}{S2G_ROW[s[1]]}'

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
        SELECT g.id, g.filepath, g.score_points, g.komi, g.num_moves, g.result_raw
        FROM games g
        WHERE g.result_type = 'score'
          AND g.board_size = 19
          AND g.num_moves >= 100
          AND NOT EXISTS (SELECT 1 FROM analysis a WHERE a.game_id = g.id)
        ORDER BY g.id
    """
    if max_games is not None:
        sql += f" LIMIT {int(max_games)}"
    return con.execute(sql).fetchall()

def analyze_game(katago, game):
    game_id, rel_path, score_points, komi, num_moves, result_raw = game
    filepath = os.path.join(ROOT, rel_path)

    moves = parse_moves(filepath)
    if not moves:
        return None

    target_turn = max(num_moves - 100, 1)
    if target_turn > len(moves):
        target_turn = len(moves)

    query = {
        'id': str(game_id),
        'rules': 'japanese',
        'komi': komi,
        'boardXSize': 19, 'boardYSize': 19,
        'maxVisits': MAX_VISITS,
        'analyzeTurns': [target_turn],
        'includeOwnership': False, 'includePolicy': False,
        'initialStones': [], 'initialPlayer': 'B',
        'moves': moves[:target_turn],
        'overrideSettings': {'reportAnalysisWinratesAs': 'BLACK'}
    }

    t0 = time.time()
    katago.stdin.write((json.dumps(query) + '\n').encode())
    katago.stdin.flush()

    line = katago.stdout.readline()
    elapsed = time.time() - t0
    if not line:
        return None

    try:
        resp = json.loads(line)
    except json.JSONDecodeError:
        return None

    if 'error' in resp:
        print(f"    Error: {resp['error'][:100]}")
        return None

    ri = resp.get('rootInfo', {})
    score_lead = ri.get('scoreLead', 0)
    winrate = ri.get('winrate', 0)
    visits = ri.get('visits', 0)
    deviation = abs(score_lead - score_points)

    return {
        'game_id': game_id,
        'turn_analyzed': target_turn,
        'score_lead': score_lead,
        'winrate': winrate,
        'deviation': deviation,
        'visits': visits,
        'time_taken': elapsed,
        'pass': deviation <= DEVIATION_THRESHOLD,
    }

def main():
    global INTERRUPTED

    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, default=None, help='Max games to analyze this run')
    args = parser.parse_args()

    def on_signal(sig, frame):
        global INTERRUPTED
        INTERRUPTED = True
        print("\n*** Interrupt received, finishing current query and exiting...")

    signal.signal(signal.SIGINT, on_signal)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")

    pending = get_pending_games(con, max_games=args.max)
    total = len(pending)
    print(f"Games to analyze: {total}")

    katago = start_katago()
    print("Starting KataGo...")
    time.sleep(5)
    print("Ready.\n")

    analyzed = 0
    passed = 0
    errors = 0
    start_time = time.time()
    session_start = start_time

    for i, game in enumerate(pending):
        if INTERRUPTED:
            break

        result = None
        for attempt in range(3):
            try:
                result = analyze_game(katago, game)
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
            if i % 100 == 0:
                print(f"  [{i}/{total}] skipping game {game[0]} (error)")
            continue

        analyzed += 1
        if result['pass']:
            passed += 1

        con.execute("""
            INSERT OR REPLACE INTO analysis
                (game_id, turn_analyzed, score_lead, winrate, deviation, visits, time_taken)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (result['game_id'], result['turn_analyzed'], result['score_lead'],
              result['winrate'], result['deviation'], result['visits'], result['time_taken']))
        con.commit()

        # Progress every game
        elapsed = time.time() - session_start
        rate = (i + 1) / elapsed * 3600  # games/hour
        remaining = total - (i + 1)
        eta = remaining / rate if rate > 0 else 0

        print(f"  [{i+1}/{total}] {'PASS' if result['pass'] else 'fail'}  "
              f"game={game[0]}  dev={result['deviation']:.1f}  "
              f"sc={result['score_lead']:+.1f} act={game[2]:+.1f}  "
              f"{rate:.0f} g/h  ETA {eta:.1f}h  passed={passed}")

    # Cleanup
    con.close()
    try:
        katago.terminate()
    except Exception:
        pass

    total_elapsed = time.time() - start_time
    print(f"\n=== Complete ===")
    print(f"Analyzed: {analyzed}  Passed: {passed}  Errors: {errors}")
    print(f"Time: {total_elapsed/3600:.1f} hours")

if __name__ == '__main__':
    main()
