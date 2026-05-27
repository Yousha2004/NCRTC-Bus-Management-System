from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth
from app.api.endpoints import avls, scheduling, ims, cms

app = FastAPI(title="NCRTC Bus Management System API")

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
