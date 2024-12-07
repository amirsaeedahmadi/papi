class Event:
    name = None
    topic = "Transactions"

    def __init__(self, data):
        self.data = data
        # key is used as message key
        self.key = data["id"]

    def __str__(self):
        return f"{self.name}: {self.data}"


class TransactionConfirmed(Event):
    name = "TransactionConfirmed"


class OrderPaid(Event):
    name = "OrderPaid"
    topic = "Orders"


class OrderPaymentFailed(Event):
    name = "OrderPaymentFailed"
    topic = "Orders"
