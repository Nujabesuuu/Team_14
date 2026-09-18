import os
from collections.abc import AsyncIterator
from datetime import date

import pytest
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["MEDIA_DIR"] = "./.test-media"

from app.core.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
async def _fresh_schema() -> AsyncIterator[None]:
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c


class UserFactory:
    """Registers users through the public API and returns auth headers."""

    def __init__(self, client: AsyncClient) -> None:
        self.client = client
        self.counter = 0

    async def __call__(
        self,
        email: str | None = None,
        birth_date: date = date(2000, 1, 1),
        premium: bool = False,
        display_name: str | None = None,
    ) -> tuple[dict, dict[str, str]]:
        self.counter += 1
        email = email or f"user{self.counter}@test.dev"
        r = await self.client.post(
            "/auth/register",
            json={
                "email": email,
                "password": "secret123",
                "display_name": display_name or f"User {self.counter}",
                "birth_date": birth_date.isoformat(),
            },
        )
        assert r.status_code == 201, r.text
        data = r.json()
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        if premium:
            r = await self.client.post("/me/premium", json={"enabled": True}, headers=headers)
            assert r.status_code == 200, r.text
        return data["user"], headers


@pytest.fixture
def make_user(client: AsyncClient) -> UserFactory:
    return UserFactory(client)
