from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from payments.tests.factories import WalletFactory
from users.factories import UserFactory


class GetDefaultWalletTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("default-wallet")

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(email_verified=True, mobile_verified=True)
        cls.wallet = WalletFactory(user=cls.user)

    def test_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_wallet_does_not_exist(self):
        self.wallet.delete()
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_successful(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("balance", data)
