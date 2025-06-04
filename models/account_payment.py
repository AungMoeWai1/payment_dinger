from odoo import models, api, _
from odoo.exceptions import UserError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # is_dinger = self._context.get('from_dinger_payment', False)
            original_amount = vals.get('amount', 0.0)

            if original_amount >= 20:
                actual_amount = original_amount - 20
                vals['amount'] = actual_amount

                # Set the writeoff account directly on the payment
                kpay_account = self.env['account.account'].search([
                    ('name', 'ilike', 'Kpay'),  # Adjust as needed
                ], limit=1)
                if not kpay_account:
                    raise UserError("Kpay journal account not found.")

        return super().create(vals_list)
