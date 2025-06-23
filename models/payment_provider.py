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

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code != "dinger":
            return default_codes
        return "dinger"
