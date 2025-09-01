import pytest
from unittest.mock import Mock, AsyncMock, patch
from bson import ObjectId

from app.shared.database.base import BaseRepository
from app.shared.database.mongodb import get_database


class DomainModel:
    def __init__(self, id: str = None, name: str = "test", value: int = 42):
        self.id = id
        self.name = name
        self.value = value


class RepositoryImpl(BaseRepository[DomainModel]):
    def _to_domain(self, doc: dict) -> DomainModel:
        return DomainModel(
            id=str(doc.get("_id")), name=doc.get("name", ""), value=doc.get("value", 0)
        )

    def _to_document(self, entity: DomainModel) -> dict:
        doc = {"name": entity.name, "value": entity.value}
        if entity.id:
            doc["_id"] = ObjectId(entity.id)
        return doc


class TestBaseRepository:
    @pytest.fixture
    def mock_collection(self):
        return Mock()

    @pytest.fixture
    def repository(self, mock_collection):
        return RepositoryImpl(mock_collection)

    def test_prepare_id_handles_invalid_input(self, repository):
        with pytest.raises(ValueError, match="Invalid ObjectId"):
            repository._prepare_id("invalid-id")

        with pytest.raises(ValueError, match="Invalid ObjectId"):
            repository._prepare_id(123)

    @pytest.mark.asyncio
    async def test_domain_conversion_preserves_data(self, repository):
        # Test the actual business logic: converting between domain and document
        entity = DomainModel(name="business_entity", value=100)
        doc = repository._to_document(entity)

        # Verify domain -> document conversion
        assert doc["name"] == "business_entity"
        assert doc["value"] == 100

        # Verify document -> domain conversion
        test_doc = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "name": "converted",
            "value": 200,
        }
        converted_entity = repository._to_domain(test_doc)
        assert converted_entity.name == "converted"
        assert converted_entity.value == 200
        assert converted_entity.id == "507f1f77bcf86cd799439011"

    @pytest.mark.asyncio
    async def test_create_handles_database_errors(self, repository, mock_collection):
        entity = DomainModel(name="test", value=42)
        mock_collection.insert_one = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        with pytest.raises(Exception, match="Failed to create entity"):
            await repository.create(entity)

    @pytest.mark.asyncio
    async def test_get_by_id_resilience(self, repository, mock_collection):
        # Test with invalid ID (doesn't crash, returns None)
        result = await repository.get_by_id("invalid-id")
        assert result is None

        # Test with database error (gracefully handles exception)
        mock_collection.find_one = AsyncMock(side_effect=Exception("DB error"))
        result = await repository.get_by_id("507f1f77bcf86cd799439011")
        assert result is None


class TestMongoDB:
    @patch("app.shared.database.mongodb.mongodb")
    def test_get_database_not_initialized_error(self, mock_mongodb):
        """Test database access fails gracefully when not initialized - prevents production crashes"""
        mock_mongodb.database = None

        with pytest.raises(RuntimeError, match="Database not initialized"):
            get_database()
