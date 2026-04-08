"""
ScholAR: Research Decision Engine — Main Application

FastAPI server serving both API endpoints and the frontend.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment BEFORE any local imports so that
# services/llm.py can read GROQ_API_KEY at module level.
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from routes.analyze import router as analyze_router
from routes.simulate import router as simulate_router
from routes.decision import router as decision_router

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("scholar")

# Create app
app = FastAPI(
    title="ScholAR — Research Decision Engine",
    description="AI-powered research analysis, critique, simulation, and decision system",
    version="2.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Mount API routes
app.include_router(analyze_router, prefix="/api", tags=["Analysis"])
app.include_router(simulate_router, prefix="/api", tags=["Simulation"])
app.include_router(decision_router, prefix="/api", tags=["Decision"])


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    has_key = bool(os.getenv("GROQ_API_KEY"))
    return {
        "status": "ok" if has_key else "missing_api_key",
        "service": "ScholAR Research Decision Engine",
        "version": "2.0.0",
        "model": os.getenv("GROQ_MODEL", "llama3-70b-8192"),
        "provider": "Groq",
        "api_key_configured": has_key,
    }


@app.get("/")
async def index(request: Request):
    """Serve the main frontend."""
    return templates.TemplateResponse("index.html", {"request": request})


# Startup banner
@app.on_event("startup")
async def startup():
    model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    has_key = bool(os.getenv("GROQ_API_KEY"))
    logger.info("=" * 50)
    logger.info("  ScholAR Research Decision Engine v2.0")
    logger.info(f"  Provider: Groq | Model: {model}")
    logger.info(f"  API Key: {'✅ Configured' if has_key else '❌ MISSING'}")
    logger.info("=" * 50)
    if not has_key:
        logger.error("  GROQ_API_KEY not set! Add it to .env file.")
