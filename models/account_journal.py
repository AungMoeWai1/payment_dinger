from odoo import fields, models

from ..dataclasses.datamodels import JournalCodeEnum


class AccountJournal(models.Model):
    """
    Implement require credentials to use in journal
    """
    _inherit = "account.journal"

    commission_tax_percentage = fields.Float(string="Bank transaction Percentage")
    commission_tax_fix = fields.Float(string="Bank transaction Amount")
    journal_code = fields.Selection(
        selection=JournalCodeEnum.get_selection(),
        string="Bank Journal Code",
    )
