# -*- coding: utf-8 -*-
# Copyright 2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import fields, models

class ACHPaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[
        ('ach', 'ACH Payment')
    ], default='ach', ondelete={'ach': 'set default'})
    mandate_msg = fields.Html('Mandate Message', translate=True)

    def ach_get_form_action_url(self):
        return '/payment/ach/feedback'
