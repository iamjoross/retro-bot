from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from bson import ObjectId
from motor.core import AgnosticCollection
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(Generic[T], ABC):
    """Base repository with common CRUD operations"""

    def __init__(self, collection: AgnosticCollection):
        self.collection = collection

    @abstractmethod
    def _to_domain(self, doc: Dict[str, Any]) -> T:
        """Convert database document to domain model"""
        pass

    @abstractmethod
    def _to_document(self, entity: T) -> Dict[str, Any]:
        """Convert domain model to database document"""
        pass

    def _prepare_id(self, entity_id: str) -> ObjectId:
        """Convert string ID to ObjectId"""
        if isinstance(entity_id, ObjectId):
            return entity_id
        if isinstance(entity_id, str) and ObjectId.is_valid(entity_id):
            return ObjectId(entity_id)
        raise ValueError(f"Invalid ObjectId: {entity_id}")

    async def create(self, entity: T) -> T:
        """Create a new entity"""
        try:
            doc = self._to_document(entity)
            doc["created_at"] = datetime.utcnow()
            doc["updated_at"] = datetime.utcnow()

            result = await self.collection.insert_one(doc)
            doc["_id"] = str(result.inserted_id)

            logger.info(f"Created entity with ID: {result.inserted_id}")
            return self._to_domain(doc)

        except Exception as e:
            logger.error(f"Failed to create entity: {str(e)}")
            raise Exception(f"Failed to create entity: {str(e)}")

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID"""
        try:
            object_id = self._prepare_id(entity_id)
            doc = await self.collection.find_one({"_id": object_id})

            if doc:
                doc["_id"] = str(doc["_id"])
                return self._to_domain(doc)
            return None

        except Exception as e:
            logger.error(f"Failed to get entity by ID {entity_id}: {str(e)}")
            return None

    async def update(self, entity_id: str, entity: T) -> Optional[T]:
        """Update an entity"""
        try:
            object_id = self._prepare_id(entity_id)
            doc = self._to_document(entity)
            doc["updated_at"] = datetime.utcnow()

            # Remove _id from update document
            doc.pop("_id", None)

            result = await self.collection.update_one({"_id": object_id}, {"$set": doc})

            if result.modified_count > 0:
                logger.info(f"Updated entity with ID: {entity_id}")
                return await self.get_by_id(entity_id)
            return None

        except Exception as e:
            logger.error(f"Failed to update entity {entity_id}: {str(e)}")
            raise Exception(f"Failed to update entity: {str(e)}")

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity"""
        try:
            object_id = self._prepare_id(entity_id)
            result = await self.collection.delete_one({"_id": object_id})

            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted entity with ID: {entity_id}")
            return success

        except Exception as e:
            logger.error(f"Failed to delete entity {entity_id}: {str(e)}")
            return False

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Find all entities with pagination"""
        try:
            cursor = (
                self.collection.find().skip(skip).limit(limit).sort("created_at", -1)
            )
            docs = await cursor.to_list(length=limit)

            entities = []
            for doc in docs:
                doc["_id"] = str(doc["_id"])
                entities.append(self._to_domain(doc))

            return entities

        except Exception as e:
            logger.error(f"Failed to find all entities: {str(e)}")
            return []
