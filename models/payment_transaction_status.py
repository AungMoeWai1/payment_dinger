from odoo import fields,models

PAYMENT_TRANSACTION_STATUS=[
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

    name=fields.Char(string="Transaction Id")
    merchant_order_id=fields.Char(string="Merchant Order Id")
    provider_name=fields.Char(string="Provider Name")
    method_name=fields.Char(string="Method Name")
    customer_name=fields.Char(string="Customer Name")
    #Here need to change float to monetary : fact- return value are float amount
    total_amount=fields.Float(string="Total Amount")
    status=fields.Selection(PAYMENT_TRANSACTION_STATUS,string="Status")
    paid_at=fields.Datetime(string="Paid At")

