import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.main import app
from app.db.session import get_db
from app.models.user import Base
from app.db.redis import init_redis, close_redis

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_coreauth.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    async with test_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_redis()
    app.dependency_overrides[get_db] = override_get_db
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await close_redis()
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def registered_user(client):
    response = await client.post("/auth/register", json={
        "email": "testuser@example.com",
        "password": "TestPassword123"
    })
    return response.json()


@pytest_asyncio.fixture(scope="function")
async def auth_tokens(client, registered_user):
    response = await client.post("/auth/login", data={
        "username": "testuser@example.com",
        "password": "TestPassword123"
    })
    return response.json()
