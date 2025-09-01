import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.features.chat import chat_router
from app.features.conversations import conversations_router
from app.shared.database import connect_to_mongo, close_mongo_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # This ensures logs go to stdout/terminal
    ],
)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Assistant API with DATACOM-7")
    await connect_to_mongo()
    logger.info("MongoDB connection established")
    yield
    # Shutdown
    logger.info("Shutting down Assistant API")
    await close_mongo_connection()
    logger.info("MongoDB connection closed")


app = FastAPI(
    title="DATACOM-7 Assistant API",
    description="AI-powered retro chat assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include feature routers
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
app.include_router(conversations_router, prefix="/api/v1", tags=["conversations"])
