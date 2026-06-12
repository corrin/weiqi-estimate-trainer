import sys
sys.path.insert(0, "C:/Users/User/source/weiqi_estimator/backend")
from database import get_app_db, init_app_db
from auth import create_session_token

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
