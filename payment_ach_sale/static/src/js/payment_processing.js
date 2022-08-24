odoo.define('payment_ach_sale.processing', function (require) {
'use strict';

var ajax = require('web.ajax');
var rpc = require('web.rpc')
var publicWidget = require('web.public.widget');

var PaymentProcessing = publicWidget.registry.PaymentProcessing;

return PaymentProcessing.include({
    processPolledData: function(transactions) {
        this._super.apply(this, arguments);
        if (transactions.length > 0 && ['ach'].indexOf(transactions[0].acquirer_provider) >= 0) {
            window.location = transactions[0].return_url;
            return;
        }
    },
});
});
