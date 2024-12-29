"""
API handler module for the AI Assistant project.
Manages all external API calls, particularly to OpenAI's GPT models.
Provides a clean interface for making API requests while handling errors,
rate limiting, and response processing.
"""

import logging
import time
import openai
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logger = logging.getLogger(__name__)

class APIHandler:
    """
    Handles all external API interactions, particularly with OpenAI's GPT models.
    Implements retry logic, rate limiting, and error handling.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the API handler with configuration settings.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary containing API settings
        """
        self.config = config
        self.api_key = config.get("OPENAI_API_KEY")
        self.model = config.get("OPENAI_MODEL", "gpt-4")
        self.max_tokens = config.get("OPENAI_MAX_TOKENS", 150)
        self.temperature = config.get("OPENAI_TEMPERATURE", 0.7)
        
        # Initialize OpenAI client
        openai.api_key = self.api_key
        
        # Rate limiting settings
        self.last_request_time = 0
        self.min_request_interval = config.get("MIN_REQUEST_INTERVAL", 1.0)  # seconds
        
        logger.info(f"APIHandler initialized with model: {self.model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a response using the configured GPT model.
        
        Args:
            messages (List[Dict[str, str]]): List of message dictionaries
            system_prompt (Optional[str]): Optional system prompt to prepend
            
        Returns:
            str: Generated response text
            
        Raises:
            Exception: If API request fails after retries
        """
        try:
            # Rate limiting
            self._handle_rate_limit()
            
            # Prepare messages
            formatted_messages = []
            if system_prompt:
                formatted_messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            formatted_messages.extend(messages)
            
            logger.debug(f"Making API request with {len(formatted_messages)} messages")
            
            # Make API request
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=formatted_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extract and log response
            response_text = response.choices[0].message.content.strip()
            logger.info(f"Generated response of length {len(response_text)}")
            
            return response_text
            
        except openai.error.RateLimitError:
            logger.warning("Rate limit exceeded, retrying after exponential backoff")
            raise
            
        except openai.error.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error in generate_response: {str(e)}")
            raise

    def _handle_rate_limit(self) -> None:
        """
        Implement basic rate limiting to prevent API abuse.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze the sentiment of given text using the GPT model.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict[str, float]: Dictionary containing sentiment scores
        """
        prompt = f"""
        Please analyze the sentiment of the following text and respond with only a JSON object containing these scores:
        - positive: (0-1)
        - negative: (0-1)
        - neutral: (0-1)

        Text: "{text}"
        """
        
        try:
            response = await self.generate_response([
                {"role": "user", "content": prompt}
            ])
            
            # TODO: Parse JSON response and return sentiment scores
            # This is a placeholder implementation
            return {
                "positive": 0.5,
                "negative": 0.2,
                "neutral": 0.3
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            raise

    async def summarize_context(self, context: str, max_length: int = 100) -> str:
        """
        Generate a concise summary of the given context.
        
        Args:
            context (str): Text to summarize
            max_length (int): Maximum length of summary in tokens
            
        Returns:
            str: Summarized text
        """
        prompt = f"""
        Please provide a concise summary of the following context in no more than {max_length} tokens:

        {context}
        """
        
        try:
            return await self.generate_response([
                {"role": "user", "content": prompt}
            ])
            
        except Exception as e:
            logger.error(f"Error in context summarization: {str(e)}")
            raise

    def cleanup(self) -> None:
        """
        Cleanup any resources used by the API handler.
        """
        logger.info("APIHandler cleanup completed") 