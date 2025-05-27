# Developed by Info"Lib. See LICENSE file for full copyright and licensing details.
{
    "name": "Dinger",
    "version": "1.0",
    "author": "SME Intellect",
    "category": "Accounting/Payment Providers",
    "summary": "A payment provider.",
    "description": " ",  # Non-empty string to avoid loading the README file.
    "depends": ["payment"],
    "data": [
        "views/payment_dinger_templates.xml",
        "views/payment_provider_views.xml",

        # Data
        "data/payment_method_data.xml",
        "data/payment_provider_data.xml",
    ],
    'external_dependencies': {
        'python': ['dinger-payment','pycryptodome','rsa']
    },
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "images": ["static/description/banner.png"],
    "license": "LGPL-3",
}
