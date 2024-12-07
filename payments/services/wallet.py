import logging
from urllib.parse import urlencode
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from requests import HTTPError
from requests import RequestException
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse

from payments.events import OrderPaid
from payments.events import OrderPaymentFailed
from payments.events import TransactionConfirmed
from payments.gateways import novin_pay
from payments.models import GatewayDeposit
from payments.models import ManualDeposit
from payments.models import Order
from payments.models import Transaction
from payments.models import Wallet
from payments.serializers import TransactionEventSerializer
from payments.services.exceptions import PaymentGatewayError
from utils import tokens

User = get_user_model()
logger = logging.getLogger(__name__)


class WalletService:
    def __init__(self, event_store):
        self.event_store = event_store

    @staticmethod
    def manual_deposit(wallet, file, amount=None):
        with transaction.atomic():
            dep = ManualDeposit.objects.create(user=wallet.user, file=file)
            content_type = ContentType.objects.get(
                app_label="payments", model="manualdeposit"
            )
            return Transaction.objects.create(
                wallet=wallet,
                content_type=content_type,
                object_id=dep.pk,
                amount=amount,
            )

    def confirm_manual_deposit(self, tx, amount):
        if tx.confirmed or tx.content_type.model != "manualdeposit":
            raise ValidationError(detail=_("Invalid operation on this transaction"))
        tx.amount = amount
        tx.confirmed = True
        serializer = TransactionEventSerializer(tx)
        event = TransactionConfirmed(serializer.data)
        self.event_store.add_event(event)
        return tx

    @staticmethod
    def get_payment_url(wallet, amount, bank, request=None):
        transaction_id = tokens.generate_integer_code(12)
        callback_url = reverse("gateway-deposit-callback", request=request)
        try:
            with transaction.atomic():
                if settings.MOCK_PAYMENTS:
                    token = tokens.generate_uppercase_code(24)
                else:
                    token = novin_pay.get_token(amount, transaction_id, callback_url)
                dep = GatewayDeposit.objects.create(
                    user=wallet.user, bank=bank, token=token
                )
                content_type = ContentType.objects.get(
                    app_label="payments", model="gatewaydeposit"
                )
                Transaction.objects.create(
                    wallet=wallet,
                    amount=amount,
                    content_type=content_type,
                    object_id=dep.pk,
                )
                if settings.MOCK_PAYMENTS:
                    payment_url = reverse("mock-gateway", request=request)
                    payment_url += "?" + urlencode({"token": token})
                    payment_url += urlencode({"amount": amount})
                    return payment_url
                return novin_pay.get_payment_url(token)
        except HTTPError as e:
            raise PaymentGatewayError(detail=str(e)) from e
        except RequestException as e:
            raise PaymentGatewayError(detail=str(e)) from e

    def confirm_gateway_payment(self, token):
        try:
            dep = GatewayDeposit.objects.get(token=token)
            content_type = ContentType.objects.get(
                app_label="payments", model="gatewaydeposit"
            )
            tx = Transaction.objects.get(
                content_type=content_type, object_id=dep.pk, confirmed=False
            )
        except (GatewayDeposit.DoesNotExist, Transaction.DoesNotExist) as e:
            raise NotFound(detail=_("Transaction not found.")) from e
        try:
            if settings.MOCK_PAYMENTS:
                data = {"status": 0, "message": "Gateway payment confirmed."}
            else:
                data = novin_pay.confirm_payment(token)
            if data["status"] == 0:
                tx.confirmed = True
                serializer = TransactionEventSerializer(tx)
                event = TransactionConfirmed(serializer.data)
                self.event_store.add_event(event)
                return tx
            raise PaymentGatewayError(detail=data["message"])
        except HTTPError as e:
            raise PaymentGatewayError(detail=str(e)) from e
        except RequestException as e:
            raise PaymentGatewayError(detail=str(e)) from e

    @staticmethod
    def confirm_transaction(**kwargs):
        with transaction.atomic():
            updated = Transaction.objects.filter(
                pk=kwargs["id"], confirmed=False
            ).update(confirmed=True)
            if updated:
                Wallet.objects.filter(pk=kwargs["wallet"]).update(
                    balance=F("balance") + kwargs["amount"]
                )
            else:
                msg = f"No unconfirmed transaction with ID `{kwargs['id']}` found."
                logger.warning(msg)

    def on_order_resource_allocated(self, **kwargs):
        user_id = kwargs["user"]
        amount = kwargs["payable_amount"]
        user = User.objects.get(pk=user_id)
        wallet = Wallet.objects.get_default_wallet(user)
        if wallet.balance < amount:
            event = OrderPaymentFailed(kwargs)
        else:
            kwargs["transaction_id"] = uuid4()
            event = OrderPaid(kwargs)
        self.event_store.add_event(event)

    def pay_order(self, **kwargs):
        order_id = kwargs["id"]
        user_id = kwargs["user"]
        amount = kwargs["payable_amount"]
        transaction_id = kwargs["transaction_id"]
        with transaction.atomic():
            wallet = (
                Wallet.objects.filter(user_id=user_id, type=Wallet.DEFAULT)
                .select_for_update()
                .get()
            )
            if wallet.balance < amount:
                event = OrderPaymentFailed(kwargs)
                self.event_store.add_event(event)
                return None
            order = Order.objects.create(pk=order_id)
            content_type = ContentType.objects.get(app_label="payments", model="order")
            tx = Transaction.objects.create(
                pk=transaction_id,
                wallet=wallet,
                amount=amount,
                content_type=content_type,
                object_id=order.pk,
                confirmed=True,
            )
            wallet.balance -= amount
            wallet.save()
            return tx

    def refund_order(self, **kwargs):
        order_id = kwargs["id"]
        user_id = kwargs["user"]
        amount = kwargs["payable_amount"]
        with transaction.atomic():
            wallet = (
                Wallet.objects.filter(user_id=user_id, type=Wallet.DEFAULT)
                .select_for_update()
                .get()
            )
            order = Order.objects.get(pk=order_id)
            content_type = ContentType.objects.get(app_label="payments", model="order")
            tx = Transaction.objects.create(
                wallet=wallet,
                amount=-amount,
                content_type=content_type,
                object_id=order.pk,
                confirmed=True,
            )
            wallet.balance += amount
            wallet.save()
            return tx
