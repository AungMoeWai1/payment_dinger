"""
Module to provide payment method operation
-store credentials
-compose payload url
-default method code sending to the system
-base url changing based on testing or production
"""
import json
from urllib.parse import urlencode, quote_plus
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

    # To request for payment by send payload
    def dinger_make_request(self, resource_data):
        """
        Collect data
        encrypt with rsa using public key
        change it to base64 to get payload
        hash value is get from hmac sha256 by encrypting using secret key and data
        return url to browse
        """

        # items_list = resource_data.get("items", [])
        # data = {
        #     # items must be string
        #     "items": json.dumps(items_list),
        #     "customerName": resource_data.get("customerName"),
        #     "totalAmount": resource_data.get("totalAmount"),
        #     "merchantOrderId": resource_data.get("orderId"),
        #     # get from checkout-form page
        #     "clientId": self.client_id,
        #     # get from data-dashboard page
        #     "publicKey": self.public_key,
        #     # get from data-dashboard page
        #     "merchantKey": self.merchant_key,
        #     # your project name
        #     "projectName": self.project_name,
        #     # your account username
        #     "merchantName": self.merchant_name,
        #     "email": "misterjames.thiha@gmail.com",
        #     "billCity": "city",
        #     "billAddress": "address",
        #     "state": "state",
        #     "country": "MM",
        #     "postalCode": "15015",
        # }

        items = [
            {"name": "DiorAct Sandal", "amount": 250, "quantity": 1},
            {"name": "Aime Leon Dore", "amount": 250, "quantity": 1},
        ]
        orderid = "123456"
        data = {
            # items must be string
            "items": json.dumps(items),
            "customerName": "James",
            "totalAmount": 500,
            "merchantOrderId": orderid,
            # get from checkout-form page
            "clientId": "6ecf9792-f093-369e-bb25-ec5c2702c5f4",
            # get from data-dashboard page
            "publicKey": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCucqVPf8TB71ZAHRxcJE9Ac2AknmLwJmoqZ5FxB7+vfe6Gsg7dFfegMCrl29P3vLp58rpzLl436RHr8/RSymsiJWI8ARpc26oPWAXgmx6P7LtdyYw7R8GrHhq8o8jTGnNA0oHbptlbLIxSlLHmLXUlSUj7T+PlQd4HQ3E4jANPBQIDAQAB",
            # get from data-dashboard page
            "merchantKey": "mhgsnvm.89_wMpuTVA9yecHyUr4aMibvbIU",
            # your project name
            "projectName": "prebuilt-test-2",
            # your account username
            "merchantName": "Jamesssy",
            "email": "misterjames.thiha@gmail.com",
            "billCity": "city",
            "billAddress": "address",
            "state": "state",
            "country": "MM",
            "postalCode": "15015",
        }
        # value = json.dumps(data)
        # get from checkout-form page
        secretkey = "1be2e692d3a1d80b8e9e3e665028b6f7"

        baseurl = self.dinger_get_api_url()
        url,encrypted_payload,hash_value=EncryptRSA.pay(baseurl,data,secretkey)
        print(url)
        return url,encrypted_payload,hash_value

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
        staging="https://form.dinger.asia"
        production="https://prebuilt.dinger.asia"
        return staging if self.state == "enabled" else production
