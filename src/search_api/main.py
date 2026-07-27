import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import SessionLocal, init_db
from .schemas import SearchRequest, SearchResponse
from .search import CursorError, search as run_search

app = FastAPI(title="semantic-search-api (reference implementation)")

# Same reasoning as search_api.seed: __file__ is inside site-packages once
# installed, so the console's location is env-configurable, defaulting to
# the working directory (the container's WORKDIR is the repo root).
_CONSOLE_DIR = Path(os.environ.get("CONSOLE_DIR", "console")).resolve()


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/search", response_model=SearchResponse)
def post_search(request: SearchRequest) -> SearchResponse:
    session = SessionLocal()
    try:
        return run_search(session, request)
    except CursorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        session.close()


if _CONSOLE_DIR.exists():
    app.mount("/console", StaticFiles(directory=str(_CONSOLE_DIR), html=True), name="console")

    @app.get("/")
    def root():
        return FileResponse(str(_CONSOLE_DIR / "index.html"))
