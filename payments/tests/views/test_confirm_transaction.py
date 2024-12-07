from unittest.mock import patch
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from payments.tests.factories import WalletFactory, ManualDepositTransactionFactory
from users.factories import UserFactory


class ConfirmTransactionTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email_verified=True, mobile_verified=True)
        cls.staff = UserFactory(is_staff=True)
        cls.superuser = UserFactory(is_staff=True, is_superuser=True)
        cls.accountable = UserFactory(is_staff=True, roles=["payments.accountable"])
        cls.wallet = WalletFactory(user=cls.user)
        cls.tx = ManualDepositTransactionFactory(wallet=cls.wallet)
        cls.url = reverse("transaction-confirm", kwargs={"pk": cls.tx.pk})

    def test_unauthenticated(self):
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_not_admin_host(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("utils.kafka.KafkaEventStore.add_event")
    def test_successful(self, add_event):
        self.client.force_authenticate(self.accountable)
        data = {
            "amount": 100
        }
        response = self.client.patch(self.url, data,
                                    headers={"host": "api.admin.testserver"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        add_event.assert_called()
        data = response.json()
        self.assertIn("content_type", data)
        self.assertIn("model", data["content_type"])
        self.assertEqual(data["content_type"]["model"], "manualdeposit")
        self.assertIn("amount", data)
        self.assertEqual(data["amount"], "100")
