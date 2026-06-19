from fastapi import status


def test_register_user(test_client):
    # Регистрация нового пользователя
    response = test_client.post(
        "/auth/register",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "birth_date": "1990-05-15",
            "gender": "Мужской",
            "email": "john@example.com",
            "phone_number": "+79991112233",
            "password": "securepass123",
            "role": "user"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "john@example.com"
    assert "id" in data


def test_login_success(test_client):
    # Успешный логин — создаём пользователя через API
    # 1. Регистрация
    reg_response = test_client.post(
        "/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "birth_date": "1990-05-15",
            "gender": "Мужской",
            "email": "test@example.com",
            "phone_number": "+79991234567",
            "password": "testpass123",
            "role": "user"
        }
    )
    assert reg_response.status_code == status.HTTP_201_CREATED

    # 2. Логин
    response = test_client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(test_client):
    # Неверный пароль = 401
    # 1. Регистрация
    test_client.post(
        "/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "birth_date": "1990-05-15",
            "gender": "Мужской",
            "email": "test@example.com",
            "phone_number": "+79991234567",
            "password": "testpass123",
            "role": "user"
        }
    )

    # 2. Логин с неверным паролем
    response = test_client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpass"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_register_duplicate_email(test_client):
    # Регистрация с занятым email = 400
    # 1. Первая регистрация
    first_user = test_client.post(
        "/auth/register",
        json={
            "first_name": "First",
            "last_name": "User",
            "birth_date": "1990-05-15",
            "gender": "Мужской",
            "email": "copyuser@example.com",
            "phone_number": "+79991112202",
            "password": "securepass123",
            "role": "user"
        }
    )

    assert first_user.status_code == 201, f"Первая регистрация не удалась: {first_user.text}"

    # 2. Попытка зарегистрировать с тем же email
    response = test_client.post(
        "/auth/register",
        json={
            "first_name": "Second",
            "last_name": "User",
            "birth_date": "1990-05-15",
            "gender": "Мужской",
            "email": "copyuser@example.com",
            "phone_number": "+79991112244",
            "password": "securepass123",
            "role": "user"
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_protected_endpoint_without_token(test_client):
    # Запрос без токена = 401
    response = test_client.get("/orders/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED