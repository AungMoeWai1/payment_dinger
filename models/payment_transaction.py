"""
After start creating new transaction, override my operations
"""

import logging
from datetime import datetime


import requests

from odoo import _, api, models,fields
from odoo.addons.payment_dinger import const
from odoo.exceptions import ValidationError
from odoo.http import request
from passlib.utils.handlers import parse_int
from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """
    when start make transaction , start create payload information
    send it to create url
    and to start url redirect , put it in the rendering_values
    """
    _inherit = "payment.transaction"
    provider_name=fields.Char(string="Provider Name",store=True)


    def _get_specific_rendering_values(self, transaction):
        """This method is called to render the payment page and redirect to Dinger's checkout form."""
        res = super()._get_specific_rendering_values(transaction)

        if self.provider_code != "dinger":
            return res

        # Prepare the payload for the payment request to Dinger
        # payload = self._dinger_prepare_preference_request_payload()

        # Make the request to Dinger to create the payment
        # url, encrypted_payload, hash_value = self.provider_id.dinger_make_request(
        #     resource_data=payload
        # )
        request.env['payment.transaction.status'].sudo().create({
            'transaction_id':self.id,
            'reference':"",
            'merchant_order': self.sale_order_ids[0].name if self.sale_order_ids else '',
            'provider_name': "",
            'received_method': "",
            'customer_name': self.partner_id.name,
            'total': self.sale_order_ids[0].amount_total,
            'state': "draft",
            'paid_at': datetime.now()
        })

        test_data = {
            "paymentResult": "5zDOSGSI/YE7wsmX/IlBZb6iH0NpwgRuUL13RY9sEKIvo8oebHCh1FKZ0MKTkvlKPQ6Cn2qYg7UDQssBuMbkVAGWcVPK0WvvrrACrx480jdydrNUcsqX4vsaqHuRlCQa/7Qfur+W6WNKO4exvOvN25FtE8hDB7ENu37r54wUlGC21bojhq9M15/Ql5P9+w1x/+Ep13nmyptGOHfI4a4V3D57v0HQ8KqUnOy5P6E4FYOSeOVeVuCJ516RK94OIVAUB3F9jqy4NLm9jqc243pWOR9fwGJK5YplMbOuQFEZKt0=",
            "checksum": "3e6dc224539d382f300f658a26775e75029b26ba0b885196e7ec66feb6a756ae"
        }
        sale_order = self.sale_order_ids[0]
        data = {
            "totalAmount": sale_order.amount_total,
            "createdAt": "20210916 085233",
            "transactionStatus": "SUCCESS",
            "methodName": "QR",
            "merchantOrderId": sale_order.name,
            "transactionId": self.reference,
            "customerName": self.partner_id.name,
            "providerName": "KBZ Pay"
        }

        # Set reference to transaction (important for matching)
        # self.provider_reference = payload.get("orderId")

        rendering_values = {
            "api_url": "/payment/dinger/webhook",
            "totalAmount": sale_order.amount_total,
            "transactionId": self.reference,
        }
        return rendering_values

        # rendering_values = {
        #     "api_url": url,
        #     "payload": encrypted_payload,
        #     "hashValue": hash_value,
        # }
        # return rendering_values

    def get_country_code(self, country):
        url = "https://staging.dinger.asia/payment-gateway-uat/api/countryCodeListEnquiry"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("Dinger Country Code getting success...")
            country_list = data.get("response", [])
            for entry in country_list:
                countries = entry.get("country", "").lower()
                if country.lower() in countries:
                    return entry.get("code")
        return None

    def _dinger_prepare_preference_request_payload(self):
        """Create the payload for the preference request based on the transaction values.

        :return: The request payload.
        :rtype: dict
        """
        user_lang = self.env.context.get("lang")

        sale_order = self.sale_order_ids[0]
        country_code = self.get_country_code(sale_order.partner_id.country_id.name)

        items = []
        if self.sale_order_ids:
            for line in sale_order.order_line:
                items.append(
                    {
                        "name": line.product_id.name,
                        "amount": line.price_unit,
                        "quantity": int(line.product_uom_qty),
                    }
                )
            items.append(
                {
                    "name": "Tax",
                    "amount": sale_order.amount_tax,
                    "quantity": 1,
                }
            )

        return {
            "clientId": self.partner_id.id,
            "providerName": self.payment_method_id.name,
            "totalAmount": sale_order.amount_total,
            "orderId": sale_order.name,
            "email": self.partner_id.email,
            "state": self.partner_id.state_id.name,
            "customerPhone": self.partner_id.phone,
            "customerName": self.partner_id.name,
            "postalCode": self.partner_id.zip,
            "billAddress": self.partner_id.street,
            "billCity": self.partner_id.city,
            "items": items,
            "description": self.reference,
            "locale": user_lang,
            "country": country_code,
            "currency": self.currency_id.name,
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "dinger" or len(tx) == 1:
            return tx
        provider_name = notification_data.get("provider_name")
        # notification_data={'reference': self.reference, 'payment_details': '1234', 'simulated_state':self.state}
        tx = self.search(
            [
                ("reference", "=", notification_data.get("ref")),
                ("provider_code", "=", "dinger"),
            ]
        )
        if not tx:
            raise ValidationError(
                "Dinger: "
                + _(
                    "No transaction found matching reference %s.",
                    notification_data.get("ref"),
                )
            )
        if provider_name:
            tx.write({'provider_name': provider_name})
        return tx

    @api.model
    def _dinger_get_error_msg(self, status_detail):
        """Return the error message corresponding to the payment status.

        :param str status_detail: The status details sent by the provider.
        :return: The error message.
        :rtype: str
        """
        return "Dinger: " + const.ERROR_MESSAGE_MAPPING.get(
            status_detail, const.ERROR_MESSAGE_MAPPING["cc_rejected_other_reason"]
        )

    def _process_notification_data(self, notification_data):
        """Override of payment to process the transaction based on Dinger data.

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data were received.
        """
        super()._process_notification_data(notification_data)

        if self.provider_code != "dinger":
            return

        payment_status = notification_data.get("status")
        # Update payment state based on the status
        # if payment_status == 'pending':
        #     self._set_pending()
        # elif payment_status == 'authorized':
        #     self._set_authorized()
        if payment_status == "SUCCESS":
            self._set_done()
        elif payment_status in [
            "DECLINED",
            "TIMEOUT",
            "CANCELLED",
            "SYSTEM_ERROR",
            "ERROR",
        ]:
            self._set_canceled(_("Payment status: %s", payment_status))
        else:
            _logger.error("Received invalid payment status: %s", payment_status)
            self._set_error(_("Invalid payment status: %s", payment_status))

    def _create_payment(self, **extra_create_values):
        """Create an `account.payment` record for the current transaction.

        If the transaction is linked to some invoices, their reconciliation is done automatically.

        Note: self.ensure_one()

        :param dict extra_create_values: Optional extra create values
        :return: The created payment
        :rtype: recordset of `account.payment`
        """
        self.ensure_one()

        reference = (f'{self.reference} - '
                     f'{self.partner_id.display_name or ""} - '
                     f'{self.provider_reference or ""}'
                     )

        # custom_journal = self.env["account.journal"].search(
        #     [('name', '=', 'Dinger'), ('company_id', '=', self.env.company.id)], limit=1)

        custom_transaction_journal = self.env["account.journal"].search(
            [('name', '=', self.provider_name), ('company_id', '=', self.env.company.id)], limit=1)

        available_methods = custom_transaction_journal.inbound_payment_method_line_ids if self.amount > 0 else custom_transaction_journal.outbound_payment_method_line_ids

        total_transaction_tax=(self.amount*custom_transaction_journal.commission_tax_percentage)/100+custom_transaction_journal.commission_tax_fix

        payment_values = {
            'amount': self.amount-total_transaction_tax,  # A tx may have a negative amount, but a payment must >= 0
            'payment_type': 'inbound' if self.amount > 0 else 'outbound',
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.commercial_partner_id.id,
            'partner_type': 'customer',
            # 'journal_id': self.provider_id.journal_id.id,
            'journal_id': custom_transaction_journal.id,
            'company_id': self.env.company.id,
            # 'payment_method_line_id': payment_method_line.id,
            'payment_method_line_id': available_methods[0].id,
            'payment_token_id': self.token_id.id,
            'payment_transaction_id': self.id,
            'memo': reference,
            'write_off_line_vals': [{
                'name': self.provider_name+" transaction charge",
                'account_id': custom_transaction_journal.suspense_account_id.id,
                'debit': total_transaction_tax,
                'credit': 0.0,
                'amount_currency': total_transaction_tax,
                'balance': total_transaction_tax,
                'partner_id': self.partner_id.commercial_partner_id.id,
            }
            ],
            'invoice_ids': self.invoice_ids,
            **extra_create_values,
        }

        for invoice in self.invoice_ids:
            if invoice.state != 'posted':
                continue
            next_payment_values = invoice._get_invoice_next_payment_values()
            if next_payment_values['installment_state'] == 'epd' and self.amount == next_payment_values['amount_due']:
                aml = next_payment_values['epd_line']
                epd_aml_values_list = [({
                    'aml': aml,
                    'amount_currency': -aml.amount_residual_currency,
                    'balance': -aml.balance,
                })]
                open_balance = next_payment_values['epd_discount_amount']
                early_payment_values = self.env[
                    'account.move']._get_invoice_counterpart_amls_for_early_payment_discount(epd_aml_values_list,
                                                                                             open_balance)
                for aml_values_list in early_payment_values.values():
                    if (aml_values_list):
                        aml_vl = aml_values_list[0]
                        aml_vl['partner_id'] = invoice.partner_id.id
                        payment_values['write_off_line_vals'] += [aml_vl]
                break

        payment_term_lines = self.invoice_ids.line_ids.filtered(lambda line: line.display_type == 'payment_term')
        if payment_term_lines:
            payment_values['destination_account_id'] = payment_term_lines[0].account_id.id

        payment = self.env['account.payment'].create(payment_values)
        payment.action_post()

        # Track the payment to make a one2one.
        self.payment_id = payment

        # Reconcile the payment with the source transaction's invoices in case of a partial capture.
        if self.operation == self.source_transaction_id.operation:
            invoices = self.source_transaction_id.invoice_ids
        else:
            invoices = self.invoice_ids
        if invoices:
            invoices.filtered(lambda inv: inv.state == 'draft').action_post()

            (payment.move_id.line_ids + invoices.line_ids).filtered(
                lambda line: line.account_id == payment.destination_account_id
                             and not line.reconciled
            ).reconcile()

        return payment
