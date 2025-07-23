"""
Custom AsyncMock implementation for Python 3.7 compatibility.

This module provides an AsyncMock class that can be used in place of unittest.mock.AsyncMock,
which is only available in Python 3.8 and later.
"""

import inspect
from unittest.mock import Mock


class AsyncMock(Mock):
    """
    Mock for async functions. Python 3.7 compatible replacement for unittest.mock.AsyncMock.
    
    This class extends unittest.mock.Mock to provide a similar interface to unittest.mock.AsyncMock,
    which is only available in Python 3.8+.
    
    Example:
        >>> mock = AsyncMock()
        >>> mock.return_value = 42
        >>> await mock()  # Returns 42
        
        >>> async def coro():
        ...     return "result"
        >>> mock.side_effect = coro
        >>> await mock()  # Returns "result"
    """
    async def __call__(self, *args, **kwargs):
        result = super(AsyncMock, self).__call__(*args, **kwargs)
        if inspect.iscoroutine(result):
            return await result
        return result 