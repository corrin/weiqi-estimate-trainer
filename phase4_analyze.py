"""
Phase 4 — Analyze: per-turn KataGo score tracking for verified games.

For each verified game, analyze turns in [MIN_TURN .. num_moves - MIN_FROM_END]
with Chinese rules and komi 7.0 — the same setup phase 3 used to compute
chinese_score, so "current score" and "final score" are in the same scoring
system. Every turn is analyzed at VISITS visits and stored with its raw
score_lead; close_score=1 where abs(score_lead - chinese_score) <= CLOSE_THRESHOLD.

Because every turn keeps its full-visit score_lead, CLOSE_THRESHOLD can be
re-derived later in SQL without re-running KataGo.

Games are processed closest-final-margin first (highest puzzle yield per
GPU-hour). Queries are pipelined: up to GAMES_IN_FLIGHT games at once, one
query per game (the analysis engine tags responses with id + turnNumber).
Resumable — skips turns already in game_analysis; a game's rows commit only
once the game is fully analyzed.

--shard I/N splits the verified games deterministically (crc32 of filepath)
across N independent workers; run one shard per GPU/machine.

Usage: python phase4_analyze.py [--max GAMES] [--shard I/N] [--visits V]
                                [--katago EXE] [--model BIN] [--config CFG]
(To wipe game_analysis after a methodology change, run reset_analysis.py.)
"""
import sqlite3, json, time, os, sys, signal, argparse, queue, zlib
from collections import deque
from backend.migrations import apply_games_db
from backend.sgf import parse_moves
from katago_engine import Engine, add_engine_args, STDERR_LOG

DB = "games.db"
ROOT = "games"

MIN_TURN = 76
MIN_FROM_END = 50
CLOSE_THRESHOLD = 1.5
VISITS = 1000
GAMES_IN_FLIGHT = 8
MAX_RESTARTS = 5

INTERRUPTED = False


class GameState:
    def __init__(self, game, moves, turns):
        self.game = game              # (filepath, score_points, komi, num_moves, chinese_score)
        self.moves = moves
        self.turns = turns
        self.awaiting = set(turns)
        self.scores = {}              # turn -> (score_lead, visits)

    @property
    def rel_path(self):
        return self.game[0]

    @property
    def chinese_score(self):
        return self.game[4]


def get_verified_games(con, max_games=None, shard=None):
    # Closest final margins first: those games yield the most close-score
    # puzzles per GPU-hour, so the app's pool grows fastest.
    rows = con.execute("""
        SELECT g.filepath, g.score_points, g.komi, g.num_moves, g.chinese_score
        FROM games g
        WHERE g.verified = 1
        ORDER BY ABS(g.score_points), g.filepath
    """).fetchall()
    if shard is not None:
        i, n = shard
        rows = [r for r in rows if zlib.crc32(r[0].encode()) % n == i]
    if max_games is not None:
        rows = rows[:int(max_games)]
    return rows


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


def load_state(game, turns):
    rel_path = game[0]
    filepath = os.path.join(ROOT, rel_path)
    try:
        with open(filepath, 'rb') as f:
            text = f.read().decode('utf-8', errors='replace')
    except OSError:
        return None
    moves = parse_moves(text)
    turns = [t for t in turns if t <= len(moves)]
    if not moves or not turns:
        return None
    return GameState(game, moves, turns)


def turn_query(qid, moves, turns, visits):
    turns = sorted(turns)
    return {
        'id': qid,
        'rules': 'chinese',
        'komi': 7.0,
        'boardXSize': 19, 'boardYSize': 19,
        'maxVisits': visits,
        'analyzeTurns': turns,
        'includeOwnership': False, 'includePolicy': False,
        'initialStones': [], 'initialPlayer': 'B',
        'moves': moves[:max(turns)],
        'overrideSettings': {'reportAnalysisWinratesAs': 'BLACK'},
    }


def main():
    global INTERRUPTED

    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, default=None, help='Max games this run')
    parser.add_argument('--shard', default=None,
                        help='I/N: process only games whose crc32(filepath) %% N == I (for parallel workers)')
    parser.add_argument('--visits', type=int, default=VISITS, help='Visits per turn')
    parser.add_argument('--games-in-flight', type=int, default=GAMES_IN_FLIGHT)
    add_engine_args(parser)
    args = parser.parse_args()

    def on_signal(sig, frame):
        global INTERRUPTED
        INTERRUPTED = True
        print("\n*** Interrupt received, draining in-flight games and exiting...")

    signal.signal(signal.SIGINT, on_signal)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    apply_games_db(DB)

    shard = None
    if args.shard:
        i, n = (int(x) for x in args.shard.split('/'))
        if not (0 <= i < n):
            parser.error("--shard must be I/N with 0 <= I < N")
        shard = (i, n)

    games = get_verified_games(con, max_games=args.max, shard=shard)
    print("Verified games to process: {}{}".format(
        len(games), "  (shard {}/{})".format(*shard) if shard else ""))
    print("Visits per turn: {}".format(args.visits))
    print("KataGo: {}".format(args.katago))

    pending = deque()
    total_turns = 0
    for game in games:
        turns = get_pending_turns(con, game[0], game[3])
        if turns:
            pending.append((game, turns))
            total_turns += len(turns)
    print("Games with pending turns: {}   Pending turns total: {}".format(len(pending), total_turns))

    if not pending:
        con.close()
        print("Nothing to do.")
        return

    engine = Engine(args.katago, args.model, args.config)
    print("Starting KataGo (responses begin once the model is loaded)...\n")

    in_flight = {}    # rel_path -> GameState
    turns_done = 0
    games_done = 0
    close_total = 0
    errors = 0
    restarts = 0
    session_start = time.time()

    def finalize(st):
        nonlocal turns_done, games_done, close_total
        chinese = st.chinese_score
        rows = []
        for t in st.turns:
            lead, visits = st.scores[t]
            close = 1 if abs(lead - chinese) <= CLOSE_THRESHOLD else 0
            rows.append((st.rel_path, t, lead, visits, close))
        con.executemany(
            "INSERT OR REPLACE INTO game_analysis (filepath, turn, score_lead, visits, close_score) VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        con.commit()

        n_close = sum(1 for r in rows if r[4] == 1)
        turns_done += len(st.turns)
        games_done += 1
        close_total += n_close

        elapsed = time.time() - session_start
        rate = turns_done / elapsed * 3600 if elapsed > 0 else 0
        remaining = total_turns - turns_done
        eta = remaining / rate if rate > 0 else 0
        print("  [{}] turns={}  puzzles={}  total {}/{}  {:.0f} t/h  ETA {:.1f}h".format(
            st.rel_path, len(st.turns), n_close, turns_done, total_turns, rate, eta))
        sys.stdout.flush()

    def resubmit_all():
        for st in in_flight.values():
            engine.send(turn_query(st.rel_path, st.moves, st.awaiting, args.visits))

    while pending or in_flight:
        while pending and len(in_flight) < args.games_in_flight and not INTERRUPTED:
            game, turns = pending.popleft()
            st = load_state(game, turns)
            if st is None:
                errors += 1
                print("  [{}] SKIPPED (no moves / turns beyond SGF)".format(game[0]))
                continue
            in_flight[st.rel_path] = st
            try:
                engine.send(turn_query(st.rel_path, st.moves, st.turns, args.visits))
            except OSError:
                break  # engine died; the None sentinel below handles resubmission

        if not in_flight:
            if INTERRUPTED:
                break
            continue

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
                resubmit_all()
            except OSError:
                pass
            continue

        try:
            resp = json.loads(line)
        except json.JSONDecodeError:
            continue

        rel_path = resp.get('id') or ''
        if not rel_path:
            continue

        if 'error' in resp:
            errors += 1
            print("  [{}] query error: {}".format(rel_path, str(resp['error'])[:120]))
            in_flight.pop(rel_path, None)
            continue

        turn = resp.get('turnNumber')
        lead = resp.get('rootInfo', {}).get('scoreLead')
        visits = resp.get('rootInfo', {}).get('visits', 0)
        if turn is None or lead is None:
            continue
        restarts = 0

        st = in_flight.get(rel_path)
        if st is None or turn not in st.awaiting:
            continue
        st.awaiting.discard(turn)
        st.scores[turn] = (lead, visits)
        if not st.awaiting:
            del in_flight[st.rel_path]
            finalize(st)

    con.commit()
    con.close()
    engine.stop()

    elapsed = time.time() - session_start
    print("\n=== Phase 4 Complete ===")
    print("Games: {}  Turns analyzed: {}  Puzzles (close_score=1): {}  Errors: {}".format(
        games_done, turns_done, close_total, errors))
    print("Time: {:.1f} hours".format(elapsed / 3600))


if __name__ == '__main__':
    main()
