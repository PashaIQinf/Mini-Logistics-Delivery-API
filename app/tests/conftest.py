import pytest
import  asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.main import app
from app.database import Base, get_db
from app.config import  settings


TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5433/test_mini_logistics"

settings.TESTING = True

@pytest.fixture(scope="session")
async def engine():
    eng = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        pool_pre_ping=True,
        echo=False,
    )

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield eng

    await asyncio.sleep(0.1)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await asyncio.sleep(0.1)
    await eng.dispose()

@pytest.fixture
async def db_session(engine):
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
def override_get_db(db_session):

    async def _get_db():
      try:
        yield db_session
      finally:
        await db_session.rollback()
        await db_session.close()

    return _get_db


@pytest.fixture
def test_client(override_get_db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


def register_user(test_client, email, password="testpass123", phone_number="+79991234567", role="user"):
    # Регистрирует пользователя через API
    response = test_client.post(
        "/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "birth_date": "1990-05-15",
            "gender": "Мужской",
            "email": email,
            "phone_number": phone_number,
            "password": password,
            "role": role,
            # Для курьера:
            "vehicle_type": "Велосипед" if role == "courier" else None,
            "vehicle_number": "А123БВ777" if role == "courier" else None,
        }
    )
    assert response.status_code == 201, f"Регистрация не удалась: {response.text}"
    return response.json()

def login_user(test_client, email, password="testpass123"):
    # Входит в пользователя через API и возвращает токен
    response = test_client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password
        }
    )
    assert response.status_code == 200, f"Авторизация не удалась: {response.text}"
    return response.json()


def create_product(test_client, token, name="Test Product", price=100.00, weight=1.5):
    # Создаёт товар через API
    response = test_client.post(
        "/products/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": name,
            "description": "Test product",
            "price": price,
            "weight": weight,
        }
    )
    assert response.status_code == 200, f"Создание товара не удалось: {response.text}"
    return response.json()


def create_order(test_client, token, product_id, quantity=1, address_from="ул. А, 1", address_to="ул. Б, 2"):
    # Создаёт заказ через API
    create_test_order = test_client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "address_from": address_from,
            "address_to": address_to,
            "items": [
                {"product_id": product_id, "quantity": quantity}
            ]
        }
    )

    assert create_test_order.status_code == 201, f"Создание заказа не удалось: {create_test_order.text}"

    response = test_client.get(
        f"/orders/{create_test_order.json()['id']}/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Создание заказа не удалось: {response.text}"
    return response.json()
