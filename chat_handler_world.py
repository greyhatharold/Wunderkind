"""
chat_handler_world.py

Extension of ChatHandler that integrates with WorldModel.
Manages conversation and updates the 'world state' with relevant facts or
structured info. We also handle hardware references in a naive manner.
"""

import openai
import logging
from typing import List, Dict, Optional
from time import time
from config import load_config
from world_model import WorldModel
from api_handler import APIHandler

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)

file_handler = logging.FileHandler('chat_handler_world.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

class ChatHandlerWorld:
    """
    A ChatHandler extension that integrates with a WorldModel.
    """

    def __init__(self, world_model: Optional[WorldModel] = None, config: Optional[dict] = None):
        """
        Initialize ChatHandlerWorld with a WorldModel instance and configuration.
        
        Args:
            world_model (Optional[WorldModel]): Instance of WorldModel to use
            config (Optional[dict]): Configuration dictionary
        """
        self.config = config or load_config()
        self.world_model = world_model or WorldModel()
        self.logger = logging.getLogger(__name__)

        # Initialize API handler
        self.api_handler = APIHandler(self.config)

        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = self.config.get("MAX_CONVERSATION_HISTORY", 10)

        logger.info("ChatHandlerWorld initialized successfully")

    async def generate_response(self, prompt: str) -> str:
        """
        Generate a response from the LLM and update world model with discovered facts.
        
        Args:
            prompt (str): User's input text
            
        Returns:
            str: Generated response text
            
        Raises:
            Exception: If API request fails
        """
        try:
            logger.info(f"User prompt: {prompt}")

            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": prompt,
                "timestamp": str(time())
            })

            # Build prompt with system message and world model summary
            system_prompt = self.config.get("SYSTEM_PROMPT", "You are a helpful AI assistant.")
            world_summary = self.world_model.get_summary()
            full_system_prompt = (
                f"{system_prompt}\n\n"
                f"Here is a summary of known facts and events so far:\n{world_summary}\n\n"
                "Use this information to provide coherent answers while respecting user context."
            )

            # Prepare messages for the API request
            messages = [
                {"role": "system", "content": full_system_prompt},
            ]
            # Include recent conversation history
            recent_history = self.conversation_history[-self.max_history:]
            for msg in recent_history:
                messages.append({"role": msg["role"], "content": msg["content"]})

            logger.debug(f"Full messages for LLM: {messages}")

            # Generate response using API handler
            response_text = await self.api_handler.generate_response(
                messages,
                system_prompt=full_system_prompt
            )

            logger.info(f"Assistant response: {response_text}")

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text,
                "timestamp": str(time())
            })

            # Update world model with any discovered facts
            self._update_world_model_from_response(response_text)

            return response_text

        except Exception as e:
            error_msg = f"Error in generate_response: {str(e)}"
            logger.error(error_msg)
            raise

    def _update_world_model_from_response(self, response_text: str) -> None:
        """
        Parse the response text for facts and update the world model accordingly.
        
        Args:
            response_text (str): The assistant's response text
        """
        try:
            # Example fact extraction (naive approach)
            if "I learned that" in response_text:
                new_fact = response_text.split("I learned that")[-1].strip(". ")
                self.world_model.add_fact(new_fact)
                logger.debug(f"Added new fact to world model: {new_fact}")

            # Example preference extraction
            if "you prefer" in response_text.lower():
                preference_text = response_text.lower().split("you prefer")[1].strip(". ")
                self.world_model.update_user_preference("user_preference", preference_text)
                logger.debug(f"Updated user preference: {preference_text}")

            # Example hardware event detection
            hardware_keywords = ["button", "motion", "sensor", "led"]
            for keyword in hardware_keywords:
                if keyword in response_text.lower():
                    self.world_model.update_hardware_event(
                        f"Hardware interaction mentioned: {keyword}"
                    )
                    logger.debug(f"Recorded hardware event: {keyword}")

        except Exception as e:
            logger.error(f"Error updating world model: {str(e)}")

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get the current conversation history.
        
        Returns:
            List[Dict[str, str]]: List of conversation messages
        """
        return self.conversation_history

    def update_world_model(self, key: str, value: str) -> None:
        """
        Manually update the world model with a key-value pair.
        
        Args:
            key (str): State key to update
            value (str): New value for the key
        """
        self.world_model.set_state(key, value)
        logger.debug(f"World model updated with {key}: {value}")

    def get_world_summary(self) -> str:
        """
        Retrieve the current summary of the world model.
        
        Returns:
            str: Summary of the world state
        """
        return self.world_model.get_summary()

    def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up ChatHandlerWorld resources")
        self.api_handler.cleanup() 