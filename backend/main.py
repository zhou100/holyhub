from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend import deps
from backend.routers import churches, reviews

app = FastAPI(title="HolyHub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(churches.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")


@app.on_event("startup")
def startup():
    deps.db.connect()


@app.get("/api/health")
def health():
    return {"status": "ok"}
