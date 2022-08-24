# Copyright 2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).
{
    "name": "ACH Payment Acquirer",
    "summary": """""",
    "version": "14.0.1.0.0",
    "category": "Accounting/Payment Acquirers",
    "website": "http://sodexis.com/",
    "author": "Sodexis",
    "license": "OPL-1",
    "installable": True,
    "application": False,
    "depends": [
        'payment',
        'payment_transfer',
        'account_banking_ach_direct_debit',
    ],
    "data": [
        "views/payment_ach_templates.xml",
        "data/payment_acquirer_data.xml",
        "views/assets.xml",
        "views/payment_acquirer_views.xml",
        "views/sale_order_views.xml",
        "views/website_sale_templates.xml"
    ],
}
