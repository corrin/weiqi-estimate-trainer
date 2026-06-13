import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .routes import router

app = FastAPI(title="Weiqi Estimate Trainer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def static_cache_headers(request: Request, call_next):
    # index.html is the only un-hashed file and it points at content-hashed
    # assets that every build replaces. Cache the hashed assets forever, but
    # always revalidate the HTML so a fresh build is picked up on the next load —
    # in dev and after every prod deploy. Without this the browser pins a stale
    # index.html referencing asset hashes the new build has already deleted.
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/assets/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif not path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


app.include_router(router, prefix="/api")

static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
assets_dir = os.path.join(static_dir, "assets")

# Register the static routes unconditionally and check files per-request (not the
# directory once at startup), so a backend started before the first `npm run build`
# serves the app as soon as dist appears — no restart required.
app.mount("/assets", StaticFiles(directory=assets_dir, check_dir=False), name="assets")


def _serve_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=503, detail="Frontend not built — run `npm run build`")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = os.path.join(static_dir, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return _serve_index()


@app.get("/")
async def serve_root():
    return _serve_index()
