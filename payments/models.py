import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from utils.models import BaseModel

User = get_user_model()


class WalletManager(models.Manager):
    def get_default_wallet(self, user):
        return self.get(user=user, type=self.model.DEFAULT)


class Wallet(BaseModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="wallet")
    DEFAULT = 0
    CREDIT = 1
    TYPE_CHOICES = {DEFAULT: _("Default"), CREDIT: _("Credit")}
    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES)
    balance = models.DecimalField(max_digits=12, decimal_places=0, default=Decimal("0"))

    objects = WalletManager()

    class Meta:
        unique_together = ("user", "type")
        ordering = ["-created_at"]


def upload_manual_deposit_file(instance, filename):
    return f"manual_deposits/{instance.pk}/{filename}"


class ManualDeposit(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="manual_deposits", editable=False
    )
    file = models.FileField(upload_to=upload_manual_deposit_file)


class GatewayDeposit(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="gateway_deposits", editable=False
    )
    NOVIN_PAY = 0
    BANK_CHOICES = {NOVIN_PAY: _("Novin Pay")}
    bank = models.PositiveSmallIntegerField(choices=BANK_CHOICES)
    token = models.CharField(max_length=64)
    rrn = models.BigIntegerField(null=True)


class Order(BaseModel):
    id = models.UUIDField(primary_key=True)
    via_credit = models.BooleanField()


class CreditSettlement(BaseModel):
    pass


class CreditDeposit(BaseModel):
    pass


class Transaction(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=0, null=True)
    balance = models.DecimalField(max_digits=12, decimal_places=0, null=True)
    # ManualDeposit, GatewayDeposit, CreditSettlement, Purchase, CreditDeposit
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="transactions"
    )
    object_id = models.CharField()
    content_object = GenericForeignKey("content_type", "object_id")
    confirmed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("content_type", "object_id")
        ordering = ["-created_at"]
