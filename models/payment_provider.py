import json
import urllib.parse
from odoo import api, fields, models
from odoo.addons.payment_dinger import const
from dinger_payment import get_prebuild_form_url, decrypt_aes_ecb
from urllib.parse import urlencode, quote_plus
# from .encryption import rsa_encrypt_chunked, generate_hash_value, decrypt
# from Crypto.PublicKey import RSA
# from .encryption_rsa import encrypt, generate_hash_value


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
    def _dinger_make_request(self, resource_data):

        items_list = resource_data.get("items", [])

        items = json.dumps(items_list)

        data = {
            "clientId": self.client_id,
            "publicKey": self.public_key,
            "items": items,
            "customerName": resource_data.get("customerName"),
            "totalAmount": str(resource_data.get("totalAmount")),
            "merchantOrderId": resource_data.get("orderId"),
            "merchantKey": self.merchant_key,
            "projectName": self.project_name,
            "merchantName": "WaiYanKyaw",
        }

        encryption_key = ("-----BEGIN PUBLIC KEY-----\n"
                          + "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCFD4IL1suUt/TsJu6zScnvsEdLPuACgBdjX82QQf8NQlFHu2v/84dztaJEyljv3TGPuEgUftpC9OEOuEG29z7z1uOw7c9T/luRhgRrkH7AwOj4U1+eK3T1R+8LVYATtPCkqAAiomkTU+aC5Y2vfMInZMgjX0DdKMctUur8tQtvkwIDAQAB"
                          + "\n-----END PUBLIC KEY-----")

        encrypted_payload, hash_value = get_prebuild_form_url(public_key=encryption_key, secretkey=self.secret_key,**data)

        baseurl = self._dinger_get_api_url()
        url=f"{baseurl}?{urlencode({'payload':encrypted_payload,'hashValue':hash_value}, quote_via=quote_plus)}"

        # url = f"{baseurl}?{urlencode({'payload': encrypted_payload,'hashValue':hash_value}, quote_via=quote_plus)}"
        print(url)

        import pdb;pdb.set_trace()

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
