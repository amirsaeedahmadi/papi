import logging

from django.conf import settings

from payments.services.wallet import WalletService
from utils.kafka import KafkaEventStore

logger = logging.getLogger(__name__)
bootstrap_servers = settings.KAFKA_URL
kafka_event_store = KafkaEventStore(bootstrap_servers=bootstrap_servers)

wallet_service = WalletService(kafka_event_store)
