from odoo import fields,models

class paymentTransactionStatus(models.Model):
    _name='payment.transaction.status'
    _description="To store the status information from the dinger payment call back"

    name=fields.Char(string="Transaction Id")
    merchant_order_id=fields.Char(string="Merchant Order Id")
    provider_name=fields.Char(string="Provider Name")
    method_name=fields.Char(string="Method Name")
    customer_name=fields.Char(string="Customer Name")
    total_amount=fields.Monetary(string="Total Amount")
    status=fields.Char(string="Status")
    paid_at=fields.Time(string="Paid At")

