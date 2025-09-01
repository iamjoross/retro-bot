import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.features.chat.service import ChatService
from app.features.chat.models import ChatRequest, ChatContext


class TestDatacom7CharacterCore:
    @pytest.fixture
    def chat_service(self):
        with patch("app.features.chat.service.ChatRepository"):
            service = ChatService()
            service.chat_repository = AsyncMock()
            return service

    def test_system_prompt_defines_datacom7_identity(self, chat_service):
        system_prompt = chat_service.get_system_prompt()

        assert "DATACOM-7" in system_prompt
        assert "1978" in system_prompt
        assert "mainframe computer" in system_prompt
        assert "1982" in system_prompt

        assert "*BEEP*" in system_prompt
        assert "*whirrrr*" in system_prompt
        assert "magnetic tape" in system_prompt
        assert "64KB RAM" in system_prompt

    def test_response_validation_handles_excessive_caps(self, chat_service):
        test_response = "THIS IS ALL CAPS TEXT WITHOUT SOUNDS"
        validated = chat_service._validate_response(test_response, "test user message")

        assert isinstance(validated, str)
        assert len(validated) > 0


class TestConversationContextCore:
    @pytest.fixture
    def mock_service(self):
        with patch("app.features.chat.service.ChatRepository"):
            service = ChatService()
            service.chat_repository = AsyncMock()
            service.chat_repository.conversation_exists.return_value = True
            service.chat_repository.get_recent_messages.return_value = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there *BEEP*"},
            ]
            return service

    async def test_context_building_includes_message_history(self, mock_service):
        context = await mock_service._build_chat_context(
            "Follow up message", "conv_123"
        )

        assert context.user_message == "Follow up message"
        assert context.conversation_id == "conv_123"
        assert len(context.message_history) == 2
        assert context.message_history[0]["role"] == "user"
        assert context.message_history[1]["role"] == "assistant"

    def test_message_formatting_for_llm(self, mock_service):
        context = ChatContext(
            user_message="Current message",
            system_prompt="System prompt",
            message_history=[
                {"role": "user", "content": "Previous message"},
                {"role": "assistant", "content": "Previous response"},
            ],
        )

        formatted = mock_service._format_messages_for_llm(context)

        assert len(formatted) == 4
        assert formatted[0]["role"] == "system"
        assert formatted[0]["content"] == "System prompt"
        assert formatted[-1]["role"] == "user"
        assert formatted[-1]["content"] == "Current message"


class TestChatProcessingCore:
    @pytest.fixture
    def processing_service(self):
        with patch("app.features.chat.service.ChatRepository"):
            service = ChatService()
            service.chat_repository = AsyncMock()
            service.llm = MagicMock()
            service.llm.is_loaded.return_value = True
            service.llm.generate_response.return_value = "DATACOM-7 response *BEEP*"
            return service

    async def test_process_chat_returns_valid_response(self, processing_service):
        with patch(
            "app.features.conversations.service.ConversationService"
        ) as mock_conv:
            mock_conv_instance = mock_conv.return_value
            mock_conversation = MagicMock()
            mock_conversation.id = "test_conv"
            mock_conv_instance.create_conversation.return_value = mock_conversation
            mock_conv_instance.add_message = AsyncMock()

            request = ChatRequest(message="Hello DATACOM-7")
            response = await processing_service.process_chat(request)

            assert hasattr(response, "message")
            assert hasattr(response, "conversation_id")
            assert hasattr(response, "timestamp")
            assert len(response.message) > 0

    async def test_error_handling_returns_character_appropriate_response(
        self, processing_service
    ):
        processing_service.llm.generate_response.side_effect = Exception("Test error")

        request = ChatRequest(message="This will cause an error")
        response = await processing_service.process_chat(request)

        assert "DATACOM-7" in response.message
        assert "ERROR" in response.message or "MALFUNCTION" in response.message
        assert "*BEEP*" in response.message or "*WHIRRRR*" in response.message


class TestInputValidationCore:
    def test_chat_request_model_validation(self):
        from pydantic import ValidationError

        valid_request = ChatRequest(message="Valid message")
        assert valid_request.message == "Valid message"

        with pytest.raises(ValidationError):
            ChatRequest(message="")

        with pytest.raises(ValidationError):
            ChatRequest(message="x" * 2001)

    def test_context_size_management(self):
        context = ChatContext(
            user_message="Current",
            system_prompt="System",
            message_history=[
                {"role": "user", "content": f"Msg {i}"} for i in range(10)
            ],
            max_context_messages=3,
        )

        assert context.max_context_messages == 3
        assert len(context.message_history) == 10

        with patch("app.features.chat.service.ChatRepository"):
            service = ChatService()
            formatted = service._format_messages_for_llm(context)
            assert len(formatted) <= 6


class TestServiceIntegrationCore:
    @pytest.fixture
    def integration_service(self):
        with patch("app.features.chat.service.ChatRepository"):
            service = ChatService()
            service.chat_repository = AsyncMock()
            return service

    async def test_conversation_service_error_handling(self, integration_service):
        with patch(
            "app.features.conversations.service.ConversationService",
            side_effect=Exception("DB Error"),
        ):
            context = ChatContext(
                user_message="Test message",
                system_prompt="System prompt",
                conversation_id="test_conv",
            )

            result = await integration_service._save_chat_exchange(context, "Response")
            assert isinstance(result, str)
            assert result in ["test_conv", "error"]

    def test_llm_lazy_loading(self, integration_service):
        assert integration_service.llm is None

        mock_llm = MagicMock()
        mock_llm.is_loaded.return_value = True

        with patch(
            "app.features.chat.service.get_assistant_llm", return_value=mock_llm
        ):
            service_llm = integration_service.llm
            assert service_llm is None


class TestPerformanceConstraints:
    def test_context_message_limit_prevents_unbounded_growth(self):
        many_messages = [
            {"role": "user", "content": f"Message {i}"} for i in range(100)
        ]

        context = ChatContext(
            user_message="Current",
            system_prompt="System",
            message_history=many_messages,
            max_context_messages=5,
        )

        assert context.max_context_messages == 5

        with patch("app.features.chat.service.ChatRepository"):
            service = ChatService()
            formatted = service._format_messages_for_llm(context)

            assert len(formatted) <= 7
