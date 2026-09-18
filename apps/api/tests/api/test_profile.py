import io
from datetime import date

from tests.helpers import seed_games


async def test_update_dna_and_games(client, make_user):
    games = await seed_games()
    _, h = await make_user()
    r = await client.put(
        "/me",
        headers=h,
        json={
            "role": "support",
            "playstyle": "casual",
            "comms": "voice",
            "schedule": ["evening"],
            "toxicity_tolerance": 2,
            "modes": ["duo", "friends"],
            "avatar_key": "duelist",
            "accent_color": "#1E90FF",
            "games": [{"game_id": str(games["valorant"].id), "rank": "Gold"}],
        },
    )
    assert r.status_code == 200, r.text
    p = r.json()["profile"]
    assert p["role"] == "support" and p["avatar_key"] == "duelist"
    assert p["games"][0]["slug"] == "valorant" and p["games"][0]["rank"] == "Gold"
    assert p["onboarded"] is True


async def test_dating_mode_requires_18(client, make_user):
    _, h = await make_user(birth_date=date(date.today().year - 17, 1, 1))
    r = await client.put("/me", headers=h, json={"modes": ["dating"]})
    assert r.status_code == 422 and r.json()["code"] == "DATING_REQUIRES_18"


async def test_unknown_game_rejected(client, make_user):
    _, h = await make_user()
    r = await client.put("/me", headers=h, json={"games": [{"game_id": "00000000-0000-0000-0000-000000000001"}]})
    assert r.status_code == 422 and r.json()["code"] == "UNKNOWN_GAME"


async def test_photo_upload(client, make_user, tmp_path):
    _, h = await make_user()
    fake_png = b"\x89PNG\r\n\x1a\n" + b"0" * 64
    r = await client.post("/me/photo", headers=h, files={"file": ("me.png", io.BytesIO(fake_png), "image/png")})
    assert r.status_code == 200, r.text
    assert r.json()["photo_url"].startswith("/media/")

    bad = await client.post("/me/photo", headers=h, files={"file": ("x.gif", io.BytesIO(b"gif"), "image/gif")})
    assert bad.status_code == 422 and bad.json()["code"] == "UNSUPPORTED_PHOTO"


async def test_premium_toggle(client, make_user):
    _, h = await make_user()
    r = await client.post("/me/premium", headers=h, json={"enabled": True})
    assert r.status_code == 200 and r.json()["user"]["is_premium"] is True
    r = await client.post("/me/premium", headers=h, json={"enabled": False})
    assert r.json()["user"]["is_premium"] is False


async def test_games_list(client):
    await seed_games()
    r = await client.get("/games")
    assert r.status_code == 200
    assert {g["slug"] for g in r.json()} >= {"valorant", "among-us"}
