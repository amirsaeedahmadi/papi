from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from payments.tests.factories import WalletFactory
from users.factories import UserFactory


class GatewayDepositTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("transaction-gateway-deposit")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email_verified=True, mobile_verified=True)
        cls.accountable = UserFactory(is_staff=True, roles=["payments.accountable"])
        cls.wallet = WalletFactory(user=cls.user)

    def test_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_accountable(self):
        self.client.force_authenticate(self.accountable)
        response = self.client.post(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bank_is_required(self):
        self.client.force_authenticate(self.user)
        data = {
            "amount": 10,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_bank(self):
        self.client.force_authenticate(self.user)
        data = {
            "amount": 10,
            "bank": 100
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_amount_is_required(self):
        self.client.force_authenticate(self.user)
        data = {
            "bank": 0
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful(self):
        self.client.force_authenticate(self.user)
        data = {
            "amount": 10,
            "bank": 0
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn("payment_url", data)
        self.assertIn("mock-gateway", data["payment_url"])
