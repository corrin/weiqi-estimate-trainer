import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "games.db")


def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_user_tables():
    con = get_db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            display_name TEXT,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        con.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    con.execute("""
        CREATE TABLE IF NOT EXISTS guesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            game_id INTEGER NOT NULL REFERENCES games(id),
            guessed_score REAL NOT NULL,
            actual_score REAL NOT NULL,
            deviation REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_guesses_user ON guesses(user_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_guesses_deviation ON guesses(deviation)")
    try:
        con.execute("ALTER TABLE guesses ADD COLUMN turn INTEGER")
    except sqlite3.OperationalError:
        pass
    con.execute("CREATE INDEX IF NOT EXISTS idx_guesses_user_game_turn ON guesses(user_id, game_id, turn)")
    con.execute("""
        CREATE TABLE IF NOT EXISTS game_positions (
            game_id INTEGER NOT NULL REFERENCES games(id),
            turn INTEGER NOT NULL,
            score_lead REAL,
            visits INTEGER,
            PRIMARY KEY (game_id, turn)
        )
    """)
    con.execute("DROP TABLE IF EXISTS analysis")
    try:
        con.execute("ALTER TABLE games ADD COLUMN chinese_score REAL")
    except sqlite3.OperationalError:
        pass
    con.commit()
    con.close()
