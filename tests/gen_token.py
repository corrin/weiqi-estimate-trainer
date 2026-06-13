import sys
from pathlib import Path

# Import backend as a package so its relative imports (e.g. `from .migrations`) resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.database import get_app_db, init_app_db
from backend.auth import create_session_token

init_app_db()
con = get_app_db()
user = con.execute("SELECT id, email FROM users LIMIT 1").fetchone()
con.close()

if user:
    token = create_session_token(user["id"], user["email"])
    print(f"TEST_TOKEN={token}")
    print(f"USER_EMAIL={user['email']}")
else:
    print("No users found in DB")
