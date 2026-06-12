"""One-shot migration: convert Windows backslash filepaths to POSIX separators in games.db."""
import sqlite3

DB = "games.db"

con = sqlite3.connect(DB)
try:
    count_before = con.execute(
        "SELECT COUNT(*) FROM games WHERE filepath LIKE '%\\%'"
    ).fetchone()[0]
    print(f"Rows with backslashes: {count_before}")

    if count_before == 0:
        print("Nothing to migrate.")
    else:
        con.execute("UPDATE games SET filepath = REPLACE(filepath, '\\', '/')")
        con.commit()
        print(f"Updated {con.total_changes} rows.")

    remaining = con.execute(
        "SELECT COUNT(*) FROM games WHERE filepath LIKE '%\\%'"
    ).fetchone()[0]
    print(f"Rows with backslashes after: {remaining}")
finally:
    con.close()
