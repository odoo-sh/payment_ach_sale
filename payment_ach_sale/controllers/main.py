# -*- coding: utf-8 -*-
# Copyright 2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).
import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class ACHController(http.Controller):
    _accept_url = '/payment/ach/feedback'

    @http.route([
        '/payment/ach/feedback',
    ], type='http', auth='public', csrf=False)
    def ach_form_feedback(self, **post):
        _logger.info('Beginning form_feedback with post data %s', pprint.pformat(post))  # debug
        request.env['payment.transaction'].sudo().form_feedback(post, 'ach')
        return werkzeug.utils.redirect('/payment/process')
