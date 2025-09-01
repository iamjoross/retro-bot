import pytest
from bson import ObjectId

from app.shared.models.common import (
    validate_object_id,
    MessageRole,
    BaseDocument,
    Message,
    APIResponse,
    ErrorResponse,
)


class TestValidateObjectId:
    def test_validate_none(self):
        result = validate_object_id(None)
        assert result is None

    def test_validate_valid_object_id(self):
        test_id = ObjectId("507f1f77bcf86cd799439011")
        result = validate_object_id(test_id)
        assert result == test_id

    def test_validate_valid_string(self):
        test_id_str = "507f1f77bcf86cd799439011"
        result = validate_object_id(test_id_str)
        assert isinstance(result, ObjectId)
        assert str(result) == test_id_str

    def test_validate_invalid_string(self):
        with pytest.raises(ValueError, match="Invalid ObjectId"):
            validate_object_id("invalid-id")

    def test_validate_invalid_type(self):
        with pytest.raises(ValueError, match="Invalid ObjectId"):
            validate_object_id(123)


class TestBaseDocument:
    def test_alias_handling(self):
        doc = BaseDocument(_id="507f1f77bcf86cd799439011")
        assert doc.id == "507f1f77bcf86cd799439011"

    def test_timezone_awareness(self):
        doc = BaseDocument()
        assert doc.created_at.tzinfo is not None
        assert doc.updated_at.tzinfo is not None

    def test_update_timestamp(self):
        doc = BaseDocument()
        original_time = doc.updated_at

        # Small delay to ensure timestamp changes
        import time

        time.sleep(0.001)

        doc.update_timestamp()
        assert doc.updated_at > original_time


class TestMessage:
    def test_message_with_metadata(self):
        metadata = {"conversation_id": "123", "user_agent": "test", "ip": "127.0.0.1"}
        msg = Message(
            role=MessageRole.ASSISTANT, content="Hi there!", metadata=metadata
        )
        assert msg.metadata["conversation_id"] == "123"
        assert msg.metadata["ip"] == "127.0.0.1"

    def test_message_timezone_consistency(self):
        msg = Message(role=MessageRole.USER, content="Test")
        assert msg.timestamp.tzinfo is not None


class TestErrorResponse:
    def test_error_response_with_structured_details(self):
        details = {
            "validation_errors": ["Required field missing"],
            "request_id": "req-123",
            "stack_trace": "...",
        }
        error = ErrorResponse(
            message="Validation failed", error_code="VALIDATION_ERROR", details=details
        )
        assert error.success is False
        assert error.error_code == "VALIDATION_ERROR"
        assert "request_id" in error.details
        assert "validation_errors" in error.details

    def test_error_response_inheritance(self):
        error = ErrorResponse(message="Test error")
        assert isinstance(error, APIResponse)
        assert error.success is False  # Should always be False for errors
