from odoo import models,fields

class account_journal(models.Model):
    _inherit = "account.journal"

    commission_tax_percentage=fields.Float(string="Tax of bank transaction percentage",default=0.0)
    commission_tax_fix=fields.Float(string="Tax of bank transaction amount",default=0.0)
