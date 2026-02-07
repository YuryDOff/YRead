"""FastAPI application entry-point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

load_dotenv()

from app.database import init_db  # noqa: E402
from app.routers import books, visual_bible, illustrations, webhook  # noqa: E402

app = FastAPI(
    title="Reading Reinvented",
    description="AI-powered book reading application with generated illustrations",
    version="1.0.0",
)

# CORS – allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated illustrations as static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(os.path.join(static_dir, "illustrations"), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(books.router, prefix="/api", tags=["books"])
app.include_router(visual_bible.router, prefix="/api", tags=["visual-bible"])
app.include_router(illustrations.router, prefix="/api", tags=["illustrations"])
app.include_router(webhook.router, prefix="/api", tags=["webhook"])


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health_check():
    return {"status": "ok", "app": "Reading Reinvented"}
