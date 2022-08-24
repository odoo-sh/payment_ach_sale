# -*- coding: utf-8 -*-
# Copyright 2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).
from odoo import models, api, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare

import logging
import pprint

_logger = logging.getLogger(__name__)


class ACHPaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _ach_form_get_tx_from_data(self, data):
        reference, amount, currency_name = data.get('reference'), data.get('amount'), data.get('currency_name')
        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = _('received data for reference %s') % (pprint.pformat(reference))
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return tx

    def _ach_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        if float_compare(float(data.get('amount') or '0.0'), self.amount, 2) != 0:
            invalid_parameters.append(('amount', data.get('amount'), '%.2f' % self.amount))
        if data.get('currency') != self.currency_id.name:
            invalid_parameters.append(('currency', data.get('currency'), self.currency_id.name))
        return invalid_parameters

    def _ach_form_validate(self, data):
        _logger.info('Validated ACH payment for tx %s: set as pending' % (self.reference))
        self._set_transaction_pending()
        return True

    def _get_payment_transaction_sent_message(self):
        self.ensure_one()
        if self.provider == 'ach':
            message = _('The customer has selected %s to pay this document.') % (self.acquirer_id.name)
        else:
            message = super(ACHPaymentTransaction,self)._get_payment_transaction_sent_message()
        return message

    def _log_payment_transaction_received(self):
        for transaction in self.filtered(lambda t: t.provider != 'ach'):
            super(ACHPaymentTransaction, transaction)._log_payment_transaction_received()

    def _set_transaction_pending(self):
        for record in self:
            if record.acquirer_id.provider == 'ach':
                record.env.context =dict(record.env.context)
                record.env.context.update({'no_email': True})
                for so in record.sale_order_ids:
                    so.reference = record._compute_sale_order_reference(so)
        super(ACHPaymentTransaction, self)._set_transaction_pending()
