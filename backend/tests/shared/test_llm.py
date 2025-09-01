from app.shared.llm import get_assistant_llm
from app.shared.llm.tinyllama import TinyLlamaLLM


class TestTinyLlamaLLM:
    """Test TinyLlama LLM implementation - focus on critical business logic"""

    def test_format_messages_chat_model(self):
        """Test message formatting for chat model"""
        llm = TinyLlamaLLM(model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        result = llm.format_messages(messages)
        expected = (
            "System: You are helpful\nUser: Hello\nAssistant: Hi there!\nAssistant:"
        )
        assert result == expected

    def test_clean_response_removes_dialogue_artifacts(self):
        """Test cleaning response removes USER/ASSISTANT dialogue - critical for DATACOM-7 responses"""
        llm = TinyLlamaLLM()

        # Test USER: dialogue removal
        response_with_user = "Hello! I'm DATACOM-7. *BEEP*\n\nUSER: What can you do?"
        result = llm._clean_response(response_with_user)
        assert "USER:" not in result
        assert "DATACOM-7" in result

        # Test quoted dialogue removal
        response_with_quotes = 'Hello! I am DATACOM-7. *BEEP*"\n\nUSER: "Tell me more"'
        result2 = llm._clean_response(response_with_quotes)
        assert "USER:" not in result2
        assert "DATACOM-7" in result2

    def test_clean_response_handles_edge_cases(self):
        """Test response cleaning handles empty/malformed inputs - prevents crashes"""
        llm = TinyLlamaLLM()

        # Empty responses should not crash
        assert llm._clean_response("") == ""
        assert llm._clean_response("   ") == ""

        # Malformed dialogue should be cleaned
        malformed = "ASSISTANT: Hello USER: What ASSISTANT: More text"
        result = llm._clean_response(malformed)
        assert "Hello" in result
        assert result.count("ASSISTANT:") == 0 or result.count("USER:") == 0


class TestLLMFactory:
    """Test LLM factory functions - focus on initialization patterns"""

    def test_factory_function_exists(self):
        """Test factory function is available - ensures proper module structure"""
        # Just verify the function exists and is importable
        assert callable(get_assistant_llm)
        # Testing actual instantiation would require model downloads
