"""
Speech handling module for the AI Assistant project.
Provides text-to-speech and speech-to-text functionality using pyttsx3 and SpeechRecognition.
"""

import speech_recognition as sr
import pyttsx3
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SpeechRecognizer:
    """Handles speech-to-text operations."""
    
    def __init__(self, language: str = "en-US", timeout: int = 5, phrase_timeout: float = 1.5):
        """
        Initialize speech recognizer.
        
        Args:
            language (str): Language code for recognition
            timeout (int): Maximum time to listen for
            phrase_timeout (float): Timeout for phrase completion
        """
        self.language = language
        self.timeout = timeout
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = phrase_timeout
        self.recognizer.operation_timeout = timeout

    def listen(self) -> Optional[str]:
        """
        Listen for speech input and convert to text.
        
        Returns:
            Optional[str]: Transcribed text or None if failed
        """
        try:
            with sr.Microphone() as source:
                logger.debug("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.debug("Listening for speech...")
                audio = self.recognizer.listen(source, timeout=self.timeout)
                
                logger.debug("Processing speech...")
                text = self.recognizer.recognize_google(
                    audio,
                    language=self.language
                )
                return text.lower()

        except sr.WaitTimeoutError:
            logger.warning("Listening timed out")
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
        except sr.RequestError as e:
            logger.error(f"Could not request results: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in listen(): {str(e)}")
        
        return None

    def detect_wake_word(self, wake_word: str = "hey assistant") -> bool:
        """
        Check for wake word in audio stream.
        
        Args:
            wake_word (str): Wake word to detect
            
        Returns:
            bool: True if wake word detected
        """
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=3)
                text = self.recognizer.recognize_google(audio).lower()
                return wake_word in text
        except:
            return False

    def cleanup(self):
        """Cleanup resources."""
        pass  # Add cleanup if needed

class TextToSpeech:
    """Handles text-to-speech operations."""
    
    def __init__(self, voice_id: Optional[str] = None, rate: int = 150, volume: float = 0.8):
        """
        Initialize text-to-speech engine.
        
        Args:
            voice_id (str, optional): Voice ID to use
            rate (int): Speech rate
            volume (float): Speech volume
        """
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
        
        # Set voice if specified
        if voice_id:
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if voice_id in voice.id:
                    self.engine.setProperty('voice', voice.id)
                    break

    def speak(self, text: str) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text (str): Text to be spoken
            
        Returns:
            bool: True if successful
        """
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"Error in speak(): {str(e)}")
            return False

    def cleanup(self):
        """Cleanup resources."""
        try:
            self.engine.stop()
        except:
            pass 