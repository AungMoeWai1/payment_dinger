from email.policy import default

from odoo import fields,models

PAYMENT_TRANSACTION_STATUS=[
    ("draft","DRAFT"),
    ("success","SUCCESS"),
    ("declined","DECLINED"),
    ("timeout","TIMEOUT"),
    ("cancelled","CANCELLED"),
    ("system_error","SYSTEM_ERROR"),
    ("error","ERROR")
]
class paymentTransactionStatus(models.Model):
    _name='payment.transaction.status'
    _description="To store the status information from the dinger payment call back"

    #Need to add payment.transaction with many2one
    transaction_id=fields.Many2one("payment.transaction",string="Payment ID")
    reference=fields.Char(string="Transaction ID")
    merchant_order=fields.Char(string="Merchant OrderID")
    provider_name=fields.Char(string="Provider Name")
    received_method=fields.Char(string="Received By")
    customer_name=fields.Char(string="Customer")
    #Here need to change float to monetary : fact- return value are float amount
    total=fields.Float(string="Total")
    state=fields.Selection(PAYMENT_TRANSACTION_STATUS,string="Status",default="draft")
    paid_at=fields.Datetime(string="Paid At")

