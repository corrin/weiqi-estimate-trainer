"""
Phase 4 — Analyze: per-turn KataGo score tracking for verified games.

For each verified game, analyze turns in [MIN_TURN .. num_moves - MIN_FROM_END]
with Chinese rules and komi 7.0 — the same setup phase 3 used to compute
chinese_score, so "current score" and "final score" are in the same scoring
system. close_score=1 where abs(score_lead - chinese_score) <= CLOSE_THRESHOLD.

By default every turn is analyzed at PASS2_VISITS (single pass — measured
borderline fraction on this dataset is ~86%, past the break-even where a
cheap screening pass pays off). --pass1-visits N enables two-pass mode:
  pass 1: every pending turn at N visits (screening only — never admits)
  pass 2: turns whose pass-1 score lands within CLOSE_THRESHOLD + MARGIN of
          chinese_score are re-analyzed at PASS2_VISITS; classification uses
          the pass-2 score. Turns clearly outside the band keep their pass-1
          values with close_score=0.

Games are processed closest-final-margin first (highest puzzle yield per
GPU-hour). Queries are pipelined: up to GAMES_IN_FLIGHT games at once, one
query per game per pass (the analysis engine tags responses with id +
turnNumber). Resumable — skips turns already in game_analysis; a game's rows
commit only once the game is fully classified.

--shard I/N splits the verified games deterministically (crc32 of filepath)
across N independent workers; run one shard per GPU/machine.

Usage: python phase4_analyze.py [--max GAMES] [--shard I/N] [--audit PCT]
                                [--pass1-visits V] [--katago EXE] [--model BIN] [--config CFG]
(To wipe game_analysis after a methodology change, run reset_analysis.py.)
"""
import sqlite3, json, time, os, sys, signal, argparse, queue, random, math, zlib
from collections import deque
from backend.migrations import apply_games_db
from backend.sgf import parse_moves
from katago_engine import Engine, add_engine_args, STDERR_LOG

DB = "games.db"
ROOT = "games"

MIN_TURN = 76
MIN_FROM_END = 50
CLOSE_THRESHOLD = 1.5
MARGIN = 2.5          # pass-1 scores within CLOSE_THRESHOLD + MARGIN get a pass-2 recheck
PASS1_VISITS = 0      # 0 = single pass at PASS2_VISITS for every turn
PASS2_VISITS = 1000
GAMES_IN_FLIGHT = 8
MAX_RESTARTS = 5

INTERRUPTED = False


class GameState:
    def __init__(self, game, moves, turns):
        self.game = game              # (filepath, score_points, komi, num_moves, chinese_score)
        self.moves = moves
        self.turns = turns
        self.phase = 1
        self.awaiting = set(turns)
        self.pass1 = {}               # turn -> (score_lead, visits)
        self.pass2 = {}
        self.borderline = []

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
    parser.add_argument('--pass1-visits', type=int, default=PASS1_VISITS,
                        help='Screening-pass visits; 0 = single pass at full visits (default)')
    parser.add_argument('--pass2-visits', type=int, default=PASS2_VISITS)
    parser.add_argument('--audit', type=float, default=0.0,
                        help='Two-pass mode only: re-check this %% of screened-out turns at full visits')
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
    if args.pass1_visits > 0:
        print("Pass 1: {} visits   Pass 2: {} visits (band: |lead - final| <= {})".format(
            args.pass1_visits, args.pass2_visits, CLOSE_THRESHOLD + MARGIN))
    else:
        print("Single pass: {} visits per turn".format(args.pass2_visits))
        if args.audit > 0:
            print("(--audit has no effect in single-pass mode; every turn already gets full visits)")
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
    audits = {}       # rel_path -> {'game': row, 'awaiting': set(turns)}
    turns_done = 0
    games_done = 0
    borderline_total = 0
    close_total = 0
    errors = 0
    restarts = 0
    audited = 0
    audit_flips = 0
    session_start = time.time()

    def finalize(st):
        nonlocal turns_done, games_done, borderline_total, close_total
        chinese = st.chinese_score
        rows = []
        for t in st.turns:
            if t in st.pass2:
                lead, visits = st.pass2[t]
                close = 1 if abs(lead - chinese) <= CLOSE_THRESHOLD else 0
            else:
                lead, visits = st.pass1[t]
                close = 0
            rows.append((st.rel_path, t, lead, visits, close))
        con.executemany(
            "INSERT OR REPLACE INTO game_analysis (filepath, turn, score_lead, visits, close_score) VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        con.commit()

        n_close = sum(1 for r in rows if r[4] == 1)
        turns_done += len(st.turns)
        games_done += 1
        borderline_total += len(st.borderline)
        close_total += n_close

        elapsed = time.time() - session_start
        rate = turns_done / elapsed * 3600 if elapsed > 0 else 0
        remaining = total_turns - turns_done
        eta = remaining / rate if rate > 0 else 0
        extra = "  borderline={}".format(len(st.borderline)) if args.pass1_visits > 0 else ""
        print("  [{}] turns={}  puzzles={}{}  total {}/{}  {:.0f} t/h  ETA {:.1f}h".format(
            st.rel_path, len(st.turns), n_close, extra, turns_done, total_turns, rate, eta))
        sys.stdout.flush()

        if args.audit > 0 and not INTERRUPTED:
            candidates = [t for t in st.turns if t not in st.pass2]
            k = int(math.ceil(len(candidates) * args.audit / 100.0))
            if candidates and k > 0:
                sample = random.sample(candidates, min(k, len(candidates)))
                audits[st.rel_path] = {'game': st.game, 'moves': st.moves, 'awaiting': set(sample)}
                try:
                    engine.send(turn_query('a|' + st.rel_path, st.moves, sample, args.pass2_visits))
                except OSError:
                    pass  # engine death is handled by the None sentinel + resubmit_all

    def resubmit_all():
        for st in in_flight.values():
            qid = ('p1|' if st.phase == 1 else 'p2|') + st.rel_path
            engine.send(turn_query(qid, st.moves, st.awaiting, args.pass1_visits if st.phase == 1 else args.pass2_visits))
        for rel_path, a in audits.items():
            engine.send(turn_query('a|' + rel_path, a['moves'], a['awaiting'], args.pass2_visits))

    while pending or in_flight or audits:
        while pending and len(in_flight) < args.games_in_flight and not INTERRUPTED:
            game, turns = pending.popleft()
            st = load_state(game, turns)
            if st is None:
                errors += 1
                print("  [{}] SKIPPED (no moves / turns beyond SGF)".format(game[0]))
                continue
            if args.pass1_visits <= 0:
                st.phase = 2  # single pass: every turn straight to full visits
            in_flight[st.rel_path] = st
            try:
                if st.phase == 2:
                    engine.send(turn_query('p2|' + st.rel_path, st.moves, st.turns, args.pass2_visits))
                else:
                    engine.send(turn_query('p1|' + st.rel_path, st.moves, st.turns, args.pass1_visits))
            except OSError:
                break  # engine died; the None sentinel below handles resubmission

        if not in_flight and not audits:
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
            print("KataGo died; restarting and resubmitting {} games...".format(len(in_flight) + len(audits)))
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

        qid = resp.get('id') or ''
        if '|' not in qid:
            continue
        kind, rel_path = qid.split('|', 1)

        if 'error' in resp:
            errors += 1
            print("  [{}] query error: {}".format(rel_path, str(resp['error'])[:120]))
            if kind == 'a':
                audits.pop(rel_path, None)
            else:
                in_flight.pop(rel_path, None)
            continue

        turn = resp.get('turnNumber')
        lead = resp.get('rootInfo', {}).get('scoreLead')
        visits = resp.get('rootInfo', {}).get('visits', 0)
        if turn is None or lead is None:
            continue
        restarts = 0

        if kind == 'a':
            a = audits.get(rel_path)
            if a is None or turn not in a['awaiting']:
                continue
            a['awaiting'].discard(turn)
            audited += 1
            chinese = a['game'][4]
            if abs(lead - chinese) <= CLOSE_THRESHOLD:
                audit_flips += 1
                print("  AUDIT: recovered missed puzzle [{} turn {}] — pass 1 screened it out, {}v says lead={:.1f} vs final={}."
                      " (Pool loss only, never a wrong puzzle; widen MARGIN to miss fewer.)".format(
                          rel_path, turn, args.pass2_visits, lead, chinese))
                con.execute(
                    "UPDATE game_analysis SET score_lead = ?, visits = ?, close_score = 1 WHERE filepath = ? AND turn = ?",
                    (lead, visits, rel_path, turn),
                )
                con.commit()
            if not a['awaiting']:
                del audits[rel_path]
            continue

        st = in_flight.get(rel_path)
        if st is None or turn not in st.awaiting:
            continue
        st.awaiting.discard(turn)

        if kind == 'p1' and st.phase == 1:
            st.pass1[turn] = (lead, visits)
            if not st.awaiting:
                chinese = st.chinese_score
                st.borderline = [t for t in st.turns
                                 if abs(st.pass1[t][0] - chinese) <= CLOSE_THRESHOLD + MARGIN]
                if st.borderline:
                    st.phase = 2
                    st.awaiting = set(st.borderline)
                    try:
                        engine.send(turn_query('p2|' + st.rel_path, st.moves, st.borderline, args.pass2_visits))
                    except OSError:
                        pass
                else:
                    del in_flight[st.rel_path]
                    finalize(st)
        elif kind == 'p2' and st.phase == 2:
            st.pass2[turn] = (lead, visits)
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
    if args.pass1_visits > 0:
        print("Borderline (pass-2): {}".format(borderline_total))
    if audited:
        print("Audit: {} screened-out turns rechecked, {} missed puzzles recovered".format(
            audited, audit_flips))
    print("Time: {:.1f} hours".format(elapsed / 3600))


if __name__ == '__main__':
    main()
