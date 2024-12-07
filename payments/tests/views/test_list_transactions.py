from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from payments.tests.factories import GatewayDepositTransactionFactory
from payments.tests.factories import ManualDepositTransactionFactory
from payments.tests.factories import OrderTransactionFactory
from payments.tests.factories import WalletFactory
from users.factories import UserFactory


class ListTransactionsTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("transaction-list")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email_verified=True, mobile_verified=True)
        cls.staff = UserFactory(is_staff=True)
        cls.superuser = UserFactory(is_staff=True, is_superuser=True)
        cls.accountable = UserFactory(is_staff=True, roles=["payments.accountable"])
        cls.wallet = WalletFactory(user=cls.user)
        ManualDepositTransactionFactory(wallet=cls.wallet)
        GatewayDepositTransactionFactory(wallet=cls.wallet)
        ManualDepositTransactionFactory.create_batch(7)
        GatewayDepositTransactionFactory.create_batch(8)
        OrderTransactionFactory.create_batch(3)

    def test_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_on_admin_host(self):
        response = self.client.get(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_successful(self):
        self.client.force_authenticate(self.accountable)
        response = self.client.get(self.url, headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 10)

    def test_filter_by_wallet(self):
        self.client.force_authenticate(self.accountable)
        response = self.client.get(
            self.url,
            {"wallet": self.wallet.pk},
            headers={"host": "api.admin.testserver"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 2)

    def test_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 2)