"""
Chat handling module for the AI Assistant project.
Provides OpenAI API integration and conversation management functionality.
"""

import openai
import logging
from typing import List, Dict, Optional
from time import time
from config import load_config

class ChatHandler:
    """
    Handles chat interactions with OpenAI's API and manages conversation history.
    
    Attributes:
        config (dict): Configuration settings
        logger (logging.Logger): Logger instance
        conversation_history (list): List of message dictionaries
        max_history (int): Maximum number of messages to keep in history
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize chat handler with configuration settings.
        
        Args:
            config (dict, optional): Configuration dictionary containing API settings
        """
        self.config = config or load_config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI API
        openai.api_key = self.config.get("OPENAI_API_KEY")
        
        # Initialize conversation history
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = self.config.get("MAX_CONVERSATION_HISTORY", 10)
        
        # Set default model
        self.model = self.config.get("OPENAI_MODEL", "gpt-3.5-turbo")
        
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in configuration")

    def generate_response(self, prompt: str) -> str:
        """
        Generate a response using OpenAI's API.
        
        Args:
            prompt (str): User's input text
            
        Returns:
            str: Generated response text
            
        Raises:
            Exception: If API request fails
        """
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": prompt,
                "timestamp": time()
            })
            
            # Prepare messages for API request
            messages = [
                {"role": "system", "content": self.config.get("SYSTEM_PROMPT", 
                    "You are a helpful AI assistant.")},
                *[{"role": m["role"], "content": m["content"]} 
                  for m in self.conversation_history[-self.max_history:]]
            ]
            
            # Make API request
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=self.config.get("TEMPERATURE", 0.7),
                max_tokens=self.config.get("MAX_TOKENS", 150),
                timeout=self.config.get("API_TIMEOUT", 30)
            )
            
            # Extract and log response
            response_text = response.choices[0].message.content.strip()
            self.logger.debug(f"Generated response: {response_text}")
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text,
                "timestamp": time()
            })
            
            return response_text
            
        except openai.error.Timeout:
            error_msg = "OpenAI API request timed out"
            self.logger.error(error_msg)
            raise TimeoutError(error_msg)
            
        except openai.error.APIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error in generate_response(): {str(e)}"
            self.logger.error(error_msg)
            raise

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get the current conversation history.
        
        Returns:
            List[Dict[str, str]]: List of conversation messages
        """
        return self.conversation_history

    def save_conversation(self, filepath: str) -> bool:
        """
        Save conversation history to a file (placeholder method).
        
        Args:
            filepath (str): Path to save the conversation
            
        Returns:
            bool: True if successful, False otherwise
        """
        # TODO: Implement conversation saving functionality
        # Possible implementations:
        # 1. Save to JSON file
        # 2. Save to database
        # 3. Save to cloud storage
        pass

def main():
    """Example usage of the ChatHandler class."""
    try:
        chat_handler = ChatHandler()
        
        # Example conversation
        prompts = [
            "Hello! How are you?",
            "What's the weather like?",
            "Thank you for your help!"
        ]
        
        for prompt in prompts:
            print(f"\nUser: {prompt}")
            response = chat_handler.generate_response(prompt)
            print(f"Assistant: {response}")
            
        # Example: Get conversation history
        print("\nConversation History:")
        for message in chat_handler.get_conversation_history():
            print(f"{message['role']}: {message['content']}")
            
    except Exception as e:
        print(f"Error in main(): {str(e)}")

if __name__ == "__main__":
    main() 