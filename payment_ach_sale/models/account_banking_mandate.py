# -*- coding: utf-8 -*-
# Copyright 2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).
from odoo import models


class AccountBankingMandate(models.Model):
    _inherit = "account.banking.mandate"

    def set_payment_modes_on_partner(self):
        customer_payment_mode = self.env["account.payment.mode"].search([("payment_type", "=", "inbound"),("company_id", "=", self.company_id.id),('is_default_incoming_payment','=',True)],limit=1)
        if self.partner_id.customer_rank and not self.partner_id.customer_payment_mode_id and customer_payment_mode:
            self.partner_id.write({'customer_payment_mode_id':customer_payment_mode.id})
        else:
            super(AccountBankingMandate,self).set_payment_modes_on_partner()