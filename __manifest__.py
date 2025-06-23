# Developed by Info"Lib. See LICENSE file for full copyright and licensing details.
{
    "name": "payment_dinger",
    "version": "1.0",
    "author": "SME Intellect",
    'website': "https://www.smeintellect.com",
    "category": "Accounting/Payment Providers",
    "summary": "A payment provider.",
    "description": " ",  # Non-empty string to avoid loading the README file.
    "depends": ["account", "dinger_mixin", "payment", "sale_management", "website_sale"],
    "data": [
        #Views
        "views/payment_dinger_templates.xml",
        # "views/payment_provider_views.xml",
        "views/account_jorunal_view.xml",
        "views/payment_transaction_status_views.xml",

        #Security
        "security/ir.model.access.csv",

        # Data
        "data/payment_method_data.xml",
        "data/payment_provider_data.xml",
    ],
    'external_dependencies': {
        'python': ['pycryptodome']
    },
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "images": ["static/description/banner.png"],
    "license": "LGPL-3",
}
