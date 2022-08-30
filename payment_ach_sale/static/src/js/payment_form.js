odoo.define('payment_ach_sale.ach_payment_form', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var PaymentForm = require('payment.payment_form');

    var QWeb = core.qweb;
    var _t = core._t;

    ajax.loadXML('/payment_ach_sale/static/src/xml/ach_payment_bank_details_template.xml', core.qweb);

    PaymentForm.include({

        /*** Transaction creation for ACH payment***/
        achPaymentProcess: function(button, $checkedRadio, acquirer_id) {
            var self = this;
            self.disableButton(button);
            var acquirer_form = false;
            if (this.isNewPaymentRadio($checkedRadio)) {
                acquirer_form = this.$('#o_payment_add_token_acq_' + acquirer_id);
            } else {
                acquirer_form = this.$('#o_payment_form_acq_' + acquirer_id);
            }
            var $tx_url = self.$el.find('input[name="prepare_tx_url"]');
            if ($tx_url.length === 1) {
                var form_save_token = acquirer_form.find('input[name="o_payment_form_save_token"]').prop('checked');
                return self._rpc({
                    route: $tx_url[0].value,
                    params: {
                        'acquirer_id': parseInt(acquirer_id),
                        'save_token': form_save_token,
                        'access_token': self.options.accessToken,
                        'success_url': self.options.successUrl,
                        'error_url': self.options.errorUrl,
                        'callback_method': self.options.callbackMethod,
                        'order_id': self.options.orderId,
                        'invoice_id': self.options.invoiceId,
                    },
                }).then(function(result) {
                    if (result) {
                        var newForm = document.createElement('form');
                        newForm.setAttribute("method", self._get_redirect_form_method());
                        newForm.setAttribute("provider", $checkedRadio.data('provider'));
                        newForm.hidden = true;
                        newForm.innerHTML = result;
                        var action_url = $(newForm).find('input[name="data_set"]').data('actionUrl');
                        newForm.setAttribute("action", action_url);
                        $(document.getElementsByTagName('body')[0]).append(newForm);
                        $(newForm).find('input[data-remove-me]').remove();
                        if (action_url) {
                            newForm.submit(); // and finally submit the form
                            return new Promise(function() {});
                        }
                    } else {
                        self.displayError(
                            _t('Server Error'),
                            _t("We are not able to redirect you to the payment form.")
                        );
                        self.enableButton(button);
                    }
                }).guardedCatch(function(error) {
                    error.event.preventDefault();
                    self.displayError(
                        _t('Server Error'),
                        _t("We are not able to redirect you to the payment form.") + " " +
                        self._parseError(error)
                    );
                    self.enableButton(button);
                });
            } else {
                // we append the form to the body and send it.
                self.displayError(
                    _t("Cannot setup the payment"),
                    _t("We're unable to process your payment.")
                );
                self.enableButton(button);
            }
        },

        /*** Check the input values numeric or not***/
        check_numeric:function(event) {
            var regex = new RegExp("^[0-9]+$");
            var key = String.fromCharCode(!event.charCode ? event.which : event.charCode);
            if (!regex.test(key)) {
               event.preventDefault();
               return false;
            }
        },

        payEvent: function(ev) {
            ev.stopPropagation();
            ev.preventDefault();
            if (ev.type === 'submit') {
                var button = $(ev.target).find('*[type="submit"]')[0]
            } else {
                var button = ev.target;
            }
            var current_url = ev.currentTarget.baseURI
            var order_id = false;
            if (current_url.includes("/my/orders/")) {
                order_id = parseInt(current_url.split("?")[0].split("/my/orders/").slice(-1)[0]);
            }
            else if (current_url.includes("sale_id=")){
               order_id = parseInt(current_url.split("sale_id=")[1].split("&")[0]);
            }
            else if (document.getElementById('ach_sale_order_id') !== 'null')
            {
               order_id = parseInt(document.getElementById('ach_sale_order_id').value);
            }
            var self = this
            var $checkedRadio = this.$('input[type="radio"]:checked');
            var acquirer_id = this.getAcquirerIdFromRadio($checkedRadio);
            /*** Inner function***/
            var validate_bank_details = function() {
                var empty_fields = [];
                var ach_account_number = this.$('#ach_account_number').val();
                var ach_routing_number = this.$('#ach_routing_number').val();
                var ach_bank_name = this.$('#ach_bank_name').val();
                var ach_account_holder_name = this.$('#ach_account_holder_name').val();
                var ach_bank_account_type = this.$('#ach_bank_account_type').val();
                var ach_mandate_checkbox = this.$('#ach_mandate_checkbox').is(":checked");
                if (ach_account_number.length === 0) {
                    empty_fields.push('ach_account_number');
                }
                if (ach_routing_number.length === 0) {
                    empty_fields.push('ach_routing_number');
                }
                if (ach_bank_name.length === 0) {
                    empty_fields.push('ach_bank_name');
                }
                if (ach_account_holder_name.length === 0) {
                    empty_fields.push('ach_account_holder_name');
                }
                if (ach_bank_account_type.length === 0) {
                    empty_fields.push('ach_bank_account_type');
                }
                if (!ach_mandate_checkbox) {
                    empty_fields.push('ach_mandate_checkbox');
                }
                if (empty_fields.length !== 0) {
                    for (let i = 0; i < empty_fields.length; ++i) {
                        var empty_field = ('#').concat(empty_fields[i])
                        this.$(empty_field).addClass('error')
                        var label_for = empty_fields[i]
                        this.$("label[for='" + label_for + "']").removeClass('ach_payment_bank_field')
                        this.$("label[for='" + label_for + "']").addClass('ach_payment_bank_field_required')
                    }
                    return false;
                }
                this._rpc({
                        model: 'res.partner',
                        method: 'read',
                        args: [
                            [parseInt(self.options.partnerId)],
                            ['commercial_partner_id']
                        ],
                    })
                    .then(function(partner_ids) {
                        if (partner_ids.length !== 0) {
                            var domain = [
                                ['acc_number', '=', ach_account_number],
                                ['partner_id', '=', parseInt(partner_ids[0]['commercial_partner_id'][0])]
                            ];
                            self._rpc({
                                    model: 'res.partner.bank',
                                    method: 'search_read',
                                    args: [domain,['id']],
                                    context: {
                                       'ach_payment': true,
                                    },
                                })
                                .then(function(bank_account_ids) {
                                    if (bank_account_ids.length === 0) {
                                        self._rpc({
                                            model: 'res.partner.bank',
                                            method: 'create',
                                            args: [{
                                                'acc_number': ach_account_number,
                                                'aba_routing': ach_routing_number,
                                                'acc_holder_name': ach_account_holder_name,
                                                'ach_bank_account_type': ach_bank_account_type,
                                                'bank_name': ach_bank_name,
                                                'partner_id': parseInt(partner_ids[0]['commercial_partner_id'][0]),
                                                'mandate_ids': [
                                                    [0, 0, {
                                                        'format': 'basic',
                                                        'type': 'oneoff',
                                                        'signature_date': new Date().toJSON().slice(0, 10),
                                                        'delay_days': 1
                                                    }]
                                                ]
                                            }],
                                            context: {
                                                'ach_payment': true,
                                                'sale_order_id': order_id
                                            },
                                        }).then(function(bank_account_id) {
                                            self.achPaymentProcess(button, $checkedRadio, acquirer_id)
                                        });

                                    } else {
                                        self._rpc({
                                            model: 'res.partner.bank',
                                            method: 'write',
                                            args: [
                                                [bank_account_ids[0]['id']], {
                                                    'aba_routing': ach_routing_number,
                                                    'acc_holder_name': ach_account_holder_name,
                                                    'ach_bank_account_type': ach_bank_account_type,
                                                    'bank_name': ach_bank_name,
                                                }
                                            ],
                                            context: {
                                                'ach_payment': true,
                                                'sale_order_id': order_id
                                            },
                                        }).then(function(bank_account_id) {
                                            self.achPaymentProcess(button, $checkedRadio, acquirer_id)
                                        });
                                    }
                                })
                        }
                    });
            }
            /*** Pay Event function for ACH payment workflow***/
            if ($checkedRadio.data('provider') === 'ach') {
                this._rpc({
                        model: 'payment.acquirer',
                        method: 'read',
                        args: [
                            [parseInt(acquirer_id)],
                            ['mandate_msg']
                        ],
                    })
                    .then(function(payment_acquier) {
                        if (payment_acquier.length !== 0) {
                            $content.find('div.ach_mandate').children('#ach_mandate_text')[0].innerHTML = payment_acquier[0]['mandate_msg'].replace('<p>', '').replace('</p>', '')
                        }
                    });
                var $content = $(QWeb.render("payment_ach_sale.ACHPaymentBankDetailsForm", {}));
                var dialog = new Dialog(this, {
                    title: _t('Please fill the ACH payment details'),
                    size: 'medium',
                    $content: $content,
                    modal: true,
                    buttons: [{
                        text: _t('Pay'),
                        classes: 'btn-primary o_ach_payment_confirm',
                        disabled: true,
                        click: validate_bank_details
                    }, ],
                });
                dialog.opened(function () {
                    dialog.$el.on('change', '#ach_mandate_checkbox', function (ev) {
                        ev.preventDefault();
                        dialog.$footer.find('.o_ach_payment_confirm')[0].disabled = !ev.currentTarget.checked;
                    });
                    dialog.$el.on('keypress', '#ach_bank_name', function (event) {
                        if (dialog.$el.find('input#ach_bank_name.error')) {
                            dialog.$el.find('input#ach_bank_name.error').removeClass('error')
                            dialog.$el.find("label[for='ach_bank_name']").addClass('ach_payment_bank_field')
                            dialog.$el.find("label[for='ach_bank_name']").removeClass('ach_payment_bank_field_required')
                         }
                    });
                    dialog.$el.on('keypress', '#ach_routing_number', function (event) {
                        self.check_numeric(event)
                        if (dialog.$el.find('input#ach_routing_number.error')) {
                            dialog.$el.find('input#ach_routing_number.error').removeClass('error')
                            dialog.$el.find("label[for='ach_routing_number']").addClass('ach_payment_bank_field')
                            dialog.$el.find("label[for='ach_routing_number']").removeClass('ach_payment_bank_field_required')
                         }
                    });
                    dialog.$el.on('keypress', '#ach_account_holder_name', function (event) {
                        if (dialog.$el.find('input#ach_account_holder_name.error')) {
                            dialog.$el.find('input#ach_account_holder_name.error').removeClass('error')
                            dialog.$el.find("label[for='ach_account_holder_name']").addClass('ach_payment_bank_field')
                            dialog.$el.find("label[for='ach_account_holder_name']").removeClass('ach_payment_bank_field_required')
                         }
                    });
                    dialog.$el.on('keypress', '#ach_account_number', function (event) {
                        self.check_numeric(event)
                        if (dialog.$el.find('input#ach_account_number.error')) {
                            dialog.$el.find('input#ach_account_number.error').removeClass('error')
                            dialog.$el.find("label[for='ach_account_number']").addClass('ach_payment_bank_field')
                            dialog.$el.find("label[for='ach_account_number']").removeClass('ach_payment_bank_field_required')
                         }
                    });
                    dialog.$el.on('change', '#ach_bank_account_type', function (event) {
                        self.check_numeric(event)
                        if (dialog.$el.find('select#ach_bank_account_type.error')) {
                            dialog.$el.find('select#ach_bank_account_type.error').removeClass('error')
                            dialog.$el.find("label[for='ach_bank_account_type']").addClass('ach_payment_bank_field')
                            dialog.$el.find("label[for='ach_bank_account_type']").removeClass('ach_payment_bank_field_required')
                         }
                    });
                });
                dialog.open();
            } else {
                return this._super.apply(this, arguments);
            }
        },
    });
});