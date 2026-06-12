from fastapi import APIRouter, HTTPException, Depends, Header, Query
from pydantic import BaseModel
import random

from .database import get_games_db, get_app_db, init_app_db
from .auth import verify_google_token, create_session_token, decode_session_token
from .board import get_position

router = APIRouter()

init_app_db()


class GoogleAuthRequest(BaseModel):
    credential: str


class GuessRequest(BaseModel):
    filepath: str
    guessed_score: float
    turn: int | None = None


def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        payload = decode_session_token(authorization[7:])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/auth/google")
def google_auth(req: GoogleAuthRequest):
    try:
        info = verify_google_token(req.credential)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = info.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email in token")

    name = info.get("name", email)

    con = get_app_db()
    user = con.execute("SELECT id, is_admin FROM users WHERE email = ?", (email,)).fetchone()
    if user:
        user_id = user["id"]
        is_admin = bool(user["is_admin"])
    else:
        cur = con.execute(
            "INSERT INTO users (email, display_name) VALUES (?, ?)",
            (email, name),
        )
        user_id = cur.lastrowid
        is_admin = False
        con.commit()
    con.close()

    token = create_session_token(user_id, email)
    return {"token": token, "user": {"id": user_id, "email": email, "name": name, "is_admin": is_admin}}


@router.get("/position")
def serve_position(
    user=Depends(get_current_user),
    filepath: str | None = Query(None),
    turn: int | None = Query(None),
):
    con = get_games_db()

    if filepath is not None and turn is not None:
        row = con.execute("""
            SELECT ga.filepath, ga.turn, g.komi, g.handicap, g.board_size, g.num_moves
            FROM game_analysis ga
            JOIN games g ON ga.filepath = g.filepath
            WHERE ga.filepath = ? AND ga.turn = ?
        """, (filepath, turn)).fetchone()
    else:
        row = con.execute("""
            SELECT ga.filepath, ga.turn, g.komi, g.handicap, g.board_size, g.num_moves
            FROM game_analysis ga
            JOIN games g ON ga.filepath = g.filepath
            WHERE g.verified = 1 AND ga.close_score = 1
            ORDER BY RANDOM() LIMIT 1
        """).fetchone()

    con.close()

    if not row:
        raise HTTPException(status_code=404, detail="No positions available")

    pos = get_position(row["filepath"], row["turn"], row["komi"])
    if not pos:
        raise HTTPException(status_code=500, detail="Failed to parse position")

    return {
        "filepath": row["filepath"],
        "turn": row["turn"],
        "ref": "{}:{}".format(row["filepath"], row["turn"]),
        "total_moves": row["num_moves"],
        "komi": row["komi"],
        "board_size": row["board_size"],
        "stones": pos["stones"],
        "last_move": pos["last_move"],
        "next_to_play": pos["next_to_play"],
    }


@router.post("/guess")
def submit_guess(req: GuessRequest, user=Depends(get_current_user)):
    con_app = get_app_db()

    if req.turn is not None:
        existing = con_app.execute(
            "SELECT guessed_score, actual_score, deviation FROM guesses WHERE user_id = ? AND filepath = ? AND turn = ?",
            (user["user_id"], req.filepath, req.turn),
        ).fetchone()
    else:
        existing = con_app.execute(
            "SELECT guessed_score, actual_score, deviation FROM guesses WHERE user_id = ? AND filepath = ? AND turn IS NULL",
            (user["user_id"], req.filepath),
        ).fetchone()

    if existing:
        con_app.close()
        dev = round(existing["deviation"], 1)
        if dev <= 3:
            rating = "Excellent!"
        elif dev <= 10:
            rating = "Close"
        elif dev <= 25:
            rating = "Not bad"
        else:
            rating = "Way off"
        return {
            "filepath": req.filepath,
            "guessed_score": existing["guessed_score"],
            "actual_score": existing["actual_score"],
            "deviation": dev,
            "rating": rating,
        }

    con_games = get_games_db()
    game = con_games.execute(
        "SELECT chinese_score FROM games WHERE filepath = ?",
        (req.filepath,),
    ).fetchone()
    con_games.close()

    if not game or game["chinese_score"] is None:
        con_app.close()
        raise HTTPException(status_code=404, detail="Game not found")

    actual_score = game["chinese_score"]
    deviation = abs(req.guessed_score - actual_score)

    con_app.execute(
        "INSERT INTO guesses (user_id, filepath, turn, guessed_score, actual_score, deviation) VALUES (?, ?, ?, ?, ?, ?)",
        (user["user_id"], req.filepath, req.turn, req.guessed_score, actual_score, deviation),
    )
    con_app.commit()
    con_app.close()

    if deviation <= 3:
        rating = "Excellent!"
    elif deviation <= 10:
        rating = "Close"
    elif deviation <= 25:
        rating = "Not bad"
    else:
        rating = "Way off"

    return {
        "filepath": req.filepath,
        "guessed_score": req.guessed_score,
        "actual_score": actual_score,
        "deviation": round(deviation, 1),
        "rating": rating,
    }


@router.get("/me/stats")
def user_stats(user=Depends(get_current_user)):
    con = get_app_db()

    row = con.execute("""
        SELECT
            COUNT(*) as total_guesses,
            COALESCE(AVG(deviation), 0) as avg_deviation,
            COALESCE(MIN(deviation), 0) as best_deviation
        FROM guesses WHERE user_id = ?
    """, (user["user_id"],)).fetchone()

    recent = con.execute("""
        SELECT g.filepath, g.turn, g.guessed_score, g.actual_score, g.deviation, g.created_at
        FROM guesses g
        WHERE g.user_id = ?
        ORDER BY g.created_at DESC LIMIT 50
    """, (user["user_id"],)).fetchall()

    con.close()

    return {
        "total_guesses": row["total_guesses"],
        "avg_deviation": round(row["avg_deviation"], 1),
        "best_deviation": round(row["best_deviation"], 1),
        "recent": [dict(r) for r in recent],
    }


@router.get("/stats")
def public_stats():
    con = get_games_db()
    row = con.execute(
        "SELECT COUNT(*) as count FROM games WHERE chinese_score IS NOT NULL"
    ).fetchone()
    con.close()
    return {"game_count": row["count"]}


@router.get("/leaderboard")
def leaderboard(user=Depends(get_current_user)):
    con = get_app_db()
    admin_row = con.execute("SELECT is_admin FROM users WHERE id = ?", (user["user_id"],)).fetchone()
    if not admin_row or not admin_row["is_admin"]:
        con.close()
        raise HTTPException(status_code=403, detail="Admin only")

    rows = con.execute("""
        SELECT
            u.id,
            u.email,
            u.display_name,
            COUNT(*) as total_guesses,
            ROUND(AVG(g.deviation), 1) as avg_deviation
        FROM guesses g
        JOIN users u ON g.user_id = u.id
        GROUP BY u.id
        HAVING COUNT(*) >= 5
        ORDER BY avg_deviation ASC
        LIMIT 50
    """).fetchall()
    con.close()

    return [dict(r) for r in rows]
