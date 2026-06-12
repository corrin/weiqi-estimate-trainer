"""
Phase 2 — Filter: Set eligible=1 on games that meet objective criteria.

Criteria (all must hold):
  - board_size = 19
  - result_type = 'score'
  - num_moves >= 126  (MIN_TURN=76 + MIN_FROM_END=50)

This phase is pure SQL — no KataGo needed.  Runs in seconds.
"""
import sqlite3
from backend.migrations import apply_games_db

DB = "games.db"

MIN_TURN = 76
MIN_FROM_END = 50
MIN_MOVES = MIN_TURN + MIN_FROM_END  # 126


def main():
    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    apply_games_db(DB)

    # Reset eligibility
    con.execute("UPDATE games SET eligible = 0")
    con.commit()

    # Mark eligible
    cur = con.execute("""
        UPDATE games SET eligible = 1
        WHERE board_size = 19
          AND result_type = 'score'
          AND num_moves >= ?
    """, (MIN_MOVES,))
    con.commit()
    eligible = cur.rowcount

    # Count reasons for exclusion
    total = con.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    not_19 = con.execute(
        "SELECT COUNT(*) FROM games WHERE board_size != 19"
    ).fetchone()[0]
    not_score = con.execute(
        "SELECT COUNT(*) FROM games WHERE board_size = 19 AND result_type != 'score'"
    ).fetchone()[0]
    too_short = con.execute(
        "SELECT COUNT(*) FROM games WHERE board_size = 19 AND result_type = 'score' AND num_moves < ?",
        (MIN_MOVES,),
    ).fetchone()[0]

    con.close()

    print(f"Phase 2 — Filter complete")
    print(f"  Total games:                {total}")
    print(f"  Eligible:                   {eligible}")
    print(f"  Excluded — not 19x19:       {not_19}")
    print(f"  Excluded — not score-based: {not_score}")
    print(f"  Excluded — too short:       {too_short}")


if __name__ == '__main__':
    main()
