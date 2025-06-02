"""
After start creating new transaction, override my operations
"""

import logging
import requests

from odoo import _, api, models
from odoo.addons.payment_dinger import const
from odoo.exceptions import ValidationError
from odoo.http import request
from passlib.utils.handlers import parse_int
from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """
    when start make transaction , start create payload information
    send it to create url
    and to start url redirect , put it in the rendering_values
    """
    _inherit = "payment.transaction"

    def _get_specific_rendering_values(self, transaction):
        """This method is called to render the payment page and redirect to Dinger's checkout form."""
        res = super()._get_specific_rendering_values(transaction)

        if self.provider_code != "dinger":
            return res

        # Prepare the payload for the payment request to Dinger
        payload = self._dinger_prepare_preference_request_payload()

        # Make the request to Dinger to create the payment
        url, encrypted_payload, hash_value = self.provider_id.dinger_make_request(
            resource_data=payload
        )

        # Set reference to transaction (important for matching)
        # self.provider_reference = payload.get("orderId")

        rendering_values = {
            "api_url": url,
            "payload": encrypted_payload,
            "hashValue": hash_value,
        }
        return rendering_values

    def get_country_code(self,country):
        url="https://staging.dinger.asia/payment-gateway-uat/api/countryCodeListEnquiry"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("Dinger Country Code getting success...")
            country_list=data.get("response",[])
            for entry in country_list:
                countries = entry.get("country", "").lower()
                if  country.lower() in countries:
                    return entry.get("code")
        return None

    def _dinger_prepare_preference_request_payload(self):
        """Create the payload for the preference request based on the transaction values.

        :return: The request payload.
        :rtype: dict
        """
        user_lang = self.env.context.get("lang")

        #This should be defined 2% for all payment method to make average fix
        tax_percentage=self.provider_id.commission_tax
        # tax_percentage=2

        sale_order=self.sale_order_ids[0]
        commission_tax = (sale_order.amount_total * 2) / 100
        country_code = self.get_country_code(sale_order.partner_id.country_id.name)

        items = []
        if self.sale_order_ids:
            for line in sale_order.order_line:
                items.append(
                    {
                        "name": line.product_id.name,
                        "amount": line.price_unit,
                        "quantity": int(line.product_uom_qty),
                    }
                )
            items.append(
                {
                    "name": "Tax",
                    "amount":sale_order.amount_tax,
                    "quantity":1,
                }
            )
            items.append(
                {
                    "name": "Commission Tax",
                    "amount":commission_tax,
                    "quantity":1,
                }
            )

        return {
            "clientId": self.partner_id.id,
            "providerName": self.payment_method_id.name,
            "totalAmount": sale_order.amount_total+commission_tax,
            "orderId": sale_order.name,
            "email": self.partner_id.email,
            "state": self.partner_id.state_id.name,
            "customerPhone": self.partner_id.phone,
            "customerName": self.partner_id.name,
            "postalCode": self.partner_id.zip,
            "billAddress": self.partner_id.street,
            "billCity": self.partner_id.city,
            "items": items,
            "description": self.reference,
            "locale": user_lang,
            "country":country_code,
            "currency":self.currency_id.name,
        }


    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "dinger" or len(tx) == 1:
            return tx

        # notification_data={'reference': self.reference, 'payment_details': '1234', 'simulated_state':self.state}
        tx = self.search(
            [
                ("reference", "=", notification_data.get("ref")),
                ("provider_code", "=", "dinger"),
            ]
        )
        if not tx:
            raise ValidationError(
                "Dinger: "
                + _(
                    "No transaction found matching reference %s.",
                    notification_data.get("ref"),
                )
            )
        return tx

    @api.model
    def _dinger_get_error_msg(self, status_detail):
        """Return the error message corresponding to the payment status.

        :param str status_detail: The status details sent by the provider.
        :return: The error message.
        :rtype: str
        """
        return "Dinger: " + const.ERROR_MESSAGE_MAPPING.get(
            status_detail, const.ERROR_MESSAGE_MAPPING["cc_rejected_other_reason"]
        )

    def _process_notification_data(self, notification_data):
        """Override of payment to process the transaction based on Dinger data.

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data were received.
        """
        super()._process_notification_data(notification_data)

        if self.provider_code != "dinger":
            return

        payment_status = notification_data.get("status")
        # Update payment state based on the status
        # if payment_status == 'pending':
        #     self._set_pending()
        # elif payment_status == 'authorized':
        #     self._set_authorized()
        if payment_status == "SUCCESS":
            self._set_done()
        elif payment_status in [
            "DECLINED",
            "TIMEOUT",
            "CANCELLED",
            "SYSTEM_ERROR",
            "ERROR",
        ]:
            self._set_canceled(_("Payment status: %s", payment_status))
        else:
            _logger.error("Received invalid payment status: %s", payment_status)
            self._set_error(_("Invalid payment status: %s", payment_status))
