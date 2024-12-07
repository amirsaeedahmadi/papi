from django.conf import settings
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views.wallet import GatewayDepositCallbackView
from .views.wallet import GetDefaultWalletView
from .views.wallet import ListWalletsView
from .views.wallet import MockGatewayView
from .views.wallet import TransactionViewSet

router = SimpleRouter()
router.register(r"transactions", TransactionViewSet)

urlpatterns = [
    path("default-wallet/", GetDefaultWalletView.as_view(), name="default-wallet"),
    path("wallets/", ListWalletsView.as_view(), name="wallet-list"),
    path(
        "gateway-deposit-callback/",
        GatewayDepositCallbackView.as_view(),
        name="gateway-deposit-callback",
    ),
]

if settings.MOCK_PAYMENTS:
    urlpatterns += [
        path("mock-gateway/", MockGatewayView.as_view(), name="mock-gateway")
    ]

urlpatterns += router.urls
