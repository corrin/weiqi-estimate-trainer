import sqlite3
import os

from .migrations import apply_app_db

ROOT = os.path.dirname(os.path.dirname(__file__))
GAMES_DB_PATH = os.path.join(ROOT, "games.db")
APP_DB_PATH = os.path.join(ROOT, "app.db")


def get_games_db():
    con = sqlite3.connect(GAMES_DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def get_app_db():
    con = sqlite3.connect(APP_DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_app_db():
    apply_app_db(APP_DB_PATH)
