from odoo import api, fields, models
from odoo.addons.payment_dinger import const
from dinger_payment import get_prebuild_form_url
from urllib.parse import urlencode, quote_plus

class PaymentProvider(models.Model):
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
        string="Dinger Wallet Public Key",
        help="Wallet public key from the Dinger dashboard.",
        required_if_provider="dinger",
        groups="base.group_system",
    )

    merchant_key = fields.Char(
        string="Dinger Wallet Merchant Key",
        help="Wallet Merchant key from the Dinger dashboard.",
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
    def _dinger_make_request(self, resource_data):
        data ={
            "clientId": resource_data.get("clientId"),
            "publicKey": self.public_key,
            "items": resource_data.get("items"),
            "customerName": resource_data.get("customerName"),
            "totalAmount": resource_data.get("totalAmount"),
            "merchantOrderId": resource_data.get("orderId"),
            "merchantKey": self.merchant_key,
            "projectName": self.project_name,
            "merchantName": "Wai Yan",
        }

        public_key = (
            "-----BEGIN PUBLIC KEY-----\n"
            f"{self.public_key}"
            "\n-----END PUBLIC KEY-----"
        )

        encrypted_payload, hash_value = get_prebuild_form_url(public_key=public_key, secretkey=self.merchant_key, **data)

        baseurl = self._dinger_get_api_url()
        url = f"{baseurl}?{urlencode({'payload': encrypted_payload, 'hashValue': hash_value}, quote_via=quote_plus)}"
        return url

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'dinger':
            return default_codes
        return const.DEFAULT_PAYMENT_METHOD_CODES

    def _dinger_get_api_url(self):
        """ Return the API URL according to the state.

        Note: self.ensure_one()

        :return: The API URL
        :rtype: str
        """
        self.ensure_one()
        if self.state == 'enabled':
            return 'https://form.dinger.asia'
        else:
            return 'https://prebuilt.dinger.asia'
