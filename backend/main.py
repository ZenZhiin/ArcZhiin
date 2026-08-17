# =============================================================================
# ArcZhiin — FastAPI Application Entrypoint
# =============================================================================

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from db.database import db
from api.routes.chat import router as chat_router
from api.routes.health import router as health_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.server.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    Runs setup on startup and cleanup on shutdown.
    """
    # --- Startup ---
    await db.connect()

    print("🚀 ArcZhiin is starting up...")
    print(f"   Server: {settings.server.host}:{settings.server.port}")
    print(f"   Debug:  {settings.server.debug}")
    print(f"   LLM:    {settings.llm.model_default}")
    print(f"   DB:     {settings.database.path}")

    yield

    # --- Shutdown ---
    await db.disconnect()
    print("👋 ArcZhiin is shutting down...")


app = FastAPI(
    title="ArcZhiin",
    description="Full-Stack AI Assistant by ZenZhiin",
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(chat_router, prefix="/ws", tags=["chat"])
