from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import ManualDeposit, GatewayDeposit
from .models import Transaction
from .models import Wallet

class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = "__all__"

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = "__all__"
        depth = 1


class DefaultWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        exclude = ("user",)
        depth = 1


class ManualDepositDefaultWalletSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=0, required=False,
                                      write_only=True)
    class Meta:
        model = ManualDeposit
        fields = "__all__"

class GatewayDepositDefaultWalletSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=0, write_only=True)
    class Meta:
        model = GatewayDeposit
        fields = ("amount", "bank")


class AmountSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=0)


class TransactionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"

class TransactionSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer(read_only=True)
    class Meta:
        model = Transaction
        exclude = ("wallet", "object_id")
