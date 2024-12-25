"""
Configuration management module for the AI Assistant project.
Handles environment variables, default settings, and hardware configurations.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Default configurations
DEFAULT_SETTINGS = {
    # Text-to-Speech settings
    "TTS_VOICE_ID": "en-US-1",  # Default voice ID
    "TTS_RATE": 150,            # Words per minute
    "TTS_VOLUME": 0.8,          # Volume level (0.0 to 1.0)
    
    # Speech-to-Text settings
    "STT_LANGUAGE": "en-US",    # Default language
    "STT_TIMEOUT": 5,           # Recognition timeout in seconds
    "STT_PHRASE_TIMEOUT": 1.5,  # Seconds of silence to mark end of phrase
    
    # OpenAI API settings
    "OPENAI_MODEL": "gpt-3.5-turbo",
    "OPENAI_MAX_TOKENS": 150,
    "OPENAI_TEMPERATURE": 0.7,
    
    # Hardware PIN configurations (BCM mode)
    "LED_PIN": 18,              # Status LED
    "BUTTON_PIN": 23,           # Push button for interaction
    "MOTION_SENSOR_PIN": 24,    # PIR motion sensor
    "SERVO_PIN": 25,            # Servo motor control
}

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables and combine with default settings.
    
    Returns:
        Dict[str, Any]: Combined configuration dictionary with environment variables
        and default settings.
    
    Raises:
        ValueError: If required environment variables are missing.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Initialize config with default settings
    config = DEFAULT_SETTINGS.copy()
    
    # Required environment variables
    required_vars = [
        "OPENAI_API_KEY",
    ]
    
    # Optional environment variables with their corresponding config keys
    optional_vars = {
        "TTS_VOICE_ID": "TTS_VOICE_ID",
        "TTS_RATE": "TTS_RATE",
        "TTS_VOLUME": "TTS_VOLUME",
        "STT_LANGUAGE": "STT_LANGUAGE",
        "OPENAI_MODEL": "OPENAI_MODEL",
        "MQTT_BROKER": "MQTT_BROKER",
        "MQTT_PORT": "MQTT_PORT",
        "MQTT_USERNAME": "MQTT_USERNAME",
        "MQTT_PASSWORD": "MQTT_PASSWORD",
    }
    
    # Check for required environment variables
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value is None:
            missing_vars.append(var)
        else:
            config[var] = value
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
    
    # Load optional environment variables if they exist
    for env_var, config_key in optional_vars.items():
        value = os.getenv(env_var)
        if value is not None:
            # Convert string values to appropriate types
            if config_key in config and isinstance(config[config_key], (int, float)):
                try:
                    if isinstance(config[config_key], int):
                        value = int(value)
                    else:
                        value = float(value)
                except ValueError:
                    continue
            config[config_key] = value
    
    return config

def get_pin_config() -> Dict[str, int]:
    """
    Get hardware PIN configuration.
    
    Returns:
        Dict[str, int]: Dictionary containing PIN assignments for hardware components.
    """
    return {
        "LED_PIN": DEFAULT_SETTINGS["LED_PIN"],
        "BUTTON_PIN": DEFAULT_SETTINGS["BUTTON_PIN"],
        "MOTION_SENSOR_PIN": DEFAULT_SETTINGS["MOTION_SENSOR_PIN"],
        "SERVO_PIN": DEFAULT_SETTINGS["SERVO_PIN"],
    }

# Example usage of how to load configuration
if __name__ == "__main__":
    try:
        config = load_config()
        print("Configuration loaded successfully:")
        for key, value in config.items():
            print(f"{key}: {value}")
    except ValueError as e:
        print(f"Error loading configuration: {e}") 