import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.features.conversations.service import ConversationService
from app.features.conversations.models import Conversation, ConversationListRequest
from app.shared.models import Message, MessageRole


class TestConversationLifecycle:
    @pytest.fixture
    def mock_repository(self):
        repository = AsyncMock()

        # Mock conversation creation - use side_effect to handle dynamic titles
        def create_conversation(conversation):
            return Conversation(
                id="conv_12345",
                title=conversation.title,  # Use the title from the input
                messages=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        
        repository.create.side_effect = create_conversation

        return repository

    @pytest.fixture
    def service(self, mock_repository):
        with patch('app.features.conversations.service.ConversationRepository'):
            service = ConversationService()
            service.repository = mock_repository
            return service

    async def test_user_can_create_new_conversation_session(
        self, service, mock_repository
    ):
        conversation = await service.create_conversation(title="My Chat Session")

        assert conversation.id is not None, "Conversation must have unique ID"
        assert conversation.title == "My Chat Session", (
            "Conversation title must be preserved"
        )
        assert isinstance(conversation.messages, list), (
            "Conversation must support message history"
        )
        assert conversation.created_at is not None, (
            "Conversation must track creation time"
        )

        mock_repository.create.assert_called_once()

    async def test_user_can_retrieve_conversation_history(
        self, service, mock_repository
    ):
        conversation_with_messages = Conversation(
            id="conv_67890",
            title="Chat with History",
            messages=[
                Message(role=MessageRole.USER, content="Hello"),
                Message(role=MessageRole.ASSISTANT, content="Hi there!"),
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_repository.get_by_id.return_value = conversation_with_messages

        result = await service.get_conversation("conv_67890")

        assert result is not None, "Existing conversation must be retrievable"
        assert result.id == "conv_67890", "Correct conversation must be returned"
        assert len(result.messages) == 2, "All messages must be preserved"
        assert result.messages[0].role == MessageRole.USER, (
            "Message order must be preserved"
        )

    async def test_user_can_manage_multiple_conversations(
        self, service, mock_repository
    ):
        mock_repository.get_conversation_summaries.return_value = [
            MagicMock(
                id="conv_1",
                title="Work Discussion",
                message_count=1,
                created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            ),
            MagicMock(
                id="conv_2",
                title="Personal Chat",
                message_count=1,
                created_at=datetime(2024, 1, 2, 14, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        request = ConversationListRequest(skip=0, limit=10, include_messages=False)
        summaries = await service.get_conversations(request)

        assert len(summaries) == 2, "All conversations must be listed"
        assert all(hasattr(s, "id") for s in summaries), (
            "Each conversation must have ID"
        )
        assert all(hasattr(s, "title") for s in summaries), (
            "Each conversation must have title"
        )
        assert all(hasattr(s, "message_count") for s in summaries), (
            "Message count must be available"
        )

    async def test_user_can_delete_unwanted_conversations(
        self, service, mock_repository
    ):
        mock_repository.delete.return_value = True

        success = await service.delete_conversation("conv_to_delete")

        assert success is True, "Conversation deletion must succeed"
        mock_repository.delete.assert_called_once_with("conv_to_delete")


class TestConversationMessaging:
    @pytest.fixture
    def service_with_existing_conversation(self):
        with patch('app.features.conversations.service.ConversationRepository'):
            service = ConversationService()
            service.repository = AsyncMock()

        # Mock existing conversation with messages
        existing_conversation = Conversation(
            id="conv_active",
            title="Active Chat",
            messages=[
                Message(role=MessageRole.USER, content="Hello"),
                Message(role=MessageRole.ASSISTANT, content="Hi! How can I help?"),
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        service.repository.add_message_to_conversation.return_value = (
            existing_conversation
        )
        return service

    async def test_messages_are_added_to_conversation_history(
        self, service_with_existing_conversation
    ):
        service = service_with_existing_conversation
        new_message = Message(role=MessageRole.USER, content="What's the weather?")

        updated_conversation = await service.add_message("conv_active", new_message)

        assert updated_conversation is not None, "Message addition must succeed"
        service.repository.add_message_to_conversation.assert_called_once_with(
            "conv_active", new_message
        )


class TestConversationBoundaries:
    @pytest.fixture
    def service(self):
        with patch('app.features.conversations.service.ConversationRepository'):
            service = ConversationService()
            service.repository = AsyncMock()
            return service

    async def test_handles_nonexistent_conversation_gracefully(self, service):
        service.repository.get_by_id.return_value = None

        result = await service.get_conversation("nonexistent_id")

        assert result is None, "Nonexistent conversation should return None"

    async def test_empty_conversation_list_returns_empty_result(self, service):
        service.repository.get_conversation_summaries.return_value = []

        request = ConversationListRequest(skip=0, limit=10, include_messages=False)
        result = await service.get_conversations(request)

        assert isinstance(result, list), "Result must be a list"
        assert len(result) == 0, "Empty conversation list should return empty list"

    async def test_pagination_respects_business_limits(self, service):
        service.repository.get_conversation_summaries.return_value = []

        request = ConversationListRequest(skip=10, limit=5, include_messages=False)
        await service.get_conversations(request)

        service.repository.get_conversation_summaries.assert_called_once_with(
            skip=10, limit=5
        )
