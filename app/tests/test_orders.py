from fastapi import status
from .conftest import register_user, create_product, create_order, login_user


def test_create_order_calculates_price(test_client):
    # Проверяет автоматический расчет суммы заказа
    # 1. Регистрируем пользователя
    user_data = register_user(test_client, "user1@example.com", phone_number="+79991234520",role="courier")
    user_auth = login_user(test_client, user_data["email"])
    token = user_auth["access_token"]

    # 2. Создаём товар (цена 100.00)
    product = create_product(test_client, token, price=100.00)

    # 3. Создаём заказ с 3 товарами = должно быть 300.00
    order = create_order(test_client, token, product["id"], quantity=3)

    assert order["price"] == "300.00"
    assert order["status"] == "Создан"
    assert len(order["items"]) == 1
    assert order["items"][0]["price_at_purchase"] == "100.00"


def test_create_order_with_multiple_items(test_client):
    # Заказ с несколькими товарами: сумма считается корректно
    user_data1 = register_user(test_client, "user2@example.com", phone_number="+79991234566")
    user_auth = login_user(test_client, user_data1["email"])
    token = user_auth["access_token"]

    # 1. Создаём два товара
    product1 = create_product(test_client, token, name="Product 1", price=100.00)
    product2 = create_product(test_client, token, name="Product 2", price=50.00)

    # 2. Заказ: 2×100 + 1×50 = 250.00
    response = test_client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "address_from": "ул. А, 1",
            "address_to": "ул. Б, 2",
            "items": [
                {"product_id": product1["id"], "quantity": 2},
                {"product_id": product2["id"], "quantity": 1},
            ]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["price"] == "250.00"


def test_create_order_product_not_found(test_client):
    # Заказ с несуществующим товаром = 404
    user_data = register_user(test_client, "user3@example.com", phone_number="+79991234561")
    user_auth = login_user(test_client, user_data["email"])
    token = user_auth["access_token"]

    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = test_client.post(
        "/orders/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "address_from": "ул. А, 1",
            "address_to": "ул. Б, 2",
            "items": [{"product_id": fake_uuid, "quantity": 1}]
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    test_client.close()


def test_create_order_without_token(test_client):
    # Создание заказа без токена = 401
    response = test_client.post(
        "/orders/",
        json={
            "address_from": "ул. А, 1",
            "address_to": "ул. Б, 2",
            "items": [{"product_id": "00000000-0000-0000-0000-000000000000", "quantity": 1}]
        }
    )
    print(response.json())
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_order_status_valid_transition(test_client):
    # Допустимый переход: CREATED => SEARCHING
    user_data = register_user(test_client, "user4@example.com",  phone_number="+79991234569")
    user_auth = login_user(test_client, user_data["email"])
    token = user_auth["access_token"]

    product = create_product(test_client, token)
    order = create_order(test_client, token, product["id"])
    order_id = order["id"]

    # Меняем статус
    response = test_client.patch(
        f"/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "new_status": "Поиск курьера",
            "comment": "Передан в поиск курьера"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "Поиск курьера"


def test_update_order_status_invalid_transition(test_client):
    # Недопустимый переход: CREATED => DELIVERED (минуя SEARCHING)
    user_data = register_user(test_client, "user5@example.com", phone_number="+79991234562")
    user_auth = login_user(test_client, user_data["email"])
    token = user_auth["access_token"]

    product = create_product(test_client, token)
    order = create_order(test_client, token, product["id"])
    order_id = order["id"]

    # Пытаемся перейти из CREATED сразу в DELIVERED
    response = test_client.patch(
        f"/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "new_status": "Доставлен",
            "comment": "Попытка пропуска статуса"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_order_not_found(test_client):
    # Получение несуществующего заказа = 404
    user_data = register_user(test_client, "user6@example.com", phone_number="+79991234563")
    user_auth = login_user(test_client, user_data["email"])
    token = user_auth["access_token"]

    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = test_client.get(
        f"/orders/{fake_uuid}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_orders_list(test_client):
    # Получение списка заказов
    user_data = register_user(test_client, "user7@example.com", phone_number="+79991234564")
    user_auth = login_user(test_client, user_data["email"])
    token = user_auth["access_token"]

    product = create_product(test_client, token)
    create_order(test_client, token, product["id"])

    response = test_client.get(
        "/orders/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1