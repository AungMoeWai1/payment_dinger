
from odoo import fields, models


class AccountJournal(models.Model):
    """
    Implement require credentials to use in journal
    """
    _inherit="account.journal"

    commission_tax_percentage=fields.Float(default=0.0,string="Bank transaction Percentage")
    commission_tax_fix=fields.Float(default=0.0,string="Bank transaction Amount")