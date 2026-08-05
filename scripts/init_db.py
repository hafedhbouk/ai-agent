#!/usr/bin/env python3
"""Initialize database and create admin user."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import init_db, get_db_context
from app.models.user import User, UserRole
from app.utils.security import get_password_hash
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("init_db")


def main():
    logger.info("Initializing database...")
    init_db()

    with get_db_context() as db:
        admin = db.query(User).filter(User.email == settings.admin_email).first()
        if not admin:
            admin = User(
                email=settings.admin_email,
                hashed_password=get_password_hash(settings.admin_password),
                full_name="Admin",
                role=UserRole.ADMIN,
            )
            db.add(admin)
            logger.info(f"Admin user created: {settings.admin_email}")
        else:
            logger.info(f"Admin user already exists: {settings.admin_email}")

    logger.info("Database initialization complete")


if __name__ == "__main__":
    main()
