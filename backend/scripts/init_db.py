"""
Database initialization script

This script:
1. Creates database tables (via Alembic or direct creation)
2. Initializes prebuilt tools
3. Creates a default organization and admin user
"""

import sys
import logging
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal, engine, Base
from app.models import Organization, User, Tool
from app.services.tool_registry import initialize_prebuilt_tools
from app.utils.auth import get_password_hash
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def init_prebuilt_tools(db):
    """Initialize prebuilt global tools"""
    logger.info("Initializing prebuilt tools...")
    tools = initialize_prebuilt_tools(db)
    logger.info(f"Created {len(tools)} prebuilt tools")
    return tools


def create_default_organization(db):
    """Create default organization"""
    org = db.query(Organization).filter(Organization.name == "Default Organization").first()
    
    if not org:
        logger.info("Creating default organization...")
        org = Organization(
            id=uuid.uuid4(),
            name="Default Organization"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        logger.info(f"Created organization: {org.name} (ID: {org.id})")
    else:
        logger.info(f"Organization already exists: {org.name} (ID: {org.id})")
    
    return org


def create_admin_user(db, organization_id, email="admin@agentbuilder.com", password="admin123"):
    """Create default admin user"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        logger.info(f"Creating admin user: {email}")
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=get_password_hash(password),
            full_name="Admin User",
            role="admin",
            is_active=True,
            organization_id=organization_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created admin user: {email}")
        logger.warning(f"⚠️  Default password: {password} - CHANGE THIS IN PRODUCTION!")
    else:
        logger.info(f"Admin user already exists: {email}")
    
    return user


def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("AgentBuilder Database Initialization")
    logger.info("=" * 60)
    
    # Create tables
    create_tables()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create default organization
        org = create_default_organization(db)
        
        # Create admin user
        admin = create_admin_user(db, org.id)
        
        # Initialize prebuilt tools
        tools = init_prebuilt_tools(db)
        
        logger.info("=" * 60)
        logger.info("✅ Database initialization complete!")
        logger.info("=" * 60)
        logger.info(f"Organization ID: {org.id}")
        logger.info(f"Admin Email: {admin.email}")
        logger.info(f"Admin Password: admin123 (CHANGE THIS!)")
        logger.info(f"Prebuilt Tools: {len(tools)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}", exc_info=True)
        db.rollback()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
