"""
Module to provide payment method operation
-store credentials
-compose payload url
-default method code sending to the system
-base url changing based on testing or production
"""

import json
from odoo import fields, models
from odoo.addons.payment_dinger import const
from .encryption import EncryptRSA


class PaymentProvider(models.Model):
    """
    Implement require credentials to use in payment
    """

    _inherit = "payment.provider"

    # === FIELDS ===#
    code = fields.Selection(
        selection_add=[("dinger", "Dinger")], ondelete={"dinger": "set default"}
    )

    project_name = fields.Char(
        string="Dinger Project Name",
        help="Name of the project in the Dinger dashboard.",
        required_if_provider="dinger",
        groups="base.group_system",
    )

    public_key = fields.Char(
        string="Public Key",
        help="Wallet public key from the Dinger dashboard.",
        required_if_provider="dinger",
        groups="base.group_system",
    )

    merchant_name = fields.Char(
        string="Merchant Name",
        help="Wallet Merchant key from the Dinger dashboard.",
        required_if_provider="dinger",
        groups="base.group_system",
    )

    merchant_key = fields.Char(
        string="Merchant Key",
        help="Wallet Merchant key from the Dinger dashboard.",
        required_if_provider="dinger",
        groups="base.group_system",
    )
    client_id = fields.Char(
        string="Client Id",
        help="Wallet Client ID from the Dinger dashboard.",
        required_if_provider="dinger",
        groups="base.group_system",
    )

    secret_key = fields.Char(
        string="Secret Key",
        help="Wallet Secret key from the Dinger dashboard.",
        required_if_provider="dinger",
        groups="base.group_system",
    )

    description = fields.Text(
        string="Description",
        default="Payment made by an Odoo website.",
        required_if_provider="dinger",
        groups="base.group_system",
    )

    # ===  BUSINESS METHODS   ===#

    def _prepare_dinger_payload(self, resource_data):
        """
        Prepare the payload for Dinger payment request.
        This method is used to collect data from the resource_data and format it
        according to Dinger's requirements.
        """
        return {
            "items": json.dumps(resource_data.get("items", [])),
            "customerName": resource_data.get("customerName"),
            "totalAmount": float(resource_data.get("totalAmount")),
            "merchantOrderId": resource_data.get("orderId"),
            "clientId": self.client_id,
            "publicKey": self.public_key,
            "merchantKey": self.merchant_key,
            "projectName": self.project_name or "dinger-prebuilt-smei",
            "merchantName": self.merchant_name,
            "email": resource_data.get("email"),
            "billCity": resource_data.get("billCity", "city"),
            "billAddress": resource_data.get("billAddress", "address"),
            "state": resource_data.get("state", "state"),
            "country": resource_data.get("country", "MM"),
            "currency":resource_data.get("currency"),
            "postalCode": resource_data.get("postalCode", "15015"),
        }

    def _get_dinger_payload(self, resource_data):
        """
        Get the payload for Dinger payment request.
        This method is used to collect data from the resource_data and format it
        according to Dinger's requirements.
        """
        return self._prepare_dinger_payload(resource_data)

    # To request for payment by send payload
    def dinger_make_request(self, resource_data):
        """
        Collect data
        encrypt with rsa using public key
        change it to base64 to get payload
        hash value is get from hmac sha256 by encrypting using secret key and data
        return url to browse
        """
        self.ensure_one()
        if not self.public_key or not self.merchant_key or not self.project_name:
            raise ValueError("Public Key, Merchant Key, and Project Name are required.")
        if not self.secret_key:
            raise ValueError("Secret Key is required for encryption.")
        # Prepare the payload data
        if not resource_data:
            raise ValueError("Resource data is required to create the payment request.")
        if not isinstance(resource_data, dict):
            raise ValueError("Resource data must be a dictionary.")
        return EncryptRSA.pay(
            baseurl=self.dinger_get_api_url(),
            data=self._get_dinger_payload(resource_data),
            secretkey=self.secret_key,
        )

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code != "dinger":
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES

    def dinger_get_api_url(self):
        """Return the API URL according to the state.

        Note: self.ensure_one()

        :return: The API URL
        :rtype: str
        """
        self.ensure_one()
        return (
            "https://form.dinger.asia"
            if self.state == "enabled"
            else "https://prebuilt.dinger.asia"
        )
