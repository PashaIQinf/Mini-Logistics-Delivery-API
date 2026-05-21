from app.models import Order_status

# Разрешённые переходы статусов
ALLOWED_TRANSITIONS = {
    Order_status.CREATED: [Order_status.SEARCHING, Order_status.CANCELLED],
    Order_status.SEARCHING: [Order_status.IN_DELIVERY, Order_status.CANCELLED],
    Order_status.IN_DELIVERY: [Order_status.DELIVERED],
    Order_status.DELIVERED: [],
    Order_status.CANCELLED: []
}

# Проверяет, разрешён ли переход между статусами
def can_transition(from_status: Order_status, to_status: Order_status) -> bool:
    return to_status in ALLOWED_TRANSITIONS.get(from_status, [])

# Возвращает список доступных следующих статусов
def get_available_transitions(current_status: Order_status) -> list[Order_status]:
    return ALLOWED_TRANSITIONS.get(current_status, [])