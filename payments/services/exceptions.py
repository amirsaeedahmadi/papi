from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException

HTTP_110_PAYMENT_GATEWAY_ERROR = 400
HTTP_111_INSUFFICIENT_BALANCE_ERROR = 400


class PaymentGatewayError(APIException):
    status_code = HTTP_110_PAYMENT_GATEWAY_ERROR
    default_detail = _("Payment gateway error.")
    default_code = "payment_gateway_error"


class InsufficientBalanceError(APIException):
    status_code = HTTP_111_INSUFFICIENT_BALANCE_ERROR
    default_detail = _("Insufficient balance.")
    default_code = "insufficient_balance_error"
