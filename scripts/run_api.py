#!/usr/bin/env python3
"""FastAPI application entry point."""

import uvicorn
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("main")


def main():
    logger.info(f"Starting {settings.app_name} on {settings.app_env}")
    uvicorn.run(
        "app.api.v1.app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
