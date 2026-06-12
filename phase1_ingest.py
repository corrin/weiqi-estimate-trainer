"""
Phase 1 — Ingest: Parse all SGF files, populate the games table in games.db.

Pipeline overview:
  Phase 1  phase1_ingest.py   Parse SGFs → INSERT into games table
  Phase 2  phase2_filter.py   Set eligible=1 on games meeting objective criteria
  Phase 3  phase3_verify.py   KataGo Chinese final query; set verified=1 when
                              abs(chinese_score - score_points) <= 1.5
  Phase 4  phase4_analyze.py  Per-turn KataGo analysis for verified games;
                              set close_score=1 where abs(score_lead - chinese_score) <= 1.5

All phases are idempotent / resumable.
"""
import sqlite3, os, re, time, sys, hashlib
from backend.migrations import apply_games_db

DB = "games.db"
ROOT = "games"

def init_db(con):
    con.execute("PRAGMA journal_mode=WAL")
    apply_games_db(DB)

def parse_result(raw):
    if not raw:
        return ('unknown', None)
    raw = raw.strip()
    if raw in ('?', '0', 'Void', 'void', 'Draw', 'draw', 'Jigo', 'jigo'):
        return ('unknown', None)
    m = re.match(r'^([BW])\+([RrTtFf])', raw)
    if m:
        typemap = {'R': 'resign', 'r': 'resign', 'T': 'time', 't': 'time', 'F': 'forfeit', 'f': 'forfeit'}
        return (typemap.get(m.group(2).upper(), 'other'), None)
    m = re.match(r'^([BW])\+([\d.]+)$', raw)
    if m:
        winner = m.group(1)
        pts = float(m.group(2))
        score = pts if winner == 'B' else -pts
        return ('score', score)
    return ('other', None)

def parse_one(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8', errors='replace')
    sgf_hash = hashlib.sha256(raw).hexdigest()

    def hdr(tag):
        m = re.search(rf'{tag}\[([^\]]*)\]', text)
        return m.group(1) if m else None

    re_val = hdr('RE') or ''
    sz = int(hdr('SZ') or 19)
    km = float(hdr('KM') or 6.5)
    ha = int(hdr('HA') or 0)
    pb = hdr('PB') or ''
    pw = hdr('PW') or ''
    dt = hdr('DT') or ''

    moves = len(re.findall(r';(B|W)\[(?:[a-z]{2}|tt|)\]', text))
    result_type, score_pts = parse_result(re_val)

    rel = os.path.relpath(filepath, ROOT).replace(os.sep, '/')
    tournament = os.path.dirname(rel)

    return {
        'filepath': rel,
        'tournament': tournament,
        'player_b': pb,
        'player_w': pw,
        'result_raw': re_val,
        'result_type': result_type,
        'score_points': score_pts,
        'board_size': sz,
        'komi': km,
        'handicap': ha,
        'num_moves': moves,
        'date': dt,
        'sgf_hash': sgf_hash,
    }

def main():
    con = sqlite3.connect(DB)
    init_db(con)

    sgf_files = []
    for dp, _, fns in os.walk(ROOT):
        for fn in fns:
            if fn.lower().endswith('.sgf'):
                sgf_files.append(os.path.join(dp, fn))

    total = len(sgf_files)
    parsed = 0
    inserted = 0
    skipped = 0
    t0 = time.time()

    for i, fp in enumerate(sgf_files):
        if i > 0 and i % 2000 == 0:
            elapsed = time.time() - t0
            rate = i / elapsed
            eta = (total - i) / rate
            print(f"  {i}/{total} ({i*100//total}%)  {rate:.0f} files/s  ETA {eta:.0f}s  inserted={inserted}")
            sys.stdout.flush()

        parsed += 1
        try:
            info = parse_one(fp)
        except Exception:
            continue

        try:
            con.execute("""
                INSERT INTO games (filepath, tournament, player_b, player_w, result_raw,
                    result_type, score_points, board_size, komi, handicap, num_moves, date, sgf_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (info['filepath'], info['tournament'], info['player_b'], info['player_w'],
                  info['result_raw'], info['result_type'], info['score_points'],
                  info['board_size'], info['komi'], info['handicap'], info['num_moves'],
                  info['date'], info['sgf_hash']))
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1

    con.commit()
    con.close()

    elapsed = time.time() - t0
    print(f"\nDone. {elapsed:.0f}s")
    print(f"  Parsed: {parsed}  Inserted: {inserted}  Skipped (dupes): {skipped}")

    # Summary
    con2 = sqlite3.connect(DB)
    for row in con2.execute("SELECT COUNT(*) FROM games"):
        print(f"  Total in DB: {row[0]}")
    for row in con2.execute("SELECT result_type, COUNT(*) FROM games GROUP BY result_type ORDER BY COUNT(*) DESC"):
        print(f"    {row[0]}: {row[1]}")
    con2.close()

if __name__ == '__main__':
    main()
