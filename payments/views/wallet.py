from django.http import Http404
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import mixins
from rest_framework import viewsets

from payments.models import Transaction
from payments.models import Wallet
from payments.permissions import HasAccountableRole
from payments.serializers import AmountSerializer, TransactionSerializer, \
    GatewayDepositDefaultWalletSerializer
from payments.serializers import DefaultWalletSerializer
from payments.serializers import ManualDepositDefaultWalletSerializer
from payments.serializers import WalletSerializer
from payments.services import wallet_service
from users.permissions import EmailVerified
from users.permissions import IsAdminHost
from users.permissions import IsNotAdminHost
from users.permissions import MobileVerified

class GetDefaultWalletView(APIView):
    permission_classes = (IsNotAdminHost, EmailVerified, MobileVerified)

    def get(self, request):
        try:
            instance = Wallet.objects.get_default_wallet(request.user)
        except Wallet.DoesNotExist as e:
            raise NotFound(_("Wallet does not exist.")) from e

        serializer = DefaultWalletSerializer(instance)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class ListWalletsView(ListAPIView):
    permission_classes = (IsAdminHost, HasAccountableRole)
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    filterset_fields = ("user",)

class TransactionViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filterset_fields = ("wallet", "confirmed", "content_type__model")

    def get_permission_classes(self):
        if self.action in ["manual_deposit", "gateway_deposit"]:
            return [IsNotAdminHost, EmailVerified, MobileVerified]
        if self.action in ["confirm"]:
            return [IsAdminHost, HasAccountableRole]
        if self.request.is_admin_host:
            return [HasAccountableRole]
        return [IsNotAdminHost, EmailVerified, MobileVerified]

    def get_permissions(self):
        return [permission() for permission in self.get_permission_classes()]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.is_admin_host:
            return qs.filter(wallet__user=self.request.user)
        return qs

    @action(methods=["POST"], detail=False,
            serializer_class=ManualDepositDefaultWalletSerializer,
            url_path="manual-deposit")
    def manual_deposit(self, request):
        try:
            instance = Wallet.objects.get_default_wallet(request.user)
        except Wallet.DoesNotExist as e:
            raise NotFound(_("Wallet does not exist.")) from e

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tx = wallet_service.manual_deposit(
            instance, serializer.validated_data["file"],
            amount=serializer.validated_data.get("amount")
        )
        serializer = TransactionSerializer(tx)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=["POST"], detail=False,
            serializer_class=GatewayDepositDefaultWalletSerializer,
            url_path="gateway-deposit")
    def gateway_deposit(self, request):
        try:
            instance = Wallet.objects.get_default_wallet(request.user)
        except Wallet.DoesNotExist as e:
            raise NotFound(_("Wallet does not exist.")) from e

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment_url = wallet_service.get_payment_url(
            instance,
            serializer.validated_data["amount"],
            serializer.validated_data["bank"],
            request=request
        )
        data = {"payment_url": payment_url}
        return Response(data, status=status.HTTP_201_CREATED)

    @action(methods=["PATCH"], detail=True, serializer_class=AmountSerializer)
    def confirm(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tx = wallet_service.confirm_manual_deposit(
            instance, serializer.validated_data["amount"]
        )
        serializer = TransactionSerializer(tx)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GatewayDepositCallbackView(TemplateView):
    template_name = "payments/deposit_callback.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                # "rrn": kwargs["rrn"],
            }
        )
        return context

    def get(self, request, *args, **kwargs):
        token = request.GET.get("token")
        try:
            wallet_service.confirm_gateway_payment(token)
        except NotFound as e:
            raise Http404 from e
        return super().get(request, *args, **kwargs)

class MockGatewayView(TemplateView):
    template_name = "payments/mock_gateway.html"
