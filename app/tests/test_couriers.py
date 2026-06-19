from fastapi import status
from .conftest import register_user, create_product, create_order, login_user

def test_courier_accepts_order(test_client):
    # Курьер может принять заказ со статусом SEARCHING
    # 1. Сначала регистрируем клиента
    user_data = register_user(test_client, "client1@example.com", phone_number="+79806508725", role="user")
    user_auth = login_user(test_client, user_data["email"])
    user_token = user_auth["access_token"]

    # 2. Потом регистрируем курьера
    courier_data = register_user(test_client, "courier1@example.com", phone_number="+79806508720", role="courier")
    courier_auth = login_user(test_client, courier_data["email"])
    courier_token = courier_auth["access_token"]

    # 2. Создаем продукт к заказу
    product = create_product(test_client, courier_token, price=100.00)



    # 3. Потом создаём заказ (он будет в статусе CREATED)
    order_response = create_order(test_client, user_token, product["id"], quantity=2)
    order_id = order_response["id"]

    # 3. Меняем статус на SEARCHING (через клиента)
    change_response = test_client.patch(
        f"/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"new_status": "Поиск курьера", "comment": "Ищем курьера"}
    )

    # 4. Курьер принимает заказ
    response = test_client.post(
        f"/couriers/orders/{order_id}/accept",
        headers={"Authorization": f"Bearer {courier_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "В пути"
    assert data["courier_id"] is not None


def test_courier_cannot_accept_already_assigned(test_client):
    # Нельзя принять заказ, который уже назначен
    # 1. Сначала регистрируем клиента
    user_data = register_user(test_client, "client11@example.com", phone_number="+79806508715", role="user")
    user_auth = login_user(test_client, user_data["email"])
    user_token = user_auth["access_token"]

    # 2. Потом регистрируем первого курьера
    courier_one_data = register_user(test_client, "courier11@example.com", phone_number="+79806508710", role="courier")
    courier_one_auth = login_user(test_client, courier_one_data["email"])
    courier_one_token = courier_one_auth["access_token"]

    # 3. Потом регистрируем вторгого курьера
    courier_two_data = register_user(test_client, "courier21@example.com", phone_number="+79806508711", role="courier")
    courier_two_auth = login_user(test_client, courier_two_data["email"])
    courier_two_token = courier_two_auth["access_token"]

    # 4. Создаем продукт к заказу
    product = create_product(test_client, courier_one_token, price=100.00)

    # 5. Клиент создает заказ
    order_response = create_order(test_client, user_token, product["id"], quantity=2)
    order_id = order_response["id"]

    # 6. Переводим в SEARCHING
    test_client.patch(
        f"/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"new_status": "Поиск курьера"}
    )

    # 7. Первый курьер принимает
    test_client.post(
        f"/couriers/orders/{order_id}/accept",
        headers={"Authorization": f"Bearer {courier_one_token}"}
    )

    # 8. Второй курьер пытается принять тот же заказ — должен получить ошибку
    response = test_client.post(
        f"/couriers/orders/{order_id}/accept",
        headers={"Authorization": f"Bearer {courier_two_token}"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_non_courier_cannot_accept(test_client):
    # Обычный пользователь не может принимать заказы
    # 1. Сначала регистрируем клиента
    user_data = register_user(test_client, "client21@example.com", phone_number="+79806508735", role="user")
    user_auth = login_user(test_client, user_data["email"])
    user_token = user_auth["access_token"]

    # 2. Создаем продукт к заказу
    product = create_product(test_client, user_token, price=100.00)

    # 3. Клиент создает заказ
    order_response = create_order(test_client, user_token, product["id"], quantity=2)
    order_id = order_response["id"]

    # 4. Переводим в SEARCHING
    test_client.patch(
        f"/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"new_status": "Поиск курьера"}
    )

    response = test_client.post(
        f"/couriers/orders/{order_id}/accept",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN