"""
Module to provide payment method operation
-store credentials
-compose payload url
-default method code sending to the system
-base url changing based on testing or production
"""

from odoo import fields, models
class PaymentProvider(models.Model):
    """
    Implement require credentials to use in payment
    """

    _inherit = "payment.provider"

    # === FIELDS ===#
    code = fields.Selection(
        selection_add=[("dinger", "Dinger")], ondelete={"dinger": "set default"}
    )

    # project_name = fields.Char(
    #     string="Dinger Project Name",
    #     help="Name of the project in the Dinger dashboard.",
    #     required_if_provider="dinger",
    #     groups="base.group_system",
    # )

    # public_key = fields.Char(
    #     string="Public Key",
    #     help="Wallet public key from the Dinger dashboard.",
    #     required_if_provider="dinger",
    #     groups="base.group_system",
    # )

    # merchant_name = fields.Char(
    #     string="Merchant Name",
    #     help="Wallet Merchant key from the Dinger dashboard.",
    #     required_if_provider="dinger",
    #     groups="base.group_system",
    # )

    # merchant_key = fields.Char(
    #     string="Merchant Key",
    #     help="Wallet Merchant key from the Dinger dashboard.",
    #     required_if_provider="dinger",
    #     groups="base.group_system",
    # )
    # client_id = fields.Char(
    #     string="Client Id",
    #     help="Wallet Client ID from the Dinger dashboard.",
    #     required_if_provider="dinger",
    #     groups="base.group_system",
    # )

    # secret_key = fields.Char(
    #     string="Secret Key",
    #     help="Wallet Secret key from the Dinger dashboard.",
    #     required_if_provider="dinger",
    #     groups="base.group_system",
    # )

    # description = fields.Text(
    #     string="Description",
    #     default="Payment made by an Odoo website.",
    #     required_if_provider="dinger",
    #     groups="base.group_system",
    # )

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code != "dinger":
            return default_codes
        return "dinger"
