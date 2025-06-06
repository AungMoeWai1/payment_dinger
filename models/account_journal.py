from odoo import fields, models, api

PAYMENT_JOURNAL_MAPPING_CODE_SELECTION = [
    ('aya_pay', 'AYA Pay'),
    ('cb_pay', 'CB pay'),
    ('citizens_pay', 'Citizens Pay'),
    ('jcb', 'JCB'),
    ('kbz_mobile_banking', 'KBZ Mobile Banking'),
    ('k_pay', 'KBZ Pay'),
    ('mab_mobile_banking', ' MAB Mobile Banking'),
    ('master', 'Master'),
    ('m_pite_san', ' M-Pite san'),
    ('mpt_pay', 'MPT Pay'),
    ('mpu', 'MPU'),
    ('mytel_pay', 'Mytel Pay'),
    ('ok_dollar', 'OK Dollar'),
    ('onepay', ' One Pay'),
    ('sai_sai_pay', 'Sai Sai Pay'),
    ('true_money', 'True Money'),
    ('uab_pay', 'UAB Pay'),
    ('visa', 'Visa'),
    ('wave_pay', 'Wave Pay'),
]


class AccountJournal(models.Model):
    """
    Implement require credentials to use in journal
    """
    _inherit = "account.journal"

    commission_tax_percentage = fields.Float(default=0.0, string="Bank transaction Percentage")
    commission_tax_fix = fields.Float(default=0.0, string="Bank transaction Amount")
    journal_code = fields.Selection(
        selection=PAYMENT_JOURNAL_MAPPING_CODE_SELECTION,
        string="Bank Journal Code",
    )
