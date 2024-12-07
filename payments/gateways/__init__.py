from django.conf import settings

from .novin_pay import NovinPay

novin_pay = NovinPay(settings.NOVINPAY_CORPORATION_PIN)
