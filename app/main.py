"""
FastAPI application entry point.

This module creates the application instance and registers API routers for the
Production RAG System for IT and Security Triage.
"""

from fastapi import FastAPI

from app.api.routes_triage import router as triage_router

APP_TITLE = "Production RAG System for IT and Security Triage"
APP_VERSION = "0.1.0"


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description=(
            "A production-oriented RAG system for triaging IT support tickets "
            "and security alerts using internal knowledge base documents."
        ),
    )

    app.include_router(triage_router)

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """
        Return application health status.

        Returns:
            Health status response.
        """
        return {
            "status": "ok",
            "service": APP_TITLE,
            "version": APP_VERSION,
        }

    return app


app = create_app()
