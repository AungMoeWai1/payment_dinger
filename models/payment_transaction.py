"""
After start creating new transaction, override my operations
"""

import logging

import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..dataclasses.datamodels import (JournalCodeEnum,
                                      TransactionStatusEnum,
                                      TransactionEnum)

_logger = logging.getLogger(__name__)

TRANSACTION_STATUS = 'payment.transaction.status'

class PaymentTransaction(models.Model):
    """
    when start make transaction , start create payload information
    send it to create url
    and to start url redirect , put it in the rendering_values
    """

    _inherit = "payment.transaction"
    provider_name = fields.Selection(
        selection=JournalCodeEnum.get_selection(), string="Provider Name"
    )

    def _get_transaction_status_values(self):
        """Return the values dict for payment.transaction.status for the current transaction."""
        self.ensure_one()
        sale_order = self.sale_order_ids[0] if self.sale_order_ids else None
        return {
            "transaction_id": self.id,
            "merchant_order": sale_order.name if sale_order else "",
            "customer_name": self.partner_id.name,
            "total": sale_order.amount_total if sale_order else 0.0,
        }

    def create_payment_transaction_status(self, values=None):
        """Create a payment.transaction.status record for the current transaction.

        :param dict values: Optional values to use for creation. If not provided, use default.
        :return: The created record.
        """
        if not values:
            values = self._get_transaction_status_values()
        return self.env[TRANSACTION_STATUS].sudo().create(values)

    def _prepare_dinger_data(self):
        """Create the payload for the preference request based on the transaction values."""
        self.ensure_one()
        user_lang = self.env.context.get("lang")
        if self.sale_order_ids:
            sale_order = self.sale_order_ids[0]
            country_code = self.get_country_code(sale_order.partner_id.country_id.name)

            items = [
                {
                    "name": line.product_id.name,
                    "amount": line.price_unit,
                    "quantity": int(line.product_uom_qty),
                }
                for line in sale_order.order_line
            ]
            if sale_order.amount_tax:
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
        return None

    def _get_specific_rendering_values(self, transaction):
        """This method is called to render the payment page and redirect to Dinger's checkout form."""
        res = super()._get_specific_rendering_values(transaction)

        if self.provider_code != TransactionEnum.DINGER.value:
            return res

        # Make the request to Dinger to create the payment
        url, encrypted_payload, hash_value = self.provider_id.dinger_make_request(
            resource_data=self._prepare_dinger_data()
        )

        # Create payment.transaction.status record
        self.create_payment_transaction_status()

        # Prepare the rendering values to be used in the payment page
        rendering_values = {
            "api_url": url,
            "payload": encrypted_payload,
            "hashValue": hash_value
        }
        return rendering_values

    def get_country_code(self, country):
        """Get the country code for a given country name.
        This method fetches the country code from Dinger's API based on the provided country name.
        It returns the country code if found, otherwise returns None.
        :param country: The name of the country for which to get the code.
        :type country: str
        :return: The country code if found, otherwise None.
        :rtype: str or None
        """
        url = (
            "https://staging.dinger.asia/payment-gateway-uat/api/countryCodeListEnquiry"
        )
        response = requests.get(url, timeout=120)
        if response.ok:
            data = response.json()
            print("Dinger Country Code getting success...")
            country_list = data.get("response", [])
            for entry in country_list:
                countries = entry.get("country", "").lower()
                if country.lower() in countries:
                    return entry.get("code")
        return None

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != TransactionEnum.DINGER.value or len(tx) == 1:
            return tx
        provider_name = notification_data.get(TransactionEnum.PROVIDER.value)
        # notification_data={'reference': self.reference, 'payment_details': '1234', 'simulated_state':self.state}
        tx = self.search(
            [
                ("reference", "=ilike", notification_data.get("ref")),
                ("provider_code", "=", provider_code),
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
        if tx and provider_name:
            tx.write({TransactionEnum.PROVIDER.value: provider_name})
        return tx

    @api.model
    def _dinger_get_error_msg(self, status_detail) -> str:
        """Return the error message corresponding to the payment status.

        :param str status_detail: The status details sent by the provider.
        :return: The error message.
        :rtype: str
        """
        return "Dinger: " + status_detail

    def _dinger_error_handler(self, notification_data):
        self._set_error(
            self._dinger_get_error_msg(
                notification_data.get("status_detail", _("Payment failed"))
            )
        )

    def _dinger_cancel_handler(self, notification_data):
        self._set_canceled(
            self._dinger_get_error_msg(
                notification_data.get("status_detail", _("Payment failed"))
            )
        )

    def _get_dinger_status_handler(self, payment_status):
        """Return the handler method for a given Dinger payment status."""
        # You can also make this a @staticmethod or @classmethod if you don't need self
        mapping = {
            TransactionStatusEnum.SUCCESS.x_name(): self._set_done,
            TransactionStatusEnum.SYSTEM_ERROR.x_name(): self._dinger_error_handler,
            TransactionStatusEnum.ERROR.x_name(): self._dinger_error_handler,
            TransactionStatusEnum.DECLINED.x_name(): self._dinger_error_handler,
            TransactionStatusEnum.TIMEOUT.x_name(): self._dinger_cancel_handler,
            TransactionStatusEnum.CANCELLED.x_name(): self._dinger_cancel_handler,
        }
        return mapping.get(payment_status)

    def _process_notification_data(self, notification_data):
        """Override of payment to process the transaction based on Dinger data."""
        super()._process_notification_data(notification_data)

        if notification_data.get(TransactionEnum.PROVIDER.value) != TransactionEnum.DINGER.value:
            return

        payment_status = notification_data.get("status")
        handler = self._get_dinger_status_handler(payment_status)

        if handler:
            # For _set_done, no args; for error/cancel, pass notification_data
            if handler in (self._set_done,):
                handler()
            else:
                handler(notification_data)
        else:
            _logger.error("Dinger: Received invalid payment status: %s", payment_status)
            self._set_error(
                self._dinger_get_error_msg(
                    _("Invalid payment status: %s", payment_status)
                )
            )

    def _prepare_dinger_values(self) -> dict:
        """Prepare the payload for Dinger payment request."""
        self.ensure_one()
        journal = self.env["account.journal"].search(
            [
                (
                    "journal_code",
                    "=",
                    self.provider_name,
                ),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        if not journal:
            raise ValidationError(
                _(
                    "No journal found for provider %s. Please configure the journal in the system.",
                    self.provider_name,
                )
            )

        total_transaction_tax = (
            self.amount * journal.commission_tax_percentage
        ) / 100 + journal.commission_tax_fix

        # Refactored payment_method_line_id assignment
        payment_method_lines = journal.outbound_payment_method_line_ids
        if self.amount > 0:
            payment_method_lines = journal.inbound_payment_method_line_ids
        payment_method_line_id = (
            payment_method_lines[0].id if payment_method_lines else False
        )

        dinger_values = {
            "amount": self.amount - total_transaction_tax,
            "journal_id": journal.id,
            "payment_method_line_id": payment_method_line_id,
            "write_off_line_vals": [
                {
                    "name": self.provider_name + " transaction charge",
                    "account_id": journal.suspense_account_id.id,
                    "debit": total_transaction_tax,
                    "credit": 0.0,
                    "amount_currency": total_transaction_tax,
                    "balance": total_transaction_tax,
                    "partner_id": self.partner_id.commercial_partner_id.id,
                }
            ],
        }

        # Add destination_account_id if payment term lines exist
        payment_term_lines = self.invoice_ids.line_ids.filtered(
            lambda line: line.display_type == "payment_term"
        )
        if payment_term_lines:
            dinger_values["destination_account_id"] = payment_term_lines[
                0
            ].account_id.id

        return dinger_values

    def _create_payment(self, **extra_create_values):
        """Create an `account.payment` record for the current transaction.

        If the transaction is linked to some invoices, their reconciliation is done automatically.

        Note: self.ensure_one()

        :param dict extra_create_values: Optional extra create values
        :return: The created payment
        :rtype: recordset of `account.payment`
        """
        self.ensure_one()
        if self.provider_id.code != TransactionEnum.DINGER.value:
            # For non-Dinger providers, use the standard logic and pass through extra values.
            return super()._create_payment(**extra_create_values)

        # Merge Dinger-specific values with any extra values passed in
        extra_create_values.update(self._prepare_dinger_values())

        # Call the parent with all values
        return super()._create_payment(**extra_create_values)

    def process_dinger_webhook(self, webhook_data: dict):
        """
        Process Dinger webhook data: update/create payment.transaction.status and process payment transaction.
        :param webhook_data: dict with keys: ref, payment_id, status, provider_name, method_name, customer_name, total_amount
        """
        # Update or create payment.transaction.status
        status_env = self.env[TRANSACTION_STATUS].sudo()
        transaction_status = status_env.search(
            [("merchant_order", "=ilike", webhook_data["merchant_order"])], limit=1
        )
        if not transaction_status:
            self.create_payment_transaction_status(
                values=dict(
                    webhook_data,
                    merchant_order=webhook_data.get("merchant_order"),
                    transaction_id=webhook_data.get("transaction_id"),
                )
            )
        elif transaction_status:
            # Remove merchant_order to avoid duplication
            update_data =webhook_data.copy()
            update_data.pop("merchant_order")
            transaction_status.sudo().write(update_data)

        # Process payment transaction
        tx = self.sudo()._get_tx_from_notification_data(
            TransactionEnum.DINGER.value,
            {
                "ref": transaction_status.transaction_id.reference,
                "payment_id": webhook_data.get("merchant_order"),
                "status": webhook_data.get("state"),
                TransactionEnum.PROVIDER.value: webhook_data.get(TransactionEnum.PROVIDER.value),
            },
        )
        tx._process_notification_data(
            {
                "transaction_id": transaction_status.transaction_id,
                TransactionEnum.PROVIDER.value: TransactionEnum.DINGER.value,
                "payment_id": webhook_data.get("merchant_order"),
                "status": webhook_data.get("state"),
            }
        )
        return tx
