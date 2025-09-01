import pytest
from datetime import datetime
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.features.conversations.models import Conversation


class TestConversationAPIWorkflows:
    """Test complete API workflows for conversation management."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_service(self, monkeypatch):
        """Mock the conversation service for API tests."""
        mock = AsyncMock()

        # Mock successful conversation creation
        mock.create_conversation.return_value = Conversation(
            id="conv_api_123",
            title="Main Title 2024-01-01 10:30:00",
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Mock conversation retrieval
        mock.get_conversation.return_value = Conversation(
            id="conv_api_123",
            title="Existing Conversation",
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Mock conversation list
        mock.get_conversations.return_value = []

        # Mock successful deletion
        mock.delete_conversation.return_value = True

        # Mock title update
        mock.update_conversation_title.return_value = Conversation(
            id="conv_api_123",
            title="Updated Title",
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        def mock_service_factory():
            return mock

        monkeypatch.setattr(
            "app.features.conversations.api.ConversationService", mock_service_factory
        )
        return mock

    def test_user_can_start_new_conversation_via_api(self, client, mock_service):
        response = client.post("/api/v1/conversations")

        assert response.status_code == 201, (
            "Conversation creation must return 201 Created"
        )

        data = response.json()
        assert "_id" in data, "Response must include conversation ID"
        assert "title" in data, "Response must include conversation title"
        assert "messages" in data, "Response must include messages array"
        assert "created_at" in data, "Response must include creation timestamp"
        assert "updated_at" in data, "Response must include update timestamp"

        mock_service.create_conversation.assert_called_once()

    def test_user_can_retrieve_conversation_details_via_api(self, client, mock_service):
        response = client.get("/api/v1/conversations/conv_api_123")

        assert response.status_code == 200, "Existing conversation must return 200 OK"

        data = response.json()
        assert data["_id"] == "conv_api_123", "Correct conversation must be returned"
        assert isinstance(data["messages"], list), "Messages must be included"

        mock_service.get_conversation.assert_called_once_with("conv_api_123")

    def test_user_can_list_all_conversations_via_api(self, client, mock_service):
        response = client.get("/api/v1/conversations")

        assert response.status_code == 200, "Conversation list must return 200 OK"
        assert isinstance(response.json(), list), "Response must be a list"

        response = client.get("/api/v1/conversations?skip=10&limit=5")

        assert response.status_code == 200, "Paginated request must succeed"
        mock_service.get_conversations.assert_called()

    def test_user_can_update_conversation_title_via_api(self, client, mock_service):
        response = client.patch(
            "/api/v1/conversations/conv_api_123", json={"title": "My Important Chat"}
        )

        assert response.status_code == 200, "Title update must return 200 OK"

        data = response.json()
        assert "title" in data, "Updated conversation must include title"

        mock_service.update_conversation_title.assert_called_once_with(
            "conv_api_123", "My Important Chat"
        )

    def test_user_can_delete_conversation_via_api(self, client, mock_service):
        response = client.delete("/api/v1/conversations/conv_api_123")

        assert response.status_code == 200, "Successful deletion must return 200 OK"

        data = response.json()
        assert "message" in data, "Deletion response must include confirmation message"

        mock_service.delete_conversation.assert_called_once_with("conv_api_123")


class TestConversationAPIErrorHandling:
    """Test API error scenarios and edge cases."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_service_with_failures(self, monkeypatch):
        mock = AsyncMock()

        # Mock conversation not found
        mock.get_conversation.return_value = None
        mock.update_conversation_title.return_value = None
        mock.delete_conversation.return_value = False

        def mock_service_factory():
            return mock

        monkeypatch.setattr(
            "app.features.conversations.api.ConversationService", mock_service_factory
        )
        return mock

    def test_api_handles_nonexistent_conversation_appropriately(
        self, client, mock_service_with_failures
    ):
        response = client.get("/api/v1/conversations/nonexistent_id")

        assert response.status_code == 404, "Nonexistent conversation must return 404"

        data = response.json()
        assert "detail" in data, "Error response must include details"

    def test_api_validates_conversation_updates(
        self, client, mock_service_with_failures
    ):
        response = client.patch("/api/v1/conversations/conv_123", json={"title": ""})

        assert response.status_code in [400, 422], "Empty title must be rejected"

    def test_api_handles_failed_deletion_gracefully(
        self, client, mock_service_with_failures
    ):
        response = client.delete("/api/v1/conversations/nonexistent_id")

        assert response.status_code == 404, "Failed deletion must return 404"

    def test_api_returns_empty_list_for_no_conversations(self, client):
        with TestClient(app) as test_client:
            response = test_client.get("/api/v1/conversations")

            # Should return 200 with empty list, not error
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list), "Response must be a list even when empty"


class TestConversationAPIBusinessRules:
    """Test API enforcement of business rules."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_conversation_creation_includes_automatic_title_with_timestamp(
        self, client, monkeypatch
    ):
        mock_service = AsyncMock()
        created_conversation = Conversation(
            id="conv_timestamped",
            title="Main Title 2024-01-01 10:30:00",  # Expected format
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_service.create_conversation.return_value = created_conversation

        def mock_service_factory():
            return mock_service

        monkeypatch.setattr(
            "app.features.conversations.api.ConversationService", mock_service_factory
        )

        response = client.post("/api/v1/conversations")

        assert response.status_code == 201
        data = response.json()

        # Verify title format includes timestamp
        title = data["title"]
        assert "Main Title" in title, "Title must include 'Main Title'"
        assert any(char.isdigit() for char in title), "Title must include timestamp"

        # Verify service was called with proper title format
        args, kwargs = mock_service.create_conversation.call_args
        created_title = kwargs.get("title") or (args[0] if args else None)
        assert created_title is not None, "Service must be called with title"
        assert "Main Title" in created_title, "Generated title must follow format"
