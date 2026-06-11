from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
import random

from .database import get_db, init_user_tables
from .auth import verify_google_token, create_session_token, decode_session_token
from .board import get_position

router = APIRouter()

init_user_tables()


class GoogleAuthRequest(BaseModel):
    credential: str


class GuessRequest(BaseModel):
    game_id: int
    guessed_score: float


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

    con = get_db()
    user = con.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if user:
        user_id = user["id"]
    else:
        cur = con.execute(
            "INSERT INTO users (email, display_name) VALUES (?, ?)",
            (email, name),
        )
        user_id = cur.lastrowid
        con.commit()
    con.close()

    token = create_session_token(user_id, email)
    return {"token": token, "user": {"id": user_id, "email": email, "name": name}}


@router.get("/position")
def serve_position(user=Depends(get_current_user)):
    con = get_db()
    row = con.execute("""
        SELECT a.game_id, a.turn_analyzed, g.filepath, g.komi, g.handicap, g.board_size
        FROM analysis a
        JOIN games g ON a.game_id = g.id
        ORDER BY RANDOM() LIMIT 1
    """).fetchone()
    con.close()

    if not row:
        raise HTTPException(status_code=404, detail="No positions available")

    pos = get_position(row["game_id"], row["filepath"], row["turn_analyzed"], row["komi"])
    if not pos:
        raise HTTPException(status_code=500, detail="Failed to parse position")

    return {
        "game_id": row["game_id"],
        "turn": row["turn_analyzed"],
        "total_moves": pos["total_moves"],
        "komi": row["komi"],
        "board_size": row["board_size"],
        "stones": pos["stones"],
        "last_move": pos["last_move"],
        "next_to_play": pos["next_to_play"],
    }


@router.post("/guess")
def submit_guess(req: GuessRequest, user=Depends(get_current_user)):
    con = get_db()

    analysis = con.execute(
        "SELECT score_lead FROM analysis WHERE game_id = ?",
        (req.game_id,),
    ).fetchone()

    if not analysis:
        con.close()
        raise HTTPException(status_code=404, detail="Game not found")

    actual_score = analysis["score_lead"]
    deviation = abs(req.guessed_score - actual_score)

    con.execute(
        "INSERT INTO guesses (user_id, game_id, guessed_score, actual_score, deviation) VALUES (?, ?, ?, ?, ?)",
        (user["user_id"], req.game_id, req.guessed_score, actual_score, deviation),
    )
    con.commit()
    con.close()

    if deviation <= 5:
        rating = "Excellent!"
    elif deviation <= 15:
        rating = "Close"
    elif deviation <= 30:
        rating = "Not bad"
    else:
        rating = "Way off"

    return {
        "game_id": req.game_id,
        "guessed_score": req.guessed_score,
        "actual_score": actual_score,
        "deviation": round(deviation, 1),
        "rating": rating,
    }


@router.get("/me/stats")
def user_stats(user=Depends(get_current_user)):
    con = get_db()

    row = con.execute("""
        SELECT
            COUNT(*) as total_guesses,
            COALESCE(AVG(deviation), 0) as avg_deviation,
            COALESCE(MIN(deviation), 0) as best_deviation
        FROM guesses WHERE user_id = ?
    """, (user["user_id"],)).fetchone()

    recent = con.execute("""
        SELECT g.game_id, g.guessed_score, g.actual_score, g.deviation, g.created_at
        FROM guesses g
        WHERE g.user_id = ?
        ORDER BY g.created_at DESC LIMIT 20
    """, (user["user_id"],)).fetchall()

    con.close()

    return {
        "total_guesses": row["total_guesses"],
        "avg_deviation": round(row["avg_deviation"], 1),
        "best_deviation": round(row["best_deviation"], 1),
        "recent": [dict(r) for r in recent],
    }


@router.get("/leaderboard")
def leaderboard():
    con = get_db()
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
