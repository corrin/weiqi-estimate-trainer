"""One-off: clear the game_analysis table.

Use when the analysis methodology changes (e.g. the 2026-06 switch from
japanese-rules to chinese-rules queries) and existing rows are invalid.
phase4_analyze.py will then re-analyze everything from scratch.

Usage: python reset_analysis.py [--yes]
"""
import sqlite3, argparse

DB = "games.db"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    con = sqlite3.connect(DB)
    n = con.execute("SELECT COUNT(*) FROM game_analysis").fetchone()[0]
    if n == 0:
        print("game_analysis is already empty.")
        con.close()
        return

    if not args.yes:
        answer = input("Delete all {} game_analysis rows? [y/N] ".format(n))
        if answer.strip().lower() != 'y':
            print("Aborted.")
            con.close()
            return

    con.execute("DELETE FROM game_analysis")
    con.commit()
    con.close()
    print("Cleared {} game_analysis rows.".format(n))


if __name__ == '__main__':
    main()
