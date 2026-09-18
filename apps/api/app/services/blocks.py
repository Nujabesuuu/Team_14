import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models import Block


async def blocked_ids(session: AsyncSession, user_id: uuid.UUID) -> set[uuid.UUID]:
    """Everyone the user blocked or who blocked the user. Symmetric on purpose."""
    rows = (
        await session.execute(
            select(Block.blocker_id, Block.blocked_id).where(
                or_(Block.blocker_id == user_id, Block.blocked_id == user_id)
            )
        )
    ).all()
    out: set[uuid.UUID] = set()
    for blocker, blocked in rows:
        out.add(blocked if blocker == user_id else blocker)
    return out


async def is_blocked(session: AsyncSession, a: uuid.UUID, b: uuid.UUID) -> bool:
    return b in await blocked_ids(session, a)


async def block_user(session: AsyncSession, blocker_id: uuid.UUID, blocked_id: uuid.UUID) -> None:
    if blocker_id == blocked_id:
        raise ApiError(422, "CANNOT_BLOCK_SELF", "You cannot block yourself")
    existing = await session.get(Block, (blocker_id, blocked_id))
    if existing is None:
        session.add(Block(blocker_id=blocker_id, blocked_id=blocked_id))
        await session.commit()
