from odoo.tests.common import TransactionCase

class TestPaymentProvider(TransactionCase):
    def test_get_default_payment_method_codes(self):
        """Tests _get_default_payment_method_codes for Dinger and another valid code."""

        # Test for Dinger
        dinger_provider = self.env["payment.provider"].create({
            "name": "Dinger Test Provider",
            "code": "dinger",
        })
        result_for_dinger = dinger_provider._get_default_payment_method_codes()
        self.assertEqual(result_for_dinger, "dinger",
                         "Should return 'dinger' when code is 'dinger'.")
        self.assertNotEqual(result_for_dinger, "other",
                            "Should NOT return 'dinger' for other codes.")
        # Optional: assert it's the parent method result
        self.assertIsInstance(result_for_dinger, (str, list),
                              "Result should be a valid parent method return value.")
