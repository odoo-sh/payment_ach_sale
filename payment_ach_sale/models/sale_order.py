# -*- coding: utf-8 -*-
# Copyright 2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).
from odoo import fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    mandate_id = fields.Many2one(
        "account.banking.mandate",
        string="Direct Debit Mandate",
        ondelete="restrict",
        check_company=True,
        readonly=False,
        domain="[('partner_id', '=', commercial_partner_id), "
        "('state', 'in', ('draft', 'valid')), "
        "('company_id', '=', company_id)]",
        copy=False)

    def _prepare_invoice(self):
        """Copy mandate from sale order to invoice"""
        vals = super()._prepare_invoice()
        if self.mandate_id:
            vals["mandate_id"] = self.mandate_id.id or False
        return vals