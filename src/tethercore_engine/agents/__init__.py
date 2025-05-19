# This file makes 'agents' a Python sub-package.
# It's where specific Mindscape Agent implementations will reside.

from .base_agent import BaseAgent # Import the base class

# You might choose to expose specific agent classes here if needed directly
# from .examples.focus_mind.agent import FocusMindAgent
# from .examples.calendar_mind.agent import CalendarMindAgent

__all__ = [
    "BaseAgent",
    # "FocusMindAgent",
    # "CalendarMindAgent",
]
