import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar, cast

logger = logging.getLogger(__name__)
T = TypeVar("T")


def log_execution_time(func: Callable[..., T]) -> Callable[..., T]:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)  # type: ignore
            execution_time = time.time() - start_time
            logger.debug(
                f"Method {func.__name__} execution completed with args: {args}, kwargs: {kwargs}. "
                f"Execution time: {execution_time:.2f}s",
            )
            return cast(T, result)
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Method {func.__name__} execution failed: Error: {str(e)}",
            )
            raise e

    return cast(Callable[..., T], wrapper)
