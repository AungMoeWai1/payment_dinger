# -*- coding: utf-8 -*-
# pylint: disable=missing-class-docstring,missing-function-docstring
import json
from datetime import datetime
from odoo.http import route, request, Controller
from ..dataclasses.datamodels import JournalCodeEnum, TransactionStatusEnum

@staticmethod
def convert_paid_at(date_str: str) -> str:
    """Convert the date string from Dinger format to Odoo format."""
    return datetime.strptime(date_str, "%Y%m%d %H%M%S").strftime("%Y-%m-%d %H:%M:%S")

class DingerPayController(Controller):
    _webhook_url = "/payment/dinger/webhook"
    # secret_key = "d655c33205363f5450427e6b6193e466"

    @route(_webhook_url, type="http", auth="none", csrf=False, methods=["POST"])
    def dinger_webhook(self, **post):

        # post will return like that
        # """{
        # “paymentResult":"5zDOSGSI / YE7wsmX / "
        # +"IlBZb6iH0NpwgRuUL13RY9sEKIvo8oebHCh1FKZ0MKTkvlKPQ6Cn2qYg7UDQssBuMbkVAGWcVPK0WvvrrACrx480jdydrNUcsqX4vsaqHuRlCQa / 7"
        # +"Qfur + W6WNKO4exvOvN25FtE8hDB7ENu37r54wUlGC21bojhq9M15 / Ql5P9 + w1x / "
        # +"Ep13nmyptGOHfI4a4V3D57v0HQ8KqUnOy5P6E4FYOSeOVeVuCJ516RK94OIVAUB3F9jqy4NLm9jqc243pWOR9fwGJK5YplMbOuQFEZKt0 = ",
        # “checksum":"3e6dc224539d382f300f658a26775e75029b26ba0b885196e7ec66feb6a756ae"
        # }"""

        # Get the value of payment result and checksum
        payment_result = post.get("paymentResult")
        # check_sum = post.get("checksum")

        # Then need to decrypt using
        # paymentResult(Needs to decrypt the paymentResult response with Base64 first and then with AES / ECB / PKCS7Padding algorithm)
        # checksum(sha256(jsonString(resultObj))
        # Testing Callback Key - d655c33205363f5450427e6b6193e466

        # Decrypt the payment result
        decrypted_str = request.env["payment.transaction"].sudo().aes_decrypt(payment_result,"prebuilt")

        try:
            result = json.loads(decrypted_str)
        except json.JSONDecodeError:
            print("Failed to parse decrypted data as JSON:")
            print(decrypted_str)
            raise

        # Prepare data for model processing
        webhook_data = {
            "merchant_order": result.get("merchantOrderId"),
            "reference": result.get("transactionId"),
            "state": TransactionStatusEnum.get_internal_value(
                result.get("transactionStatus")
            ),
            "total": float(result.get("totalAmount", 0.0) or 0.0),
            "provider_name": JournalCodeEnum.get_internal_value(
                result.get("providerName")
            ),
            "received_method": result.get("methodName"),
            "customer_name": result.get("customerName"),
            "paid_at": convert_paid_at(result.get("createdAt", "")),
        }
        # Delegate all business logic to the model
        request.env["payment.transaction"].sudo().process_dinger_webhook(webhook_data)

        # Redirect to the payment success page
        return request.redirect("/payment/status")
