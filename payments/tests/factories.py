import uuid
import factory
from django.contrib.contenttypes.models import ContentType
from faker import Faker

from payments.models import GatewayDeposit
from payments.models import ManualDeposit
from payments.models import Order
from payments.models import Transaction
from payments.models import Wallet
from users.factories import UserFactory
from utils import tokens

faker = Faker()


class WalletFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Wallet

    type = Wallet.DEFAULT
    user = factory.SubFactory(UserFactory)


class ManualDepositFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = ManualDeposit


class GatewayDepositFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    bank = GatewayDeposit.NOVIN_PAY
    token = factory.LazyAttribute(lambda _: tokens.generate_uppercase_code())

    class Meta:
        model = GatewayDeposit


class OrderFactory(factory.django.DjangoModelFactory):
    id = factory.LazyAttribute(lambda _: uuid.uuid4())
    via_credit = faker.boolean()

    class Meta:
        model = Order


class AbstractTransactionFactory(factory.django.DjangoModelFactory):
    id = factory.LazyAttribute(lambda _: uuid.uuid4())
    wallet = factory.SubFactory(WalletFactory)

    class Meta:
        abstract = True


class ManualDepositTransactionFactory(AbstractTransactionFactory):
    content_type = ContentType.objects.get(app_label="payments", model="manualdeposit")
    content_object = factory.SubFactory(ManualDepositFactory)
    object_id = factory.SelfAttribute("content_object.pk")

    class Meta:
        model = Transaction


class GatewayDepositTransactionFactory(AbstractTransactionFactory):
    content_type = ContentType.objects.get(app_label="payments", model="gatewaydeposit")
    content_object = factory.SubFactory(GatewayDepositFactory)
    object_id = factory.SelfAttribute("content_object.pk")

    class Meta:
        model = Transaction


class OrderTransactionFactory(AbstractTransactionFactory):
    content_type = ContentType.objects.get(app_label="payments", model="order")
    content_object = factory.SubFactory(OrderFactory)
    object_id = factory.SelfAttribute("content_object.pk")

    class Meta:
        model = Transaction
