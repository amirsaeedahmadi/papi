from urllib.parse import urlencode
from django.test import TestCase
from django.urls import reverse

from payments.tests.factories import WalletFactory, ManualDepositTransactionFactory, \
    GatewayDepositTransactionFactory
from users.factories import UserFactory


class GatewayDepositCallbackTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("gateway-deposit-callback")
        cls.tx = GatewayDepositTransactionFactory()

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email_verified=True, mobile_verified=True)
        cls.wallet = WalletFactory(user=cls.user)
        cls.tx = ManualDepositTransactionFactory(wallet=cls.wallet)

    def test_valid_transaction(self):
        url = self.url+"?"+urlencode({"token": self.tx.content_object.token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_invalid_transaction(self):
        url = self.url+"?"+urlencode({"token": "invalid_token"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
