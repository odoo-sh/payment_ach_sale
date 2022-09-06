# -*- coding: utf-8 -*-
# Copyright 2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).
from odoo import models, fields

class AccountPaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    is_default_incoming_payment = fields.Boolean(string="Default For Incoming Payments")