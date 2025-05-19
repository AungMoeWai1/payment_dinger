# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import json
from odoo.http import request
from odoo import _, models, api, fields
from odoo.tools import float_round
from odoo.exceptions import ValidationError
from odoo.addons.payment_dinger import const
from odoo.addons.payment_dinger.controllers.main import DingerPayController

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, transaction):
        """This method is called to render the payment page and redirect to Dinger's checkout form."""
        res = super()._get_specific_rendering_values(transaction)

        if self.provider_code != 'dinger':
            return res

        # Prepare the payload for the payment request to Dinger
        payload = self._dinger_prepare_preference_request_payload()

        # Make the request to Dinger to create the payment
        url = self.provider_id._dinger_make_request(resource_data=payload)

        # Set reference to transaction (important for matching)
        self.provider_reference = payload.get("orderId")

        rendering_values = {
            'api_url': url,
        }
        return rendering_values

    def _dinger_prepare_preference_request_payload(self):
        """ Create the payload for the preference request based on the transaction values.

        :return: The request payload.
        :rtype: dict
        """
        user_lang = self.env.context.get('lang')

        items = []
        if self.sale_order_ids:
            for line in self.sale_order_ids[0].order_line:
                items.append({
                    'name': line.product_id.name,
                    'amount': line.price_unit,
                    'quantity': line.product_uom_qty,
                })

        return {
            'clientId':self.partner_id.id,
            'providerName': self.payment_method_id.name,
            'totalAmount': self.amount,
            'orderId': self.sale_order_ids.name,
            'email': self.partner_id.email,
            'state': self.partner_id.state_id.name,
            'customerPhone': self.partner_id.phone,
            'customerName': self.partner_id.name,
            "postalCode": self.partner_id.zip,
            "billAddress": self.partner_id.street,
            "billCity": self.partner_id.city,
            "items": json.dumps(items),
            'description': self.reference,
            'locale': user_lang,
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'dinger' or len(tx) == 1:
            return tx

        import pdb;
        pdb.set_trace()
        # notification_data={'reference': self.reference, 'payment_details': '1234', 'simulated_state':self.state}
        tx = self.search(
            [('reference', '=', notification_data.get('ref')), ('provider_code', '=', 'dinger')]
        )
        if not tx:
            raise ValidationError("Dinger: " + _(
                "No transaction found matching reference %s.", notification_data.get('ref')
            ))
        return tx

    @api.model
    def _dinger_get_error_msg(self, status_detail):
        """ Return the error message corresponding to the payment status.

        :param str status_detail: The status details sent by the provider.
        :return: The error message.
        :rtype: str
        """
        return "Dinger: " + const.ERROR_MESSAGE_MAPPING.get(
            status_detail, const.ERROR_MESSAGE_MAPPING['cc_rejected_other_reason']
        )

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on Dinger data.

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data were received.
        """
        super()._process_notification_data(notification_data)

        if self.provider_code != 'dinger':
            return

        payment_status = notification_data.get('status')
        # Update payment state based on the status
        if payment_status == 'pending':
            self._set_pending()
        elif payment_status == 'authorized':
            self._set_authorized()
        elif payment_status == 'paid':
            self._set_done()
        elif payment_status in ['expired', 'canceled', 'failed']:
            self._set_canceled(_("Payment status: %s", payment_status))
        else:
            _logger.error("Received invalid payment status: %s", payment_status)
            self._set_error(_("Invalid payment status: %s", payment_status))

        # Get encrypted paymentResult and checksum from notification_data
        # encrypted_payment_result = notification_data.get('paymentResult')
        # checksum = notification_data.get('checksum')
        #
        # if not encrypted_payment_result or not checksum:
        #     raise ValidationError(_("Invalid notification data received."))
        #
        # try:
        #     # Step 1: Decrypt paymentResult using AES and Base64
        #     secret_key = 'd655c33205363f5450427e6b6193e466'  # From Dinger API documentation
        #     cipher = AES.new(secret_key.encode(), AES.MODE_ECB)
        #     decrypted = unpad(cipher.decrypt(base64.b64decode(encrypted_payment_result)), AES.block_size)
        #     decrypted_str = decrypted.decode('utf-8')
        #
        #     # Step 2: Verify the checksum
        #     calculated_checksum = hashlib.sha256(decrypted_str.encode('utf-8')).hexdigest()
        #     if calculated_checksum != checksum:
        #         raise ValidationError(_("Checksum verification failed."))
        #
        #     # Step 3: Process the decrypted payment result
        #     payment_result = json.loads(decrypted_str)
        #     self.provider_reference = payment_result.get('transactionNum')  # Transaction ID from Dinger
        #     payment_status = payment_result.get('status')
        #
        #     # Update payment state based on the status
        #     if payment_status == 'pending':
        #         self._set_pending()
        #     elif payment_status == 'authorized':
        #         self._set_authorized()
        #     elif payment_status == 'paid':
        #         self._set_done()
        #     elif payment_status in ['expired', 'canceled', 'failed']:
        #         self._set_canceled(_("Payment status: %s", payment_status))
        #     else:
        #         _logger.error("Received invalid payment status: %s", payment_status)
        #         self._set_error(_("Invalid payment status: %s", payment_status))
        #
        # except Exception as e:
        #     _logger.error("Error processing Dinger notification: %s", str(e))
        #     raise ValidationError(_("Error processing the payment notification."))

