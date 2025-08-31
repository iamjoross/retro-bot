from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database
from app.shared.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager"""

    client: Optional[AsyncIOMotorClient] = None
    database: Optional[Database] = None


mongodb = MongoDB()


async def connect_to_mongo():
    """Create async database connection"""
    logger.info(f"Connecting to MongoDB: {settings.MONGODB_URL}")
    mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
    mongodb.database = mongodb.client[settings.DATABASE_NAME]
    logger.info(f"Connected to database: {settings.DATABASE_NAME}")


async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client:
        logger.info("Closing MongoDB connection")
        mongodb.client.close()
        logger.info("MongoDB connection closed")


def get_database() -> Database:
    """Get database instance"""
    if mongodb.database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return mongodb.database
