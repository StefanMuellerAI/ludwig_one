"""
Activity wrapper to run async activities with asyncio
"""
import asyncio
import functools
from typing import Callable, Any


def async_activity(func: Callable) -> Callable:
    """
    Decorator to wrap async activities for Temporal.
    Creates a new event loop for each invocation to avoid threading issues.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Create new event loop for this activity execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            loop.close()

    return wrapper
