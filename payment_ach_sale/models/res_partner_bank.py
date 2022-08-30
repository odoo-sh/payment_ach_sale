# -*- coding: utf-8 -*-
# Copyright 2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).
from odoo import models, fields, api, _
from datetime import date


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    ach_bank_account_type = fields.Selection([('personal_checking','Personal Checking'),
                                              ('personal_saving','Personal Savings'),
                                              ('business_checking','Business Checking'),
                                              ('business_saving','Business Savings')],string='ACH Bank Account Type')

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
                sale_order.write({'mandate_id':record.mandate_ids[0].id})
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
                    sale_order.write({'mandate_id':mandate_id.id})
        return res

    @api.model
    def retrieve_acc_type(self, acc_number):
        for partner_bank in self.filtered(lambda x:x.ach_bank_account_type):
            return partner_bank.ach_bank_account_type
        return super(ResPartnerBank, self).retrieve_acc_type(acc_number)

    @api.model
    def _get_supported_account_types(self):
        rslt = super(ResPartnerBank, self)._get_supported_account_types()
        rslt.append(('personal_checking', _('Personal Checking')))
        rslt.append(('personal_saving', _('Personal Savings')))
        rslt.append(('business_checking', _('Business Checking')))
        rslt.append(('business_saving', _('Business Savings')))
        return rslt
