"""
world_model.py

Maintains a high-level "world state" or "knowledge store" that can be updated
based on user interactions and hardware events. Provides methods for
summarizing or structuring the stored data so it can be passed to an LLM.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class WorldModel:
    """
    A class to maintain and update a "world state" that represents
    facts, user preferences, events, or other data gleaned from
    conversation or hardware inputs.
    """

    def __init__(self):
        """
        Initialize the internal world state.
        """
        self.state: Dict[str, Any] = {}
        self.facts: List[str] = []  # Could store discrete facts or statements

        # Example specialized fields:
        self.user_preferences: Dict[str, Any] = {}
        self.hardware_events: List[str] = []
        logger.info("WorldModel initialized.")

    def add_fact(self, fact: str) -> None:
        """
        Add a new fact or piece of information to the world model.
        """
        self.facts.append(fact)
        logger.debug(f"Added fact: {fact}")

    def update_hardware_event(self, event_description: str) -> None:
        """
        Log hardware-related events, such as motion detection, button press, etc.
        """
        self.hardware_events.append(event_description)
        logger.debug(f"Hardware event recorded: {event_description}")

    def set_state(self, key: str, value: Any) -> None:
        """
        Set (or update) a key-value pair in the internal state dictionary.
        """
        self.state[key] = value
        logger.debug(f"Set internal state [{key}]: {value}")

    def get_state(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the internal state dictionary by key.
        """
        return self.state.get(key)

    def get_summary(self) -> str:
        """
        Produce a simple textual summary of the internal world model.
        In a more advanced system, this could call an LLM to generate
        a short, compressed representation.
        """
        # For now, we'll just create a naive textual summary.
        lines = []
        lines.append("Facts: " + "; ".join(self.facts) if self.facts else "No known facts yet.")
        lines.append("Hardware Events: " + "; ".join(self.hardware_events) if self.hardware_events else "No hardware events recorded.")
        lines.append(f"State keys: {list(self.state.keys())}" if self.state else "No internal state set yet.")
        lines.append(f"User Preferences: {self.user_preferences}" if self.user_preferences else "No user preferences stored.")
        summary_text = "\n".join(lines)
        logger.debug(f"World model summary: {summary_text}")
        return summary_text

    def update_user_preference(self, preference_name: str, preference_value: Any) -> None:
        """
        Store or update a user preference in the world model.
        """
        self.user_preferences[preference_name] = preference_value
        logger.debug(f"Updated user preference [{preference_name}]: {preference_value}")

    def clear(self) -> None:
        """
        Clear the entire world model.
        """
        self.state.clear()
        self.facts.clear()
        self.hardware_events.clear()
        self.user_preferences.clear()
        logger.info("WorldModel has been cleared.") 