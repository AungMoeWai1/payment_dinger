from odoo import models

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)

        if self.payment_method_line_id.name.lower() == 'dinger' and vals.get('amount', 0) >= 20:
            vals['amount'] = vals['amount'] - 20
            vals['payment_difference_handling'] = 'reconcile'
            vals['writeoff_label'] = 'Kpay Fee'
            kpay_account = self.env['account.account'].search([
                ('name', 'ilike', 'Kpay')
            ], limit=1)
            if not kpay_account:
                raise ValueError("Kpay account not found.")
            vals['writeoff_account_id'] = kpay_account.id

        return vals
