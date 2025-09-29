import pytest
from unittest.mock import AsyncMock, patch

from db.utils import get_or_create_user_wrapper


@pytest.mark.asyncio
async def test_get_or_create_user_wrapper():
    """Тест що wrapper правильно викликає get_or_create_user"""
    mock_session = AsyncMock()
    
    with patch('db.utils.get_or_create_user', new_callable=AsyncMock) as mock_func:
        mock_func.return_value = "mocked_user"
        
        result = await get_or_create_user_wrapper(
            mock_session, 
            telegram_id=123456789, 
            username="test"
        )
        
        mock_func.assert_called_once_with(
            mock_session, 
            123456789, 
            username="test"
        )
        assert result == "mocked_user"