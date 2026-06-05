"""
FastAPI Application Factory.

Creates and configures the FastAPI application with CORS, routers, and startup events.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.config import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="FlowCompiler — AI Application Compiler",
        description=(
            "Production-grade AI system that converts natural language "
            "software requirements into complete executable application configurations."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url, "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register router
    app.include_router(router, prefix="", tags=["compiler"])

    # Logging
    logging.basicConfig(
        level=logging.DEBUG if settings.app_debug else logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    @app.on_event("startup")
    async def startup():
        logging.getLogger(__name__).info(
            f"FlowCompiler started in {settings.app_env} mode"
        )

    return app


app = create_app()
