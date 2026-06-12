import sqlite3


def apply_games_db(db_path):
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""
        CREATE TABLE IF NOT EXISTS games (
            filepath      TEXT PRIMARY KEY,
            tournament    TEXT,
            player_b      TEXT,
            player_w      TEXT,
            result_raw    TEXT,
            result_type   TEXT,
            score_points  REAL,
            board_size    INTEGER,
            komi          REAL,
            handicap      INTEGER,
            num_moves     INTEGER,
            date          TEXT,
            chinese_score REAL,
            sgf_hash      TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS game_analysis (
            filepath   TEXT NOT NULL REFERENCES games(filepath),
            turn       INTEGER NOT NULL,
            score_lead REAL,
            visits     INTEGER,
            PRIMARY KEY (filepath, turn)
        )
    """)

    try:
        con.execute("ALTER TABLE games ADD COLUMN eligible INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        con.execute("ALTER TABLE games ADD COLUMN verified INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        con.execute("ALTER TABLE game_analysis ADD COLUMN close_score INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        con.execute("ALTER TABLE games ADD COLUMN sgf_hash TEXT")
    except sqlite3.OperationalError:
        pass

    con.commit()
    con.close()


def apply_app_db(db_path):
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            email        TEXT UNIQUE NOT NULL,
            display_name TEXT,
            is_admin     INTEGER DEFAULT 0,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        con.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    s = con.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='guesses'"
    ).fetchone()

    if s and 'game_id' in s[0] and 'filepath' not in s[0]:
        con.execute("ALTER TABLE guesses RENAME TO guesses_old")
        con.execute("""
            CREATE TABLE guesses (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id),
                filepath      TEXT NOT NULL,
                turn          INTEGER,
                guessed_score REAL NOT NULL,
                actual_score  REAL NOT NULL,
                deviation     REAL NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        con.execute("""
            INSERT INTO guesses (id, user_id, filepath, turn, guessed_score, actual_score, deviation, created_at)
            SELECT id, user_id, CAST(game_id AS TEXT), turn, guessed_score, actual_score, deviation, created_at
            FROM guesses_old
        """)
        con.execute("DROP TABLE guesses_old")
    else:
        con.execute("""
            CREATE TABLE IF NOT EXISTS guesses (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id),
                filepath      TEXT NOT NULL,
                turn          INTEGER,
                guessed_score REAL NOT NULL,
                actual_score  REAL NOT NULL,
                deviation     REAL NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    try:
        con.execute("ALTER TABLE guesses ADD COLUMN turn INTEGER")
    except sqlite3.OperationalError:
        pass

    con.execute("CREATE INDEX IF NOT EXISTS idx_guesses_user ON guesses(user_id)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_guesses_deviation ON guesses(deviation)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_guesses_user_game_turn ON guesses(user_id, filepath, turn)")
    con.commit()
    con.close()
