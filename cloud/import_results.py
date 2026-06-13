"""Merge games.db files from cloud workers back into the local games.db.

For each shard DB:
  - games:        copy chinese_score/verified for games the local DB hasn't
                  verified yet (local values win when both exist)
  - game_analysis: INSERT OR IGNORE (local rows win; idempotent — rerunning
                  the same shard imports 0)

Refuses to run if another process (e.g. a local phase 4 run) holds a write
lock on games.db.

Usage: python cloud/import_results.py shard0.db [shard1.db ...]
"""
import sqlite3, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "games.db")


def main():
    shards = sys.argv[1:]
    if not shards:
        print(__doc__)
        sys.exit(1)

    con = sqlite3.connect(DB, timeout=1)
    try:
        con.execute("BEGIN IMMEDIATE")
        con.rollback()
    except sqlite3.OperationalError:
        print("games.db is locked — stop any running phase 3/4 first.")
        sys.exit(1)

    for shard in shards:
        if not os.path.exists(shard):
            print("{}: not found, skipping".format(shard))
            continue
        con.execute("ATTACH DATABASE ? AS shard", (shard,))

        before = con.total_changes
        con.execute("""
            UPDATE games SET
                chinese_score = (SELECT s.chinese_score FROM shard.games s WHERE s.filepath = games.filepath),
                verified      = (SELECT s.verified      FROM shard.games s WHERE s.filepath = games.filepath)
            WHERE chinese_score IS NULL
              AND filepath IN (SELECT filepath FROM shard.games WHERE chinese_score IS NOT NULL)
        """)
        games_merged = con.total_changes - before

        before = con.total_changes
        con.execute("""
            INSERT OR IGNORE INTO game_analysis (filepath, turn, score_lead, visits, close_score)
            SELECT filepath, turn, score_lead, visits, close_score FROM shard.game_analysis
        """)
        analysis_merged = con.total_changes - before

        con.commit()
        con.execute("DETACH DATABASE shard")
        print("{}: merged {} game verifications, {} analysis rows".format(
            shard, games_merged, analysis_merged))

    total_close = con.execute(
        "SELECT COUNT(*) FROM game_analysis WHERE close_score = 1").fetchone()[0]
    total_verified = con.execute(
        "SELECT COUNT(*) FROM games WHERE verified = 1").fetchone()[0]
    print("Local DB now: {} verified games, {} puzzles (close_score=1)".format(
        total_verified, total_close))
    con.close()


if __name__ == '__main__':
    main()
