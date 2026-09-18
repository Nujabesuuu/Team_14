import asyncio
from datetime import date

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models import Profile, User
from app.services.bot import GUIDE_EMAIL, pick_reply
from tests.helpers import onboard, seed_games


async def _seed_guide() -> None:
    async with SessionLocal() as s:
        guide = User(
            email=GUIDE_EMAIL,
            password_hash=hash_password("x"),
            display_name="Guide",
            birth_date=date(2000, 1, 1),
            is_bot=True,
        )
        guide.profile = Profile(modes=["duo"], role="support", playstyle="casual", comms="text")
        s.add(guide)
        await s.commit()


def test_pick_reply_matches_topics():
    assert "Reveal" in pick_reply("can I see your photo?") or "reveal" in pick_reply("can I see your photo?")
    assert pick_reply("hello there")  # never empty
    assert pick_reply("something completely unrelated")


async def test_onboarding_creates_guide_match_with_openers(client, make_user):
    await _seed_guide()
    games = await seed_games()
    _, h = await make_user()
    assert (await client.get("/matches", headers=h)).json() == []

    await onboard(client, h, games=[games["valorant"]])
    matches = (await client.get("/matches", headers=h)).json()
    assert len(matches) == 1 and matches[0]["other"]["display_name"] == "Guide"

    history = (await client.get(f"/conversations/{matches[0]['conversation_id']}/messages", headers=h)).json()
    assert len(history) == 2 and all(m["sender_id"] == matches[0]["other"]["id"] for m in history)

    # Re-saving the profile must not duplicate the match or the openers.
    await onboard(client, h, games=[games["valorant"]], bio="edited")
    assert len((await client.get("/matches", headers=h)).json()) == 1


async def test_guide_replies_and_consents(client, make_user):
    await _seed_guide()
    games = await seed_games()
    _, h = await make_user()
    await onboard(client, h, games=[games["valorant"]])
    match = (await client.get("/matches", headers=h)).json()[0]
    conv = match["conversation_id"]

    r = await client.post(f"/conversations/{conv}/messages", headers=h, json={"body": "hey, wanna play valorant?"})
    assert r.status_code == 201
    await asyncio.sleep(2.2)
    bodies = [m["body"] for m in (await client.get(f"/conversations/{conv}/messages", headers=h)).json()]
    assert bodies[-2] == "hey, wanna play valorant?"
    assert bodies[-1] != bodies[-2], "guide replied"

    r = await client.post(f"/matches/{match['id']}/reveal/consent", headers=h)
    assert r.json()["reveal"]["my_stage"] == 1
    await asyncio.sleep(2.2)
    r = await client.get(f"/matches/{match['id']}", headers=h)
    assert r.json()["reveal"] == {
        "my_stage": 3,
        "their_stage": 3,
        "my_consent": True,
        "their_consent": True,
        "early_request_from_me": False,
        "early_request_from_them": False,
    }
