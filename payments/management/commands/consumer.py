import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from payments.events import TransactionConfirmed
from payments.services import wallet_service
from users.services import UserService
from utils.kafka import create_consumer

logger = logging.getLogger(__name__)
User = get_user_model()

on_order_resource_allocated = wallet_service.on_order_resource_allocated


class Command(BaseCommand):
    help = "Starts consuming events and tasks."

    TOPICS = ["Users", "Transactions", "Orders"]

    CALLBACKS = {
        "UserCreated": lambda body: UserService.on_user_created(**body),
        "UserUpdated": lambda body: UserService.on_user_updated(**body),
        "UserDeleted": lambda body: User.objects.filter(pk=body["id"]).delete(),
        "OrderResourceAllocated": lambda body: on_order_resource_allocated(**body),
        "OrderPaid": lambda body: wallet_service.pay_order(**body),
        "OrderResourceAllocationFailed": lambda body: wallet_service.refund_order(
            **body
        ),
        TransactionConfirmed.name: lambda body: wallet_service.confirm_transaction(
            **body
        ),
    }

    def on_message(self, message):
        tp = message.value["type"]
        callback = self.CALLBACKS.get(tp)
        if callback:
            body = message.value["payload"]
            callback(body)

    def handle(self, *args, countdown=3, **options):
        bootstrap_servers = settings.KAFKA_URL
        logger.info("Connecting to Kafka...")
        # Create Kafka consumer
        consumer = create_consumer(bootstrap_servers, "paymentapi", self.TOPICS)
        consumer.start_consuming(on_message=self.on_message)
