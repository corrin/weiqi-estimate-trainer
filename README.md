# Weiqi Estimate Trainer

Train your Go positional judgment by guessing score differences from real professional games. Positions are analyzed by KataGo to give you ground-truth accuracy feedback.

**[weiqi-estimate-trainer.ngrok-free.app](https://weiqi-estimate-trainer.ngrok-free.app/)**

## How it works

1. A Go board position appears — taken from a real professional game
2. You guess which side is leading and by how many points
3. Your guess is compared against KataGo's evaluation
4. Get instant accuracy feedback and track your progress over time

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Frontend | React + Vite + Tailwind CSS |
| Go board | [jgoboard](https://github.com/jokkebk/jgoboard) |
| Database | SQLite |
| Auth | Google Identity Services |
| Analysis | [KataGo](https://github.com/lightvector/KataGo) |

## Project structure

```
weiqi_estimator/
├── backend/
│   ├── main.py          FastAPI app entry point
│   ├── routes.py        API endpoints
│   ├── auth.py          Google JWT verification
│   ├── database.py      SQLite helpers
│   └── board.py         SGF parsing & board replay
├── frontend/
│   └── src/
│       ├── pages/       Splash, Play, Progress, Leaderboard
│       └── components/  GoBoard, ScoreSlider, ResultOverlay
├── phase1_parse.py      Parse SGF files → games.db
├── phase2_analyze.py    Run KataGo analysis on eligible games
└── games.db             (not in repo — see data pipeline below)
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/yourname/weiqi-estimate-trainer.git
cd weiqi_estimator

# Backend
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install --force
cd ..
```

### 2. Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create an OAuth 2.0 Client ID (Web application)
3. Add your domain to **Authorized JavaScript origins**
4. Set the Client ID:

```bash
# backend/auth.py — update GOOGLE_CLIENT_ID
# frontend/.env — update VITE_GOOGLE_CLIENT_ID
```

### 3. Game data pipeline

The app needs an SQLite database of analyzed Go games.

```bash
# Step 1: Place SGF files in games/
# Step 2: Parse them
python phase1_parse.py

# Step 3: Analyze with KataGo (requires KataGo binary + model)
python phase2_analyze.py --max 1000
```

The app works with any number of analyzed positions — more is better.

### 4. Run

**Option A: VS Code** (recommended)

- `Tasks: Run Task` → **"Run All"** starts both backend and frontend
- `Run > Start Debugging` → **"Debug Backend"** for Python debugging

**Option B: Terminal**

```bash
# Terminal 1 — backend (port 8001)
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 — frontend dev (port 5173, proxies /api to 8001)
cd frontend && npm run dev
```

**Option C: Production build + ngrok**

```bash
cd frontend && npm run build
uvicorn backend.main:app --host 0.0.0.0 --port 8001
# FastAPI serves dist/ as static files on port 8001
ngrok http 8001
```

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).

## Credits

- KataGo by [lightvector](https://github.com/lightvector/KataGo) — game analysis engine
- jgoboard by [jokkebk](https://github.com/jokkebk/jgoboard) — Go board rendering (CC-BY-NC-4.0)
