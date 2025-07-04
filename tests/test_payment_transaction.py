#pylint: disable=invalid-name
import json
from unittest.mock import patch
from odoo.tests.common import TransactionCase


class TestPaymentTransaction(TransactionCase):
    """Test cases for payment transaction with Dinger provider."""

    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        super(TestPaymentTransaction, cls).setUpClass()

        dinger_provider = cls.env["payment.provider"].create(
            {
                "name": "Dinger Provider",
                "code": "dinger",
            }
        )

        # Find or create a payment method
        payment_method = cls.env["payment.method"].create(
            {
                "name": "Test Dinger Method",
                "code": "dinger",
            }
        )

        # Setup sample transaction and other data
        cls.payment_tx = cls.env["payment.transaction"].create(
            {
                "amount": 100,
                "provider_id": dinger_provider.id,
                "payment_method_id": payment_method.id,
                "currency_id": cls.env.ref("base.USD").id,
                "partner_id": cls.env.ref("base.res_partner_1").id,
            }
        )

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
        """Test _prepare_dinger_data with test_enable configuration."""
        testing_product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "list_price": 100.0,
                "type": "consu",
            }
        )
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.payment_tx.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": testing_product.id,
                            "name": "Test Product",
                            "product_uom_qty": 1,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )
        self.payment_tx.sale_order_ids = [(4, sale_order.id)]

        # Case 1: test_enable = False -> normal behavior
        with patch(
            "odoo.addons.dinger_mixin.models.dinger_mixin.config"
        ) as mock_config:
            mock_config.__getitem__.side_effect = lambda key: (
                False if key == "test_enable" else None
            )

            result = self.payment_tx._prepare_dinger_data()
            self.assertIn("items", result)
            self.assertEqual(result["customerName"], self.payment_tx.partner_id.name)
            items = json.loads(result["items"])
            self.assertEqual(len(items), 2, "Expected 2 items in the payload.")
            self.assertEqual(
                items[0]["name"], "Test Product", "Product name should match."
            )

    def test_get_specific_rendering_values(self):
        """Test _get_specific_rendering_values for Dinger provider."""
        # ... your setup code

        dinger_provider = self.env["payment.provider"].create(
            {
                "name": "Dinger Provider",
                "code": "dinger",
            }
        )

        # Find or create a payment method
        payment_method = self.env["payment.method"].create(
            {
                "name": "Test Dinger Method",
                "code": "dinger",
            }
        )

        # Setup sample transaction and other data
        self.payment_tx = self.env["payment.transaction"].create(
            {
                "amount": 100,
                "provider_id": dinger_provider.id,
                "payment_method_id": payment_method.id,
                "currency_id": self.env.ref("base.USD").id,
                "partner_id": self.env.ref("base.res_partner_1").id,
            }
        )

        with patch.object(
            type(self.payment_tx),
            "dinger_make_request",
            return_value=("url", "payload", "hash"),
        ), patch.object(
            type(self.payment_tx),
            "_prepare_dinger_data",
            return_value={"dummy": "data"},
        ):
            result_dinger = self.payment_tx._get_specific_rendering_values(
                self.payment_tx
            )

            self.assertEqual(result_dinger["api_url"], "url")
            self.assertEqual(result_dinger["payload"], "payload")
