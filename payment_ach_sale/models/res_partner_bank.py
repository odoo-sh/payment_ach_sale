# -*- coding: utf-8 -*-
# Copyright 2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).
from odoo import models, fields, api, _
from datetime import date


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    ach_bank_account_type = fields.Selection(selection=lambda x: x.env['res.partner.bank'].get_supported_account_types(),string='ACH Bank Account Type')
    acc_type = fields.Selection(selection=lambda x: x.env['res.partner.bank'].get_supported_account_types(),
                                compute='_compute_acc_type',
                                inverse='_inverse_acc_type',
                                string='Type',
                                help='Bank account type: Normal or IBAN. Inferred from the bank account number.')

    def _inverse_acc_type(self):
        self.ach_bank_account_type = self.acc_type

    @api.depends('acc_number')
    def _compute_acc_type(self):
        for bank in self:
            if bank.ach_bank_account_type:
                bank.acc_type = bank.ach_bank_account_type
            else:
                bank.acc_type = self.retrieve_acc_type(bank.acc_number)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self._context.get('ach_payment',False):
            self = self.sudo()
        return super(ResPartnerBank, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    @api.model
    def create(self, vals):
        if self._context.get('ach_payment',False):
            self = self.sudo()
            if vals.get('bank_name',False):
                bank_id = self.env["res.bank"].search([('name','=',vals.get('bank_name')),('routing_number','=',vals.get('aba_routing'))])
                if not bank_id:
                    bank_id = self.env["res.bank"].create({'name':vals.get('bank_name'),'routing_number' : vals.get('aba_routing')})
                vals.update({'bank_id':bank_id.id})
        record = super(ResPartnerBank,self).create(vals)
        if self._context.get('sale_order_id',False):
            sale_order = self.env["sale.order"].browse(self._context.get('sale_order_id'))
            if sale_order and record.mandate_ids:
                #Validate the Mandate
                record.mandate_ids[0].validate()
                values = {'mandate_id':record.mandate_ids[0].id}
                partner_payment_mode_id = sale_order.partner_id.customer_payment_mode_id
                if not sale_order.payment_mode_id and partner_payment_mode_id:
                    values.update({'payment_mode_id': partner_payment_mode_id and partner_payment_mode_id.id})
                sale_order.write(values)
        return record

    def write(self, vals):
        if self._context.get('ach_payment',False):
            self = self.sudo()
            if vals.get('bank_name',False):
                bank_id = self.env["res.bank"].search([('name','=',vals.get('bank_name')),('routing_number','=',vals.get('aba_routing'))])
                if not bank_id:
                    bank_id = self.env["res.bank"].create({'name':vals.get('bank_name'),'routing_number' : vals.get('aba_routing')})
                vals.update({'bank_id':bank_id.id})
        res = super(ResPartnerBank,self).write(vals)
        for partner_bank in self:
            if partner_bank._context.get('sale_order_id',False):
                sale_order = self.env["sale.order"].browse(partner_bank._context.get('sale_order_id'))
                if sale_order and not sale_order.mandate_id:
                    mandate_id = self.env["account.banking.mandate"].create({'format':'basic',
                                            'type':'oneoff', 
                                            'signature_date': date.today(),
                                            'delay_days': 1,
                                            'partner_bank_id': partner_bank.id
                                      })
                    #Validate the Mandate
                    mandate_id.validate()
                    values = {'mandate_id':mandate_id.id}
                    partner_payment_mode_id = sale_order.partner_id.customer_payment_mode_id
                    if not sale_order.payment_mode_id and partner_payment_mode_id:
                        values.update({'payment_mode_id': partner_payment_mode_id and partner_payment_mode_id.id})
                    sale_order.write(values)
        return res

    @api.model
    def _get_supported_account_types(self):
        rslt = super(ResPartnerBank, self)._get_supported_account_types()
        rslt.append(('personal_checking', _('Personal Checking')))
        rslt.append(('personal_saving', _('Personal Savings')))
        rslt.append(('business_checking', _('Business Checking')))
        rslt.append(('business_saving', _('Business Savings')))
        return rslt
