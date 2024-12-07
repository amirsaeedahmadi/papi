import requests
from requests import HTTPError


class NovinPay:
    def __init__(self, corporation_pin):
        self.corporation_pin = corporation_pin

    def get_token(self, amount, order_id, callback_url, **kwargs):
        payload = {
            "CorporationPin": self.corporation_pin,
            "Amount": amount,
            "OrderId": order_id,
            "CallBackUrl": callback_url,
            "AdditionalData": kwargs.get("additional_data", ""),
            "Originator": kwargs.get("mobile", ""),
        }
        response = requests.post(
            "https://pna.shaparak.ir/mhipg/api/Payment/NormalSale",
            json=payload,
            timeout=5,
        )
        response.raise_for_status()
        response_data = response.json()
        if response_data["status"] == 0:
            return response_data["token"]
        raise HTTPError(response.text, response=response)

    @staticmethod
    def get_payment_url(token):
        return f"https://pna.shaparak.ir/mhui/home/index/{token}"

    def confirm_payment(self, token):
        payload = {
            "CorporationPin": self.corporation_pin,
            "Token": token,
        }
        response = requests.post(
            "https://pna.shaparak.ir/mhipg/api/Payment/confirm", json=payload, timeout=5
        )
        response.raise_for_status()
        response_data = response.json()
        if response_data["status"] == 0:
            return response.json()
        raise HTTPError(response.text, response=response)

    def reverse_payment(self, token):
        payload = {
            "CorporationPin": self.corporation_pin,
            "Token": token,
        }
        response = requests.post(
            "https://pna.shaparak.ir/mhipg/api/Payment/Reverse", json=payload, timeout=5
        )
        response.raise_for_status()
        response_data = response.json()
        if response_data["status"] == 0:
            return response
        raise HTTPError(response.text, response=response)
