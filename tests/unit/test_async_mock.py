"""
Test file to verify our custom AsyncMock implementation works correctly.
"""
import pytest
import asyncio
from unittest.mock import Mock
import inspect

# Custom AsyncMock implementation for Python 3.7
class AsyncMock(Mock):
    """Mock for async functions. Python 3.7 compatible replacement for unittest.mock.AsyncMock"""
    async def __call__(self, *args, **kwargs):
        result = super(AsyncMock, self).__call__(*args, **kwargs)
        if inspect.iscoroutine(result):
            return await result
        return result

@pytest.mark.asyncio
async def test_async_mock_return_value():
    """Test that AsyncMock return_value works correctly"""
    mock = AsyncMock()
    mock.return_value = 42
    result = await mock()
    assert result == 42

@pytest.mark.asyncio
async def test_async_mock_side_effect():
    """Test that AsyncMock side_effect works correctly"""
    mock = AsyncMock()
    
    # Test with a regular value
    mock.side_effect = [1, 2, 3]
    assert await mock() == 1
    assert await mock() == 2
    assert await mock() == 3
    
    # Test with an async function as side_effect
    async def async_side_effect(*args, **kwargs):
        return "async_result"
    
    mock.side_effect = async_side_effect
    result = await mock()
    assert result == "async_result"
    
    # Test with a regular function as side_effect
    def regular_side_effect(*args, **kwargs):
        return "regular_result"
    
    mock.side_effect = regular_side_effect
    result = await mock()
    assert result == "regular_result"
    
    # Test with an exception
    mock.side_effect = ValueError("test error")
    with pytest.raises(ValueError, match="test error"):
        await mock()

@pytest.mark.asyncio
async def test_async_mock_called_with():
    """Test that AsyncMock records calls correctly"""
    mock = AsyncMock()
    await mock(1, 2, key="value")
    mock.assert_called_once_with(1, 2, key="value") 