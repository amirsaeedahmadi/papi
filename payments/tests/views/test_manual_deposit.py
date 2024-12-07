from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from payments.tests.factories import WalletFactory
from users.factories import UserFactory
from utils.files import uploaded_image_file


class ManualDepositTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("transaction-manual-deposit")

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

    def test_file_is_required(self):
        self.client.force_authenticate(self.user)
        data = {"amount": 10}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful(self):
        self.client.force_authenticate(self.user)
        data = {"file": uploaded_image_file()}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn("content_type", data)
        self.assertIn("model", data["content_type"])
        self.assertEqual(data["content_type"]["model"], "manualdeposit")
        self.assertIn("amount", data)
        self.assertEqual(data["amount"], None)

    def test_amount(self):
        self.client.force_authenticate(self.user)
        data = {"file": uploaded_image_file(), "amount": 10}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn("amount", data)
        self.assertEqual(data["amount"], "10")
