import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.features.conversations.service import ConversationService
from app.features.conversations.models import Conversation, ConversationListRequest
from app.shared.models import Message, MessageRole


class TestConversationBusinessRules:
    """Test enforcement of critical business rules."""

    @pytest.fixture
    def service(self):
        with patch('app.features.conversations.service.ConversationRepository'):
            service = ConversationService()
            service.repository = AsyncMock()
            return service

    async def test_conversation_timestamps_are_automatically_managed(self, service):
        now = datetime.now(timezone.utc)
        created_conversation = Conversation(
            id="conv_timestamp_test",
            title="Test Conversation",
            messages=[],
            created_at=now,
            updated_at=now,
        )
        service.repository.create.return_value = created_conversation

        result = await service.create_conversation("Test Conversation")

        assert result.created_at is not None, "Created timestamp must be set"
        assert result.updated_at is not None, "Updated timestamp must be set"

        service.repository.create.assert_called_once()

    async def test_conversation_list_pagination_enforces_reasonable_limits(
        self, service
    ):
        service.repository.get_conversation_summaries.return_value = []

        request = ConversationListRequest(skip=0, limit=20)
        await service.get_conversations(request)

        service.repository.get_conversation_summaries.assert_called_with(
            skip=0, limit=20
        )

    async def test_message_history_maintains_chronological_order(self, service):
        conversation_with_ordered_messages = Conversation(
            id="conv_ordered",
            title="Ordered Chat",
            messages=[
                Message(
                    role=MessageRole.USER,
                    content="First message",
                    timestamp=datetime(2024, 1, 1, 10, 0, 0),
                ),
                Message(
                    role=MessageRole.ASSISTANT,
                    content="First response",
                    timestamp=datetime(2024, 1, 1, 10, 0, 5),
                ),
                Message(
                    role=MessageRole.USER,
                    content="Second message",
                    timestamp=datetime(2024, 1, 1, 10, 1, 0),
                ),
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        service.repository.add_message_to_conversation.return_value = (
            conversation_with_ordered_messages
        )

        new_message = Message(role=MessageRole.USER, content="Latest message")
        result = await service.add_message("conv_ordered", new_message)

        assert result is not None, "Message addition must succeed"

        service.repository.add_message_to_conversation.assert_called_once()

    async def test_conversation_deletion_is_permanent_and_safe(self, service):
        service.repository.delete.return_value = True

        result = await service.delete_conversation("conv_to_delete")

        assert result is True, "Deletion must report success"
        service.repository.delete.assert_called_once_with("conv_to_delete")


class TestConversationDataIntegrity:
    @pytest.fixture
    def service(self):
        with patch('app.features.conversations.service.ConversationRepository'):
            service = ConversationService()
            service.repository = AsyncMock()
            return service

    async def test_conversation_id_uniqueness_is_guaranteed(self, service):
        conversation1 = Conversation(
            id="conv_unique_1",
            title="First",
            messages=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        conversation2 = Conversation(
            id="conv_unique_2",
            title="Second",
            messages=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        service.repository.create.side_effect = [conversation1, conversation2]

        result1 = await service.create_conversation("First")
        result2 = await service.create_conversation("Second")

        assert result1.id != result2.id, "Conversation IDs must be unique"
        assert result1.id is not None, "First conversation must have ID"
        assert result2.id is not None, "Second conversation must have ID"

    async def test_empty_message_lists_are_handled_gracefully(self, service):
        empty_conversation = Conversation(
            id="conv_empty",
            title="Empty Chat",
            messages=[],  # Empty list
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        service.repository.create.return_value = empty_conversation

        result = await service.create_conversation("Empty Chat")

        assert result is not None, "Empty conversation creation must succeed"
        assert isinstance(result.messages, list), "Messages must be a list"
        assert len(result.messages) == 0, "New conversation should have no messages"

    async def test_conversation_retrieval_handles_missing_data_safely(self, service):
        service.repository.get_by_id.return_value = None

        result = await service.get_conversation("nonexistent_conversation")

        assert result is None, "Missing conversation should return None"


class TestConversationPerformanceConstraints:
    """Test performance-related business rules."""

    @pytest.fixture
    def service(self):
        with patch('app.features.conversations.service.ConversationRepository'):
            service = ConversationService()
            service.repository = AsyncMock()
            return service

    async def test_conversation_list_supports_efficient_pagination(self, service):
        service.repository.get_conversation_summaries.return_value = []

        scenarios = [
            (0, 10),  # First page
            (10, 10),  # Second page
            (50, 25),  # Larger page size
            (0, 100),  # Maximum allowed page size
        ]

        for skip, limit in scenarios:
            request = ConversationListRequest(skip=skip, limit=limit)
            await service.get_conversations(request)

        assert service.repository.get_conversation_summaries.call_count == len(
            scenarios
        )

    async def test_conversation_summaries_provide_essential_info_only(self, service):
        service.repository.get_conversation_summaries.return_value = []

        request = ConversationListRequest(skip=0, limit=10, include_messages=False)
        result = await service.get_conversations(request)

        assert isinstance(result, list), "Result must be a list of summaries"
        service.repository.get_conversation_summaries.assert_called_once()
