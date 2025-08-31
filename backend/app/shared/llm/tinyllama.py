import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TinyLlamaLLM:
    """TinyLlama implementation for chat responses"""

    def __init__(
        self, model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0", **kwargs
    ):
        self.model_name = model_name
        self.max_tokens = kwargs.get("max_tokens", 150)
        self.temperature = kwargs.get("temperature", 0.7)
        self.top_p = kwargs.get("top_p", 0.9)
        logger.info(f"Initializing TinyLlamaLLM with model: {model_name} (CPU only)")
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForCausalLM] = None
        self.generation_config: Optional[GenerationConfig] = None
        self.cache_dir = kwargs.get("cache_dir", "/tmp/huggingface")

    async def load_model(self) -> None:
        """Load the TinyLlama model and tokenizer"""
        try:
            logger.info(f"Loading TinyLlama model: {self.model_name}")
            logger.info(f"Cache directory: {self.cache_dir}")

            # Load tokenizer
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True,
            )
            logger.info("Tokenizer loaded successfully")

            # Set pad token if not present
            if self.tokenizer.pad_token is None:
                logger.info("Setting pad token to eos token")
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Load model (CPU only)
            logger.info("Loading model for CPU...")
            model_kwargs = {
                "cache_dir": self.cache_dir,
                "trust_remote_code": True,
                "torch_dtype": torch.float32,  # Always float32 for CPU
            }

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name, **model_kwargs
            )
            logger.info("Model loaded successfully on CPU")

            # Generation config
            logger.info("Setting up generation configuration...")
            self.generation_config = GenerationConfig(
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

            logger.info("TinyLlama model loaded and configured successfully!")

        except Exception as e:
            logger.error(f"Failed to load TinyLlama model: {str(e)}")
            raise RuntimeError(f"Failed to load model: {str(e)}")

    def is_loaded(self) -> bool:
        """Check if model is loaded and ready"""
        return (
            self.tokenizer is not None
            and self.model is not None
            and self.generation_config is not None
        )

    def format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for TinyLlama instruction format"""
        try:
            model_name = self.model_name.lower()

            # TinyLlama supports instruction format
            if "instruct" in model_name or "chat" in model_name:
                formatted = []
                for msg in messages:
                    role = msg["role"]
                    content = msg["content"]

                    if role == "system":
                        formatted.append(f"System: {content}")
                    elif role == "user":
                        formatted.append(f"User: {content}")
                    elif role == "assistant":
                        formatted.append(f"Assistant: {content}")

                formatted.append("Assistant:")  # Prompt for response
                return "\n".join(formatted)
            else:
                # Fallback format
                formatted = []
                for msg in messages:
                    role = msg["role"]
                    content = msg["content"]

                    if role == "system":
                        formatted.append(f"System: {content}")
                    elif role == "user":
                        formatted.append(f"User: {content}")
                    elif role == "assistant":
                        formatted.append(f"Assistant: {content}")

                formatted.append("Assistant:")
                return "\n".join(formatted)

        except Exception:
            # Fallback formatting
            return messages[-1]["content"] if messages else "Hello"

    def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate response from conversation messages"""
        if not self.is_loaded():
            raise RuntimeError("Model not loaded. Call load_model() first.")

        try:
            logger.info(f"Generating response for {len(messages)} messages")

            # Format messages for the model
            formatted_prompt = self.format_messages(messages)
            logger.info(f"Formatted prompt length: {len(formatted_prompt)} chars")

            # Tokenize
            logger.info("Tokenizing input...")
            inputs = self.tokenizer(
                formatted_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048,
                padding=True,
            )
            logger.info(f"Input tokens shape: {inputs['input_ids'].shape}")

            # Inputs stay on CPU

            # Generate
            logger.info("Starting model generation...")
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    generation_config=self.generation_config,
                )
            logger.info("Model generation completed")

            # Decode response
            logger.info("Decoding generated tokens...")
            raw_response = self.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
            ).strip()
            logger.info(f"Raw response: '{raw_response}'")

            # Clean response
            response = self._clean_response(raw_response)
            logger.info(f"Cleaned response: '{response}'")

            return response or "[ERROR] Failed to generate response"

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "[ERROR] Model generation failed"

    def _clean_response(self, raw_response: str) -> str:
        """Clean up model response - extract just the assistant's part"""
        if not raw_response or not raw_response.strip():
            return ""

        response = raw_response.strip()
        
        # Remove conversation formatting artifacts more aggressively
        # Split by any dialogue marker (case-insensitive) and take the first part
        dialogue_markers = ['USER:', 'User:', 'ASSISTANT:', 'Assistant:', 'HUMAN:', 'Human:']
        
        for marker in dialogue_markers:
            if marker in response:
                parts = response.split(marker)
                first_part = parts[0].strip()
                if first_part:
                    response = first_part
                    break
        
        # Also handle quotes that might contain dialogue
        if response.endswith('"') and '"' in response[:-1]:
            # Find the last quote and remove everything after it
            last_quote_idx = response.rfind('"')
            if last_quote_idx > 0:
                response = response[:last_quote_idx + 1]
        
        # Clean up any remaining artifacts
        lines = [line.strip() for line in response.split("\n") if line.strip()]
        
        if not lines:
            return ""
            
        # Take the first meaningful line/paragraph
        cleaned_lines = []
        for line in lines:
            # Skip lines that look like dialogue markers
            if any(marker.lower() in line.lower() for marker in ['user:', 'assistant:', 'human:']):
                break
            # Skip lines that are just formatting artifacts
            if line.startswith("(") and line.endswith(")"):
                continue
            cleaned_lines.append(line)
        
        # Join lines back together
        result = "\n".join(cleaned_lines).strip()
        
        # Final cleanup - remove any trailing dialogue artifacts
        for marker in dialogue_markers:
            if result.endswith(marker):
                result = result[:-len(marker)].strip()
        
        return result if result else response

    def cleanup(self) -> None:
        """Cleanup model resources"""
        logger.info("Cleaning up TinyLlama model")
        del self.model, self.tokenizer, self.generation_config
