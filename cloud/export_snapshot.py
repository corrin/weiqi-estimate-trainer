"""Create cloud_input.db — a trimmed games.db for a cloud analysis worker.

Contains all eligible games (so the pod can run phase 3 AND phase 4) plus any
game_analysis rows already computed locally (so the pod skips them). Run from
anywhere; paths resolve relative to the repo root.

Usage: python cloud/export_snapshot.py
"""
import sqlite3, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from backend.migrations import apply_games_db

SRC = os.path.join(ROOT, "games.db")
OUT = os.path.join(ROOT, "cloud_input.db")


def main():
    if os.path.exists(OUT):
        os.remove(OUT)
    apply_games_db(OUT)

    src = sqlite3.connect(SRC)
    dst = sqlite3.connect(OUT)

    src_cols = {r[1] for r in src.execute("PRAGMA table_info(games)")}
    dst_cols = [r[1] for r in dst.execute("PRAGMA table_info(games)")]
    cols = [c for c in dst_cols if c in src_cols]  # legacy local columns (e.g. id) are dropped
    col_list = ", ".join(cols)
    rows = src.execute(
        "SELECT {} FROM games WHERE eligible = 1".format(col_list)).fetchall()
    dst.executemany(
        "INSERT INTO games ({}) VALUES ({})".format(col_list, ", ".join("?" * len(cols))),
        rows)

    done = src.execute(
        "SELECT filepath, turn, score_lead, visits, close_score FROM game_analysis").fetchall()
    dst.executemany(
        "INSERT INTO game_analysis (filepath, turn, score_lead, visits, close_score) VALUES (?, ?, ?, ?, ?)",
        done)

    dst.commit()
    n_verified = dst.execute("SELECT COUNT(*) FROM games WHERE verified = 1").fetchone()[0]
    print("Wrote {}".format(OUT))
    print("  games (eligible): {}   already verified: {}   analysis rows carried over: {}".format(
        len(rows), n_verified, len(done)))
    src.close()
    dst.close()


if __name__ == '__main__':
    main()
