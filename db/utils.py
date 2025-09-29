from sqlalchemy.ext.asyncio import AsyncSession
from db.crud import get_or_create_user  # замість get_user, create_user


async def get_or_create_user_wrapper(
    session: AsyncSession, telegram_id: int, username=None
):
    return await get_or_create_user(session, telegram_id, username=username)
