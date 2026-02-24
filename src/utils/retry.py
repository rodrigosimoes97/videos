from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

T = TypeVar("T")


def retry(max_attempts: int = 3, base_sleep: float = 0.5, exceptions: tuple[type[Exception], ...] = (Exception,)):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == max_attempts:
                        raise
                    time.sleep(base_sleep * attempt)

        return wrapper

    return decorator
