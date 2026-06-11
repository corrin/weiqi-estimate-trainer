import os
import time
import jwt
from google.oauth2 import id_token
from google.auth.transport import requests

GOOGLE_CLIENT_ID = os.environ.get(
    "GOOGLE_CLIENT_ID",
    "1094479426720-l6aq1va60p2fl8ajb6b1c9ii1bjeca58.apps.googleusercontent.com",
)
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me-in-production")
JWT_ALGORITHM = "HS256"


def verify_google_token(credential: str) -> dict:
    info = id_token.verify_oauth2_token(credential, requests.Request(), GOOGLE_CLIENT_ID)
    return info


def create_session_token(user_id: int, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": int(time.time()) + 86400 * 30,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
