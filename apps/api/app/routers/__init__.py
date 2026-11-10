from fastapi import APIRouter


def register_routers(api: APIRouter) -> None:
    """Attach every feature router to the versioned API router."""
    from app.routers import (
        auth,
        blocks,
        chat,
        discover,
        events,
        feedback,
        games,
        matches,
        me,
        reports,
        reveal,
        swipes,
        ws,
    )

    for module in (auth, me, games, events, feedback, discover, swipes, matches, reveal, chat, blocks, reports, ws):
        api.include_router(module.router)
    api.include_router(reports.moderation_router)
