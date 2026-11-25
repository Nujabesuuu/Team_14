"""US-01. Реєстрація з перевіркою 18+ (BR-01, NEVER-04, NEVER-07). Written from requirements and contracts."""

from datetime import UTC, date, datetime, timedelta

import pytest

from tests.helpers import create_event, onboard, seed_games

PASSWORD = "secret123"
PRIVATE_KEYS = {"birth_date", "password_hash", "password"}


def registration_day() -> date:
    # Stored time is UTC (A-03), so "the day of registration" is the UTC date.
    return datetime.now(UTC).date()


def born_years_ago(years: int, *, days_later: int = 0) -> date:
    today = registration_day()
    try:
        birthday = today.replace(year=today.year - years)
    except ValueError:  # 29 February in a non-leap year: the birthday has not come yet, so take 1 March
        birthday = date(today.year - years, 3, 1)
    return birthday + timedelta(days=days_later)


def all_keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in all_keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in all_keys(v)}
    return set()


def register(client, email: str, birth_date: date, display_name: str = "Olena"):
    return client.post(
        "/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": display_name, "birth_date": birth_date.isoformat()},
    )


# Birth dates are computed inside the test, not at collection: the suite runs ~2.5 min, and a run that crossed
# midnight UTC turned "17 years 364 days" into an 18th birthday (found by the audit, prompt 6.3).
@pytest.mark.parametrize(
    "age",
    [25, 18],
    ids=["25 years | lands on Game DNA", "exactly 18 years | lands on Game DNA"],
)
async def test_adult_registers_and_lands_on_game_dna(client, age):
    """US-01 Scenario Outline: Межа віку 18 років — accepted rows (also «Дорослий гравець створює акаунт»)."""
    r = await register(client, "olena@test.dev", born_years_ago(age))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["token_type"] == "bearer" and body["access_token"]
    assert body["user"]["age"] == age

    me = await client.get("/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["user"]["id"] == body["user"]["id"]
    assert me.json()["profile"]["onboarded"] is False, "a new account goes to Game DNA first"


@pytest.mark.parametrize(
    "years,days_later",
    [(18, 1), (16, 0)],
    ids=["17 years 364 days | 18+ only, no account", "16 years | 18+ only, no account"],
)
async def test_minor_is_refused_and_no_account_is_created(client, years, days_later):
    """US-01 Scenario Outline: Межа віку 18 років — refused rows (BR-01, NEVER-04)."""
    r = await register(client, "maksym@test.dev", born_years_ago(years, days_later=days_later))
    assert r.status_code == 422 and r.json()["code"] == "TOO_YOUNG"
    assert "access_token" not in r.json()

    login = await client.post("/auth/login", json={"email": "maksym@test.dev", "password": PASSWORD})
    assert login.status_code == 401 and login.json()["code"] == "INVALID_CREDENTIALS", "no account may exist"


async def test_refused_minor_sees_no_events_and_no_profiles(client, make_user):
    """US-01 Scenario: Неповнолітній не потрапляє до вмісту застосунку."""
    games = await seed_games()
    _, host_h = await make_user()
    await onboard(client, host_h, games=[games["valorant"]])
    event = await create_event(client, host_h, games["valorant"])

    r = await register(client, "maksym@test.dev", born_years_ago(17))
    assert r.status_code == 422 and r.json()["code"] == "TOO_YOUNG"
    assert "access_token" not in r.json()

    # Content is closed to him only because he can get no token at all: the refusal gave none, and there is no
    # account to log into. (Without a token any endpoint says 401 — that part alone would prove nothing.)
    login = await client.post("/auth/login", json={"email": "maksym@test.dev", "password": PASSWORD})
    assert login.status_code == 401 and login.json()["code"] == "INVALID_CREDENTIALS"
    for path in ("/events", f"/events/{event['id']}", "/discover?mode=duo"):
        r = await client.get(path)
        assert r.status_code == 401 and r.json()["code"] == "UNAUTHORIZED", path


async def test_returning_user_sees_her_own_profile(client):
    """US-01 Scenario: Повторний вхід."""
    games = await seed_games()
    r = await register(client, "olena@test.dev", born_years_ago(22))
    assert r.status_code == 201
    first = r.json()
    first_h = {"Authorization": f"Bearer {first['access_token']}"}
    await onboard(client, first_h, games=[games["overcooked-2"]], bio="Overcooked enjoyer")

    login = await client.post("/auth/login", json={"email": "olena@test.dev", "password": PASSWORD})
    assert login.status_code == 200
    me = await client.get("/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.status_code == 200
    assert me.json()["user"]["id"] == first["user"]["id"]
    assert me.json()["user"]["email"] == "olena@test.dev"
    assert me.json()["profile"]["bio"] == "Overcooked enjoyer"
    assert me.json()["profile"]["onboarded"] is True


async def test_own_account_responses_never_contain_birth_date_or_password(client):
    """US-01 + NEVER-07: Account carries `age`, never birth_date or password_hash (contracts/api.md, Account)."""
    r = await register(client, "olena@test.dev", born_years_ago(22))
    assert r.status_code == 201
    login = await client.post("/auth/login", json={"email": "olena@test.dev", "password": PASSWORD})
    assert login.status_code == 200
    me = await client.get("/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.status_code == 200

    for name, body in (("register", r.json()), ("login", login.json()), ("GET /me", me.json())):
        assert not all_keys(body) & PRIVATE_KEYS, name


async def test_other_players_see_only_public_user(client, make_user):
    """US-01 + NEVER-07: what others see is PublicUser — no email, birth_date or password_hash."""
    games = await seed_games()
    _, host_h = await make_user(email="taras@test.dev")
    _, olena_h = await make_user()
    await onboard(client, host_h, games=[games["valorant"]])
    await onboard(client, olena_h, games=[games["valorant"]])
    event = await create_event(client, host_h, games["valorant"])

    r = await client.get(f"/events/{event['id']}", headers=olena_h)
    assert r.status_code == 200
    assert not all_keys(r.json()) & (PRIVATE_KEYS | {"email"})
    assert "taras@test.dev" not in r.text
