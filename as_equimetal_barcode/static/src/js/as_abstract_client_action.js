odoo.define('as_equimetal_barcode.as_ClientAction', function (require) {
    'use strict';
    console.log('ENTRO A CLIENTQ')
    var ClientAction = require('stock_barcode.ClientAction');

    var concurrency = require('web.concurrency');
    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');
    var BarcodeParser = require('barcodes.BarcodeParser');

    var ViewsWidget = require('stock_barcode.ViewsWidget');
    var HeaderWidget = require('stock_barcode.HeaderWidget');
    var LinesWidget = require('stock_barcode.LinesWidget');
    var SettingsWidget = require('stock_barcode.SettingsWidget');
    var utils = require('web.utils');
    var _t = core._t;
    var vals_resp 

    function urlParam2(name) {
        var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
        if (results == null) {
            return null;
        }
        return decodeURI(results[1]) || 0;
    }

    function searchReadGS1(barcode) {
        console.log('Enro aqui tercero' + barcode)
        var urlcadena = window.location.origin + '/quimetal/barcode' + '?barcode=' + barcode;
        console.log(urlcadena);
        window.vals_resp = ''
        $.ajax({
            url: urlcadena,
            success: function (respuesta) {
                var obj = JSON.parse(respuesta);
                window.vals_resp = obj;

            },
            error: function () {
                console.log("No se ha podido obtener la información");
                window.vals_resp = {
                    'type': false,
                    'barcode': barcode,
                    'product': false,
                };
            }
        });
        return vals_resp;

    }
    var as_ClientAction = ClientAction.include({

        events: {
            'click .o_barman': '_asBarcode',
            'change .o_search_barman': '_asAutoSearchBarcode',
        },

        /**
         * Handles the `add_product` OdooEvent. It destroys `this.linesWidget` and displays an instance
         * of `ViewsWidget` for the line model.
         * `this.ViewsWidget`
         *
         * @private
         * @param {OdooEvent} ev
         */
        _asBarcode: function (ev) {
            var barcode = $('#barman').val();
            console.log("barcode:" + barcode);
            this._onBarcodeScannedHandler(barcode);
        },
        _asAutoSearchBarcode: function (ev) {
            var barcode = $('#barman').val();
            console.log("barcode:" + barcode);
            this._onBarcodeScannedHandler(barcode);
        },
        start: function () {
            var self = this;
            // this.$('.o_content').addClass('o_barcode_client_action');
            // core.bus.on('barcode_scanned', this, this._onBarcodeScannedHandler);
    
            this.headerWidget = new HeaderWidget(this);
            this.settingsWidget = new SettingsWidget(this, this.actionParams.model, this.mode, this.allow_scrap);
            return this._super.apply(this, arguments).then(function () {
                return Promise.all([
                    self.headerWidget.prependTo(self.$('.o_content')),
                    self.settingsWidget.appendTo(self.$('.o_content'))
                ]).then(function () {
                    self.settingsWidget.do_hide();
                    return self._save();
                }).then(function () {
                    return self._reloadLineWidget(self.currentPageIndex);
                });
            });
        },

        /**
         * Handles the barcode scan event. Dispatch it to the appropriate method if it is a
         * commande, else use `this._onBarcodeScanned`.
         *
         * @private
         * @param {String} barcode scanned barcode
         */
        _onBarcodeScannedHandler: function (barcode) {
            var resultado = {}
            var self = this;
            var debug_gs1 = urlParam2('debug_gs1');
            if (debug_gs1) {
                barcode = debug_gs1;
                // alert(debug_gs1)
            }
            // barcode = '104443391MPQUI01117210308';
            //llamando a endpoint barcode
            var urlcadena = window.location.origin + '/quimetal/barcode' + '?barcode=' + barcode;
            
            
            $.ajax({
                url: urlcadena,
                global: false,
                async:false,
                success: function (respuesta) {
                    window.val1 = JSON.parse(respuesta);
                    vals_resp = JSON.parse(respuesta);
                    console.log('IDs: ' + (vals_resp.result))
                    // alert(vals_resp.result)
                    
                },
                error: function () {
                    console.log("No se ha podido obtener la información");
                    vals_resp = {
                        'type': false,
                        'barcode': barcode,
                        'product': false,
                    };
                }
            });
            resultado = vals_resp;
            console.log('resultado: ' + JSON.stringify(resultado));
            if (resultado.type) {
                barcode = resultado.lote;
                $('#as_barcode_scanned').text(vals_resp.barcode);
                $('#as_barcode_scanned2').text(vals_resp.result);
                $('#barman').val("");
            } else {
                $('#as_barcode_scanned').text(barcode);
                $('#as_barcode_scanned2').text("");
                $('#barman').val("");
            }

            this.mutex.exec(function () {
                if (self.mode === 'done' || self.mode === 'cancel') {
                    self.do_warn(false, _t('Scanning is disabled in this state'));
                    return Promise.resolve();
                }
                var commandeHandler = self.commands[barcode];
                if (commandeHandler) {
                    return commandeHandler();
                }
                return self._onBarcodeScanned(barcode).then(function () {
                    // FIXME sle: not the right place to do that
                    if (self.show_entire_packs && self.lastScannedPackage) {
                        return self._reloadLineWidget(self.currentPageIndex);
                    }
                });
            });
        },
    });
    core.action_registry.add('stock_barcode.stock_barcode_client_action', as_ClientAction);
    return as_ClientAction;

});