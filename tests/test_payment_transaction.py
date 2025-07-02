from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from ...dinger_mixin.dataclasses.datamodels import TransactionStatusEnum
from unittest.mock import patch
import json


class TestPaymentTransaction(TransactionCase):

    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        super(TestPaymentTransaction, cls).setUpClass()

        dinger_provider = cls.env["payment.provider"].create({
            "name": "Dinger Provider",
            "code": "dinger",
        })

        # Find or create a payment method
        payment_method = cls.env["payment.method"].create({
            "name": "Test Dinger Method",
            "code": "dinger",
        })

        # Setup sample transaction and other data
        cls.payment_tx = cls.env["payment.transaction"].create({
            "amount": 100,
            "provider_id": dinger_provider.id,
            "payment_method_id": payment_method.id,
            "currency_id": cls.env.ref("base.USD").id,
            "partner_id": cls.env.ref("base.res_partner_1").id,
        })

    def test_get_transaction_status_values(self):
        """Test _get_transaction_status_values returns correctly formatted dict"""
        result = self.payment_tx._get_transaction_status_values()
        self.assertIn("transaction_id", result)
        self.assertEqual(result["transaction_id"], self.payment_tx.id)

    def test_create_payment_transaction_status(self):
        """Test create_payment_transaction_status creates a record"""
        result = self.payment_tx.create_payment_transaction_status()
        self.assertEqual(result.transaction_id.id, self.payment_tx.id)
        self.assertEqual(result.customer_name, self.payment_tx.partner_id.name)

    def test_prepare_dinger_data_with_test_enable(self):
        # Setup product and sale order first (common for both cases)
        self.test_product = self.env["product.product"].create({
            "name": "Test Product",
            "list_price": 100.0,
            "type": "consu",
        })
        sale_order = self.env["sale.order"].create({
            "partner_id": self.payment_tx.partner_id.id,
            "order_line": [
                (0, 0, {
                    "product_id": self.test_product.id,
                    "name": "Test Product",
                    "product_uom_qty": 1,
                    "price_unit": 100,
                })
            ]
        })
        self.payment_tx.sale_order_ids = [(4, sale_order.id)]

        # Case 1: test_enable = False -> normal behavior
        with patch("odoo.addons.dinger_mixin.models.dinger_mixin.config") as mock_config:
            mock_config.__getitem__.side_effect = lambda key: False if key == "test_enable" else None

            result = self.payment_tx._prepare_dinger_data()
            self.assertIn("items", result)
            self.assertEqual(result["customerName"], self.payment_tx.partner_id.name)
            items = json.loads(result["items"])
            self.assertEqual(len(items), 2, "Expected 2 items in the payload.")
            self.assertEqual(items[0]["name"], "Test Product", "Product name should match.")



    # def test_prepare_dinger_data(self):
    #     """Test _prepare_dinger_data returns correctly formatted payload"""
    #     self.test_product = self.env["product.product"].create({
    #         "name": "Test Product",
    #         "list_price": 100.0,
    #         "type": "consu",  # or "service" or "product"
    #     })
    #     sale_order = self.env["sale.order"].create({
    #         "partner_id": self.payment_tx.partner_id.id,
    #         "order_line": [
    #             (0, 0, {
    #                 "product_id": self.test_product.id,
    #                 "name": "Test Product",
    #                 "product_uom_qty": 1,
    #                 "price_unit": 100,
    #             })
    #         ]
    #     })
    #     self.payment_tx.sale_order_ids = [(4, sale_order.id)]  # Link sale order
    #
    #     # Test
    #     result = self.payment_tx._prepare_dinger_data()
    #     self.assertIn("items", result)  # Now result is a dict
    #     self.assertEqual(result["customerName"], self.payment_tx.partner_id.name)
    #     items = json.loads(result["items"])
    #     self.assertEqual(len(items), 2, "Expected 2 item in the payload.") # This is in the item contain tax line , so two item
    #     self.assertEqual(items[0]["name"], "Test Product", "Product name should match.")

    def test_get_specific_rendering_values(self):
        # ... your setup code

        dinger_provider = self.env["payment.provider"].create({
            "name": "Dinger Provider",
            "code": "dinger",
        })

        # Find or create a payment method
        payment_method = self.env["payment.method"].create({
            "name": "Test Dinger Method",
            "code": "dinger",
        })

        # Setup sample transaction and other data
        self.payment_tx = self.env["payment.transaction"].create({
            "amount": 100,
            "provider_id": dinger_provider.id,
            "payment_method_id": payment_method.id,
            "currency_id": self.env.ref("base.USD").id,
            "partner_id": self.env.ref("base.res_partner_1").id,
        })

        with patch.object(type(self.payment_tx), "dinger_make_request", return_value=("url", "payload", "hash")), \
                patch.object(type(self.payment_tx), "_prepare_dinger_data", return_value={"dummy": "data"}):
            result_dinger = self.payment_tx._get_specific_rendering_values(self.payment_tx)

            self.assertEqual(result_dinger["api_url"], "url")
            self.assertEqual(result_dinger["payload"], "payload")

    #
    # def test_get_tx_from_notification_data(self):
    #     """Test _get_tx_from_notification_data returns transaction"""
    #     tx = self.payment_tx._get_tx_from_notification_data("dinger", {
    #         "ref": self.payment_tx.reference,
    #         "payment_details": "123",
    #         "simulated_state": self.payment_tx.state,
    #         "provider": "dinger"
    #     })
    #     self.assertEqual(tx.id, self.payment_tx.id)
    #
    # def test_dinger_error_handler(self):
    #     """Test _dinger_error_handler sets error status"""
    #     status_detail = "Error occurred."
    #     self.payment_tx._dinger_error_handler({"status_detail": status_detail})
    #     self.assertEqual(self.payment_tx.state, "error")
    #     self.assertIn(status_detail, self.payment_tx.last_error_message)
    #
    # def test_get_dinger_status_handler(self):
    #     """Test _get_dinger_status_handler returns the right handler method"""
    #     handler = self.payment_tx._get_dinger_status_handler("success")
    #     self.assertEqual(handler, self.payment_tx._set_done)
    #
    # def test_process_notification_data(self):
    #     """Test _process_notification_data processes correctly"""
    #     self.payment_tx._process_notification_data({
    #         "provider": "dinger",
    #         "status": TransactionStatusEnum.SUCCESS.x_name(),
    #     })
    #     self.assertEqual(self.payment_tx.state, "success")
    #
    # def test_prepare_dinger_values(self):
    #     """Test _prepare_dinger_values returns correct dict"""
    #     journal = self.env["account.journal"].search([], limit=1)
    #     self.payment_tx.provider_name = journal.journal_code
    #     result = self.payment_tx._prepare_dinger_values()
    #     self.assertEqual(result["journal_id"], journal.id)
    #
    # from your_module.dataclasses.datamodels import JournalCodeEnum
    #
    # def test_create_payment_for_dinger(self):
    #     """Test _create_payment creates account.payment correctly for Dinger"""
    #     journal = self.env["account.journal"].search([], limit=1)
    #     # Use the actual value from JournalCodeEnum
    #     self.payment_tx.provider_name = JournalCodeEnum.DINGER
    #     result = self.payment_tx._create_payment()
    #     self.assertEqual(
    #         result.payment_method_line_id.payment_method_id.code,
    #         journal.outbound_payment_method_line_ids[0].payment_method_id.code,
    #     )
    #
    # def test_process_dinger_webhook(self):
    #     """Test process_dinger_webhook creates and processes transaction status"""
    #     data = {
    #         "merchant_order": "ORDER123",
    #         "payment_id": "PAYMENT123",
    #         "status": "success",
    #         "provider_name": "dinger",
    #     }
    #     result = self.payment_tx.process_dinger_webhook(data)
    #
    #     status = self.env["payment.transaction.status"].sudo().search([("merchant_order", "=", "ORDER123")])
    #     self.assertEqual(status.merchant_order, "ORDER123")
    #     self.assertEqual(result.id, self.payment_tx.id)
