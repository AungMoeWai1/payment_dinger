import logging
import json
from odoo import http
from odoo.http import route, request, Controller
from .decryption_aes_ecb_pkcs7padding import decrypt

class DingerPayController(Controller):
    _webhook_url = '/payment/dinger/webhook'
    secret_key = 'd655c33205363f5450427e6b6193e466'

    @route(_webhook_url, type='http', auth='none', csrf=False, methods=['POST'])
    def dinger_webhook(self, **post):

        #post will return like that
        # """{
        # “paymentResult":"5zDOSGSI / YE7wsmX / IlBZb6iH0NpwgRuUL13RY9sEKIvo8oebHCh1FKZ0MKTkvlKPQ6Cn2qYg7UDQssBuMbkVAGWcVPK0WvvrrACrx480jdydrNUcsqX4vsaqHuRlCQa / 7
        #     Qfur + W6WNKO4exvOvN25FtE8hDB7ENu37r54wUlGC21bojhq9M15 / Ql5P9 + w1x / +Ep13nmyptGOHfI4a4V3D57v0HQ8KqUnOy5P6E4FYOSeOVeVuCJ516RK94OIVAUB3F9jqy4NLm9jqc243pWOR9fwGJK5YplMbOuQFEZKt0 = ",
        # “checksum":"3e6dc224539d382f300f658a26775e75029b26ba0b885196e7ec66feb6a756ae"
        # }"""

        #Get the value of payment result and checksum
        payment_result=post.get('paymentResult')
        check_sum=post.get('checksum')

        # Then need to decrypt using
        # paymentResult(Needs to decrypt the paymentResult response with Base64 first and then with AES / ECB / PKCS7Padding algorithm)
        # checksum(sha256(jsonString(resultObj))
        # Testing Callback Key - d655c33205363f5450427e6b6193e466

        #Decrypt the payment result
        decrypted_str=decrypt(self.secret_key,payment_result)
        try:
            result = json.loads(decrypted_str)
        except json.JSONDecodeError:
            print("Failed to parse decrypted data as JSON:")
            print(decrypted_str)
            raise

        ref = result.get('merchantOrderId')
        payment_id = result.get('transactionId')
        status = result.get('transactionStatus')

        #Notify the system to make payment status is set_done
        tx = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('dinger', {
            'ref': ref,
            'payment_id': payment_id,
            'status': status
        })

        tx._process_notification_data({
            'payment_id': payment_id,
            'status': status
        })

        #Redirect to the payment success page
        return request.redirect('/payment/status')