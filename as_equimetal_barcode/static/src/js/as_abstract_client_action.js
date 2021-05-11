odoo.define('as_equimetal_barcode.ClientActionQ', function (require) {
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
    window.actionq = ClientAction;
    var ClientActionQ = ClientAction.include({
  /**
     * Handle what needs to be done when a product is scanned.
     *
     * @param {string} barcode scanned barcode
     * @param {Object} linesActions
     * @returns {Promise}
     */
    _step_product: function (barcode, linesActions) {
        console.log('se ha entrado a escanear codigos de bara ee4jemplo')
        var self = this;
        this.currentStep = 'product';
        this.stepState = $.extend(true, {}, this.currentState);
        var errorMessage;

        var product = this._isProduct(barcode);
        if (product) {
            if (product.tracking !== 'none' && self.requireLotNumber) {
                this.currentStep = 'lot';
            }
            var res = this._incrementLines({'product': product, 'barcode': barcode});
            if (res.isNewLine) {
                if (this.actionParams.model === 'stock.inventory') {
                    // FIXME sle: add owner_id, prod_lot_id, owner_id, product_uom_id
                    return this._rpc({
                        model: 'product.product',
                        method: 'get_theoretical_quantity',
                        args: [
                            res.lineDescription.product_id.id,
                            res.lineDescription.location_id.id,
                        ],
                    }).then(function (theoretical_qty) {
                        res.lineDescription.theoretical_qty = theoretical_qty;
                        linesActions.push([self.linesWidget.addProduct, [res.lineDescription, self.actionParams.model]]);
                        self.scannedLines.push(res.id || res.virtualId);
                        return Promise.resolve({linesActions: linesActions});
                    });
                } else {
                    linesActions.push([this.linesWidget.addProduct, [res.lineDescription, this.actionParams.model]]);
                }
            } else if (!(res.id || res.virtualId)) {
                return Promise.reject(_("There are no lines to increment."));
            } else {
                if (product.tracking === 'none' || !self.requireLotNumber) {
                    linesActions.push([this.linesWidget.incrementProduct, [res.id || res.virtualId, product.qty || 1, this.actionParams.model]]);
                } else {
                    linesActions.push([this.linesWidget.incrementProduct, [res.id || res.virtualId, 0, this.actionParams.model]]);
                }
            }
            this.scannedLines.push(res.id || res.virtualId);
            return Promise.resolve({linesActions: linesActions});
        } else {
            var success = function (res) {
                return Promise.resolve({linesActions: res.linesActions});
            };
            var fail = function (specializedErrorMessage) {
                self.currentStep = 'product';
                if (specializedErrorMessage){
                    return Promise.reject(specializedErrorMessage);
                }
                if (! self.scannedLines.length) {
                    if (self.groups.group_tracking_lot) {
                        errorMessage = _t("You are expected to scan one or more products or a package available at the picking's location");
                    } else {
                        errorMessage = _t('ERROR “PRODUCTO NO ESTÁ EN SISTEMA, DEBE CREARLO');
                    }
                    return Promise.reject(errorMessage);
                }

                var destinationLocation = self.locationsByBarcode[barcode];
                if (destinationLocation) {
                    return self._step_destination(barcode, linesActions);
                } else {
                    errorMessage = _t('You are expected to scan more products or a destination location.');
                    return Promise.reject(errorMessage);
                }
            };
            return self._step_lot(barcode, linesActions).then(success, function () {
                return self._step_package(barcode, linesActions).then(success, fail);
            });
        }
    },

        /**
         * Handle what needs to be done when a lot is scanned.
         *
         * @param {string} barcode scanned barcode
         * @param {Object} linesActions
         * @returns {Promise}
         */
        _step_lot: function (barcode, linesActions) {
            
            if (! this.groups.group_production_lot) {
                return Promise.reject();
            }
            this.currentStep = 'lot';
            this.stepState = $.extend(true, {}, this.currentState);
            var errorMessage;
            var self = this;
    
            // Bypass this step if needed.
            if (this.productsByBarcode[barcode]) {
                
                return this._step_product(barcode, linesActions);
            } else if (this.locationsByBarcode[barcode]) {
                return this._step_destination(barcode, linesActions);
            }
    
            var getProductFromLastScannedLine = function () {
                if (self.scannedLines.length) {
                    var idOrVirtualId = self.scannedLines[self.scannedLines.length - 1];
                    var line = _.find(self._getLines(self.currentState), function (line) {
                        return line.virtual_id === idOrVirtualId || line.id === idOrVirtualId;
                    });
                    if (line) {
                        var product = self.productsByBarcode[line.product_barcode || line.product_id.barcode];
                        // Product was added by lot or package
                        if (!product) {
                            return false;
                        }
                        product.barcode = line.product_barcode || line.product_id.barcode;
                        return product;
                    }
                }
                return false;
            };
    
            var getProductFromCurrentPage = function () {
                return _.map(self.pages[self.currentPageIndex].lines, function (line) {
                    return line.product_id.id;
                });
            };
    
            var getProductFromOperation = function () {
                return _.map(self._getLines(self.currentState), function (line) {
                    return line.product_id.id;
                });
            };
    
            var readProductQuant = function (product_id, lots) {
                var advanceSettings = self.groups.group_tracking_lot || self.groups.group_tracking_owner;
                var product_barcode = _.findKey(self.productsByBarcode, function (product) {
                    return product.id === product_id;
                });
                var product = false;
                var prom = Promise.resolve();
    
                if (product_barcode) {
                    product = self.productsByBarcode[product_barcode];
                    product.barcode = product_barcode;
                }
    
                if (!product || advanceSettings) {
                    var lot_ids = _.map(lots, function (lot) {
                        return lot.id;
                    });
                    prom = self._rpc({
                        model: 'product.product',
                        method: 'read_product_and_package',
                        args: [product_id],
                        kwargs: {
                            lot_ids: advanceSettings ? lot_ids : false,
                            fetch_product: !(product),
                        },
                    });
                }
    
                return prom.then(function (res) {
                    product = product || res.product;
                    var lot = _.find(lots, function (lot) {
                        return lot.product_id[0] === product.id;
                    });
                    var data = {
                        lot_id: lot.id,
                        lot_name: lot.display_name,
                        product: product
                    };
                    if (res && res.quant) {
                        data.package_id = res.quant.package_id;
                        data.owner_id = res.quant.owner_id;
                    }
                    return Promise.resolve(data);
                });
            };
    
            var getLotInfo = function (lots) {
                var products_in_lots = _.map(lots, function (lot) {
                    return lot.product_id[0];
                });
                var products = getProductFromLastScannedLine();
                var product_id = _.intersection(products, products_in_lots);
                if (! product_id.length) {
                    products = getProductFromCurrentPage();
                    product_id = _.intersection(products, products_in_lots);
                }
                if (! product_id.length) {
                    products = getProductFromOperation();
                    product_id = _.intersection(products, products_in_lots);
                }
                if (! product_id.length) {
                    product_id = [lots[0].product_id[0]];
                }
                return readProductQuant(product_id[0], lots);
            };


            var searchReadGS1 = function (barcode) {
                url = window.location.origin
                var urlcadena = window.location.origin + '/quimetal/barcode' + '?barcode=' + barcode;
                console.log(urlcadena);
                $.ajax({
                    url: urlcadena,
                    success: function (respuesta) {
                        var obj = JSON.parse(respuesta);
                        window.vals_resp = obj;
                        
                    },
                    error: function () {
                        console.log("No se ha podido obtener la información");
                        window.vals_resp = {
                            'type':false,
                            'barcode': barcode,
                            'product': false,
                        };
                    }
                });
                
                return vals_resp;
            
            };
            var urlParam = function (name) {
                var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
                if (results == null) {
                    return null;
                }
                return decodeURI(results[1]) || 0;
            }
            
            var searchRead = function (barcode) {
                
                var debug_gs1 = urlParam('debug_gs1');
                if(debug_gs1){
                    barcode = debug_gs1;
                }
                barcode = searchReadGS1(barcode);
                window.barr = barcode;
                var product = false;
                if (barcode.type){
                    product = barcode.product;
                    barcode = barcode.lote;
                }
                if (!product){
                    console.log(_t('ERROR “PRODUCTO NO ESTÁ EN SISTEMA, DEBE CREARLO.'));
                    errorMessage = _t('ERROR “PRODUCTO NO ESTÁ EN SISTEMA, DEBE CREARLO.');
                    return Promise.reject(errorMessage);
                }
                
                var line_with_lot = _.find(self.currentState.move_line_ids, function (line) {
                    return (line.lot_id && line.lot_id[1] === barcode) || line.lot_name === barcode;
                });
                var def;
                window.lot = line_with_lot;
                if (line_with_lot) {
                    def = Promise.resolve([{
                        name: barcode,
                        display_name: barcode,
                        id: line_with_lot.lot_id[0],
                        product_id: [line_with_lot.product_id.id, line_with_lot.display_name],
                    }]);                    
                } else {
                    def = self._rpc({
                        model: 'stock.production.lot',
                        method: 'search_read',
                        domain: [['name', '=', barcode]],
                    });
                }
                window.prueba = product;
                
                return def.then(function (res) {
                    window.mensaje = res;
                    
                    if (! res.length) {
                        errorMessage = _t('ERROR: PRODUCTO –LOTE NO ESTÁ EN LA ORDEN.');
                        return Promise.reject(errorMessage);
                    }
                    
                    return getLotInfo(res);
                });
            };
    
            var create = function (barcode, product) {
                return self._rpc({
                    model: 'stock.production.lot',
                    method: 'create',
                    args: [{
                        'name': barcode,
                        'product_id': product.id,
                        'company_id': self.currentState.company_id[0],
                    }],
                });
            };
    
            var def;
            if (this.currentState.use_create_lots &&
                ! this.currentState.use_existing_lots) {
                // Do not create lot if product is not set. It could happens by a
                // direct lot scan from product or source location step.
                var product = getProductFromLastScannedLine();
                if (! product  || product.tracking === "none") {
                    return Promise.reject();
                }
                def = Promise.resolve({lot_name: barcode, product: product});
            } else if (! this.currentState.use_create_lots &&
                        this.currentState.use_existing_lots) {
                
                def = searchRead(barcode);
            } else {
                
                def = searchRead(barcode).then(function (res) {
                    return Promise.resolve(res);
                }, function (errorMessage) {
                    var product = getProductFromLastScannedLine();
                    if (product && product.tracking !== "none") {
                        return create(barcode, product).then(function (lot_id) {
                            return Promise.resolve({lot_id: lot_id, lot_name: barcode, product: product});
                        });
                    }
                    return Promise.reject(errorMessage);
                });
            }
            return def.then(function (lot_info) {
                var product = lot_info.product;
                if (product.tracking === 'serial' && self._lot_name_used(product, barcode)){
                    errorMessage = _t('The scanned serial number is already used.');
                    return Promise.reject(errorMessage);
                }
                var res = self._incrementLines({
                    'product': product,
                    'barcode': lot_info.product.barcode,
                    'lot_id': lot_info.lot_id,
                    'lot_name': lot_info.lot_name,
                    'owner_id': lot_info.owner_id,
                    'package_id': lot_info.package_id,
                });
                if (res.isNewLine) {
                    self.scannedLines.push(res.lineDescription.virtual_id);
                    linesActions.push([self.linesWidget.addProduct, [res.lineDescription, self.actionParams.model]]);
                } else {
                    if (self.scannedLines.indexOf(res.lineDescription.id) === -1) {
                        self.scannedLines.push(res.lineDescription.id || res.lineDescription.virtual_id);
                    }
                    linesActions.push([self.linesWidget.incrementProduct, [res.id || res.virtualId, 1, self.actionParams.model]]);
                    linesActions.push([self.linesWidget.setLotName, [res.id || res.virtualId, barcode]]);
                }
                return Promise.resolve({linesActions: linesActions});
            });
        },
    });
    core.action_registry.add('stock_barcode.stock_barcode_client_action', ClientActionQ);
    return ClientActionQ;

    });
    