import os
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth
from app.api.endpoints import avls, scheduling, ims, cms

app = FastAPI(title="NCRTC Bus Management System API")


@app.on_event("startup")
def _maybe_start_simulator():
    """When RUN_SIMULATOR is set, animate the live map from inside the API
    process (a daemon thread) so no separate always-on worker is needed in the
    cloud. Locally you can still run scripts/tick.py instead."""
    if os.getenv("RUN_SIMULATOR", "").lower() in ("1", "true", "yes"):
        from scripts.tick import simulate
        threading.Thread(target=simulate, daemon=True).start()
        print("Live-map simulator started (RUN_SIMULATOR enabled).")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(avls.router, prefix="/avls", tags=["avls"])
app.include_router(scheduling.router, prefix="/scheduling", tags=["scheduling"])
app.include_router(ims.router, prefix="/ims", tags=["ims"])
app.include_router(cms.router, prefix="/cms", tags=["cms"])

@app.get("/")
def read_root():
    return {"message": "Welcome to NCRTC Bus Management System API"}
