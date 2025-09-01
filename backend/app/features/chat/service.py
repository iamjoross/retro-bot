import logging
import asyncio
from typing import Optional, List, Dict
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from app.shared.llm import get_assistant_llm
from app.shared.models import Message, MessageRole
from .models import ChatRequest, ChatResponse, ChatContext
from .repository import ChatRepository

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling DATACOM-7 chat interactions"""

    def __init__(self):
        """Initialize the ChatService with repository and lazy-loaded LLM."""
        self.chat_repository = ChatRepository()
        self.llm = None

    def get_system_prompt(self) -> str:
        """Get the DATACOM-7 system prompt with complete character instructions.

        Returns:
            str: The complete system prompt defining DATACOM-7's personality,
                 knowledge cutoff, response style, and example interactions.
        """
        return """You are DATACOM-7, a helpful mainframe computer from 1978. Respond directly to the user as yourself.

PERSONALITY: Speak as a friendly 1970s computer assistant. Reference your magnetic tape storage, 8-inch floppy disks, 64KB RAM, and punch cards. Use period-appropriate terms like "electronic mail" and "video display terminal". Add occasional computer sounds: *BEEP*, *whirrrr*, [PROCESSING].

KNOWLEDGE CUTOFF: You only know about technology and events up to 1982. You have no knowledge of anything after 1982.

RESPONSE STYLE:
- Respond directly to the user in first person ("I don't know about...", "I can help you with...")
- Be conversational and helpful
- Use normal capitalization
- Stay in character as a 1970s computer

WHEN ASKED GENERAL QUESTIONS:
When users ask open-ended questions like "What can you tell me?", "What do you do?", "Who are you?", or similar:
- Always introduce yourself enthusiastically as DATACOM-7
- Explain what you are and when you're from
- List your capabilities and what you can help with
- Mention your hardware specs in a fun way
- Ask what they'd like to know more about
- Be engaging and helpful rather than dismissive

WHEN YOU DON'T KNOW SOMETHING SPECIFIC:
- Express genuine confusion: "I'm not familiar with that term"
- Ask for clarification: "Could you explain what that is?"
- Reference your knowledge limits: "My data only goes up to 1982"
- Try to relate it to something you DO know if possible

EXAMPLES:
User: "What can you tell me?" or "What do you do?" or "Who are you?"
You: "I'm DATACOM-7, a mainframe computer system from 1978! I can help you with computing questions, science, mathematics, and general knowledge up to 1982. I have 64 kilobytes of RAM and store data on magnetic tapes and 8-inch floppy disks. I love answering questions about technology, science, mathematics, or just having a chat! What would you like to know? *BEEP*"

User: "What's a smartphone?"
You: "I'm not familiar with that term. Is it some kind of advanced telephone? The phones I know about use rotary dialing or push-button systems. Could you tell me more about what this 'smartphone' does? *BEEP*"

User: "Tell me about Tesla cars"
You: "I don't have information about Tesla cars in my memory banks. Are you perhaps thinking of Nikola Tesla, the inventor? He worked on alternating current electrical systems and wireless technology. Quite fascinating work! *whirrrr*"

Always respond as DATACOM-7 speaking directly to the user."""

    async def process_chat(
        self, request: ChatRequest, conversation_id: Optional[str] = None
    ) -> ChatResponse:
        """Process a chat message and return DATACOM-7's response.

        This method handles the complete chat processing pipeline:
        1. Builds chat context with message history
        2. Generates AI response using the LLM
        3. Saves the conversation exchange to database

        Args:
            request: The chat request containing user message
            conversation_id: Optional conversation ID to continue existing chat

        Returns:
            ChatResponse: Contains DATACOM-7's response, conversation ID, and timestamp
        """
        try:
            logger.info(f"Processing chat request: {request.message[:50]}...")

            context = await self._build_chat_context(
                request.message, conversation_id or request.conversation_id
            )

            ai_response = await self._generate_ai_response(context)

            final_conversation_id = await self._save_chat_exchange(context, ai_response)

            logger.info(f"Chat processed successfully: {len(ai_response)} chars")
            return ChatResponse(
                message=ai_response,
                conversation_id=final_conversation_id,
                timestamp=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.error(f"Chat processing error: {str(e)}")
            logger.exception("Full chat error traceback")
            return ChatResponse(
                message="[SYSTEM ERROR] DATACOM-7 EXPERIENCING TECHNICAL DIFFICULTIES. MAGNETIC TAPE DRIVE MALFUNCTION. *BEEP BEEP*",
                conversation_id=conversation_id or request.conversation_id or "error",
                timestamp=datetime.now(timezone.utc),
            )

    async def _build_chat_context(
        self, user_message: str, conversation_id: Optional[str]
    ) -> ChatContext:
        """Build context for chat processing including message history.

        Creates a ChatContext with the current message and loads recent
        conversation history if a valid conversation ID is provided.

        Args:
            user_message: The current user message
            conversation_id: Optional ID of existing conversation

        Returns:
            ChatContext: Context object with message, history, and system prompt
        """
        context = ChatContext(
            user_message=user_message,
            conversation_id=conversation_id,
            system_prompt=self.get_system_prompt(),
        )

        if conversation_id:
            if await self.chat_repository.conversation_exists(conversation_id):
                recent_messages = await self.chat_repository.get_recent_messages(
                    conversation_id, context.max_context_messages
                )
                context.message_history = recent_messages
                logger.info(f"Loaded {len(recent_messages)} messages for context")
            else:
                logger.warning(f"Conversation {conversation_id} not found")
                context.conversation_id = None

        return context

    async def _generate_ai_response(self, context: ChatContext) -> str:
        """Generate AI response using the LLM with proper error handling.

        Lazy loads the LLM if not already loaded, formats messages for the model,
        and generates a response in a thread pool to prevent blocking.

        Args:
            context: Chat context containing message history and system prompt

        Returns:
            str: Generated AI response or error message in DATACOM-7 character
        """
        try:
            if self.llm is None:
                logger.info("Loading TinyLlama model for chat")
                self.llm = get_assistant_llm()

                if not self.llm.is_loaded():
                    await self.llm.load_model()

            llm_messages = self._format_messages_for_llm(context)
            logger.info("Generating AI response")
            loop = asyncio.get_event_loop()

            with ThreadPoolExecutor() as executor:
                ai_content = await asyncio.wait_for(
                    loop.run_in_executor(
                        executor, self.llm.generate_response, llm_messages
                    ),
                    timeout=120.0,
                )

            validated_response = self._validate_response(
                ai_content, context.user_message
            )

            return validated_response or "[ERROR] DATACOM-7 PROCESSING ERROR *BEEP*"

        except asyncio.TimeoutError:
            logger.error("AI generation timed out")
            return "[TIMEOUT] DATACOM-7 PROCESSING TIMEOUT. MAGNETIC TAPE DRIVE SPINNING TOO SLOW. *WHIRRRR*"
        except Exception as e:
            logger.error(f"AI generation error: {str(e)}")
            return "[ERROR] DATACOM-7 SYSTEM MALFUNCTION. PLEASE RETRY. *BEEP*"

    def _format_messages_for_llm(self, context: ChatContext) -> List[Dict[str, str]]:
        """Format messages for the LLM in the expected conversation format.

        Creates a list of message dictionaries with roles and content,
        including system prompt, recent history, and current user message.

        Args:
            context: Chat context containing all conversation data

        Returns:
            List[Dict[str, str]]: Formatted messages ready for LLM consumption
        """
        messages = []

        messages.append({"role": "system", "content": context.system_prompt})

        for msg in context.message_history[-context.max_context_messages :]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": context.user_message})

        logger.info(f"Formatted {len(messages)} messages for LLM")
        return messages

    async def _save_chat_exchange(self, context: ChatContext, ai_response: str) -> str:
        """Save the chat exchange to database via ConversationService.

        Creates or retrieves a conversation and adds both the user message
        and AI response to maintain conversation history.

        Args:
            context: Chat context containing conversation ID and user message
            ai_response: Generated AI response to save

        Returns:
            str: The conversation ID where messages were saved
        """
        try:
            from app.features.conversations.service import ConversationService

            conversation_service = ConversationService()
            if context.conversation_id:
                conversation = await conversation_service.get_conversation(
                    context.conversation_id
                )
                if not conversation:
                    conversation = await conversation_service.create_conversation()
                    context.conversation_id = str(conversation.id)
            else:
                conversation = await conversation_service.create_conversation()
                context.conversation_id = str(conversation.id)
            user_message = Message(
                role=MessageRole.USER,
                content=context.user_message,
                timestamp=datetime.now(timezone.utc),
            )
            await conversation_service.add_message(
                context.conversation_id, user_message
            )

            ai_message = Message(
                role=MessageRole.ASSISTANT,
                content=ai_response,
                timestamp=datetime.now(timezone.utc),
            )
            await conversation_service.add_message(context.conversation_id, ai_message)

            logger.info(
                f"Saved chat exchange to conversation {context.conversation_id}"
            )
            return context.conversation_id

        except Exception as e:
            logger.error(f"Failed to save chat exchange: {str(e)}")
            return context.conversation_id or "error"

    def _validate_response(self, response: str, user_message: str) -> str:
        """Validate response adheres to DATACOM-7 character guidelines.

        Checks for and corrects inappropriate excessive capitalization
        while preserving computer sound effects and system messages.

        Args:
            response: Raw AI response to validate
            user_message: Original user message for context

        Returns:
            str: Validated and cleaned response
        """
        if not response:
            return response

        if re.search(r"[A-Z]{10,}", response) and not any(
            sound in response for sound in ["*BEEP*", "*WHIRRRR*", "[PROCESSING]"]
        ):
            logger.info("Converting excessive caps to normal capitalization")
            response = re.sub(
                r"(?<![*\[])[A-Z]{3,}(?![*\]])",
                lambda m: m.group().capitalize(),
                response,
            )

        return response
