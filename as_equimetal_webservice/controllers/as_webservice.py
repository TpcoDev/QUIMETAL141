# -*- coding: utf-8 -*-
from odoo.tools.translate import _
from odoo import http
from odoo import http
from odoo.http import request
from datetime import datetime
from bs4 import BeautifulSoup
import json
import sys
import uuid
from odoo import http
from odoo.http import request, Response
import jsonschema
from jsonschema import validate
import json
import yaml
from . import as_estructuras
import logging
_logger = logging.getLogger(__name__)

from werkzeug import urls
from werkzeug.wsgi import wrap_file

class as_webservice_quimetal(http.Controller):

    # WS001, de SAP a ODOO
    @http.route(['/tpco/odoo/ws001',], auth="public", type="json", method=['POST'], csrf=False)
    def WS001(self, **post):
        post = yaml.load(request.httprequest.data)
        res = {}
        as_token = uuid.uuid4().hex
        try:
            myapikey = request.httprequest.headers.get("Authorization")
            if myapikey == "123":
                res['token'] = as_token
                post = post['params']
                uid = request.env.user.id
                # request.session.logout()
                es_valido = self.validar_json(post, esquema=as_estructuras.esquema_ws001)

                if es_valido:
                    # Tratamiento de cliente
                    cliente = request.env['res.partner']
                    cliente_search = cliente.sudo().search([('name', 'ilike', post['CardName'])])
                    if cliente_search.id:
                        cliente_id = cliente_search.id
                    else:
                        cliente_nuevo = cliente.sudo().create(
                            {
                                "name": post['CardName'],
                                "vat": post['CardCode'],
                            }
                        )
                        cliente_id = cliente_nuevo.id

                    # Orden de compra
                    compra = request.env['purchase.order']
                    date_order = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    date_approve = post['DocDate'].replace("T"," ")[:-3]
                    # date_approve = datetime.strptime(date_approve, '%Y-%m-%d %H:%M:%S')
                    # date_approve = '2021-04-21 10:00:00'
                    compra_nueva_linea = []
                    for linea in post["DatosProdOC"]:
                        producto_uom = request.env['uom.uom']
                        producto_uom_search = producto_uom.sudo().search([('name', 'ilike', linea['MeasureUnit'])])[0]
                        producto_uom_id = 0
                        if producto_uom_search.id:
                            producto_uom_id = producto_uom_search.id

                        # Tratamiento de producto
                        producto = request.env['product.template']
                        producto_search = producto.sudo().search([('default_code', '=', linea['ItemCode'])])
                        if producto_search.id:
                            producto_id = producto_search.id
                            product_product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', producto_id)])[0]
                            product_product_id = product_product.id
                        else:
                            product_data = {
                                "name": str(linea['ItemDescription']) or "",
                                "type": "product",
                                "categ_id": 1,
                                "default_code": str(linea['ItemCode']) or "",
                                "barcode": "",
                                "list_price": 1,
                                "standard_price": 1,
                                "uom_id": producto_uom_id,
                                "uom_po_id": producto_uom_id,
                                "purchase_ok": True,
                                "sale_ok": True,
                            }

                            _logger.debug("\n\n\n\n\nproduct_data: %s", product_data)

                            producto_nuevo = producto.sudo().create(product_data)
                            producto_id = producto_nuevo.id
                            product_product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', producto_id)])[0]
                            product_product_id = product_product.id

                        # Tratamiento de UOM

                        compra_nueva_linea.append(
                                                    {
                                                    'display_type': False,
                                                    "product_id": product_product_id,
                                                    "product_qty": linea["Quantity"],
                                                    # "sequence": 1,
                                                    'name': linea["ItemDescription"],
                                                    'account_analytic_id': False,
                                                    'product_uom': producto_uom_id,
                                                    "price_unit":1,
                                                    "qty_received_manual":0,
                                                    "date_planned":"2021-04-21 10:00:00",
                                                    "taxes_id":[
                                                        [
                                                            6,
                                                            False,
                                                            [
                                                                
                                                            ]
                                                        ]
                                                    ],
                                                    "analytic_tag_ids":[
                                                    [
                                                        6,
                                                        False,
                                                        [
                                                            
                                                        ]
                                                    ]
                                                    ],
                                                    }
                                                )
                    # request.env.cr.commit()
                    _logger.debug("\n\n\n\n\ncompra_nueva_linea: %s", compra_nueva_linea)

                    # Ensamblando la compra
                    compra_nueva = {
                        'name': post['DocNum'], 
                        'origin': post['DocNum'],
                        'priority': '0', 
                        'partner_id': cliente_id, 
                        'partner_ref': False, 
                        'currency_id': 2, 
                        'date_order': date_order,
                        'date_approve': date_approve, 
                        'date_planned': '2021-04-23 10:00:00', 
                        'receipt_reminder_email': False, 
                        'reminder_date_before_receipt': 1, 
                        'notes': post['CardCode'], 
                        'user_id': uid,
                        'company_id': 1, 
                        'payment_term_id': 7, 
                        'fiscal_position_id': False,
                        'order_line': [(0, False, line) for line in compra_nueva_linea],
                        }

                    nueva_compra = request.env['purchase.order'].sudo().create(compra_nueva)
                    
                    # res['token'] = token
                    # request.session.logout()
                    return {
                        "purchase_id": nueva_compra.id,
                        "purchase_name": nueva_compra.name,
                        "Token": as_token,
                        "RespCode":0,
                        "RespMessage":"OC creada correctamente",
                        "json_recibido":post
                    }
                else:
                    res['error'] = "Estructura no Valida"
                    res['Token'] = as_token
                    res_json = json.dumps(res)
                    return res_json
            else:
                res['error'] = "Login o Password erroneo"
                res['Token'] = as_token
                res_json = json.dumps(res)
                return res_json
        except Exception as e:
            return {
                    "Token": as_token,
                    "RespCode":-1,
                    "RespMessage": e
                }

    # WS016, de SAP a ODOO
    @http.route(['/tpco/odoo/ws016',], auth="public", type="json", method=['POST'], csrf=False)
    def WS016(self, **post):
        post = yaml.load(request.httprequest.data)
        res = {}
        as_token = uuid.uuid4().hex
        try:
            myapikey = request.httprequest.headers.get("Authorization")
            if myapikey == "123":
                res['token'] = as_token
                # request.session.logout()
                es_valido = self.validar_json(post, esquema=as_estructuras.esquema_ws016)
                post = post['params']
                uid = request.env.user.id
                if es_valido:
                    # Tratamiento de cliente
                    cliente = request.env['res.partner']
                    cliente_search = cliente.sudo().search([('name', 'ilike', post['CardName'])])
                    if cliente_search.id:
                        cliente_id = cliente_search.id
                    else:
                        cliente_nuevo = cliente.sudo().create(
                            {
                                "name": post['CardName'],
                                "vat": post['CardCode'],
                            }
                        )
                        cliente_id = cliente_nuevo.id

                    # Orden de venta
                    venta = request.env['sale.order']
                    date_order = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    date_approve = post['DocDate'].replace("T"," ")[:-3]
                    # date_approve = datetime.strptime(date_approve, '%Y-%m-%d %H:%M:%S')
                    # date_approve = '2021-04-21 10:00:00'
                    venta_nueva_linea = []
                    for linea in post["DatosProdOV"]:

                        # Tratamiento de producto
                        producto = request.env['product.template']
                        producto_search = producto.sudo().search([('default_code', '=', linea['ItemCode'])])
                        if producto_search.id:
                            producto_id = producto_search.id
                            product_product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', producto_id)])[0]
                            product_product_id = product_product.id
                        else:
                            product_data = {
                                "name": str(linea['ItemDescription']) or "",
                                "type": "product",
                                "categ_id": 1,
                                "default_code": str(linea['ItemCode']) or "",
                                "barcode": "",
                                "list_price": 1,
                                "standard_price": 1,
                                "uom_id": 3,
                                "uom_po_id": 3,
                                "purchase_ok": True,
                                "sale_ok": True,
                            }

                            _logger.debug("\n\n\n\n\nproduct_data: %s", product_data)

                            producto_nuevo = producto.sudo().create(product_data)
                            producto_id = producto_nuevo.id
                            product_product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', producto_id)])[0]
                            product_product_id = product_product.id

                        # Tratamiento de UOM
                        producto_uom = request.env['uom.uom']
                        producto_uom_search = producto_uom.sudo().search([('name', 'ilike', linea['MeasureUnit'])])[0]
                        producto_uom_id = 0
                        if producto_uom_search.id:
                            producto_uom_id = producto_uom_search.id

                        venta_nueva_linea.append(
                                                    {
                                                    'display_type': False,
                                                    "product_id": product_product_id,
                                                    "product_uom_qty": linea["Quantity"],
                                                    # "sequence": 1,
                                                    'name': linea["ItemDescription"],
                                                    # 'account_analytic_id': False,
                                                    'product_uom': producto_uom_id,
                                                    "price_unit":1,
                                                    "route_id":False,
                                                    "customer_lead":0,
                                                    "product_packaging":False,
                                                    "qty_delivered_manual":0,
                                                    "product_template_id":producto_id,

                                                    }
                                                )
                    # request.env.cr.commit()
                    _logger.debug("\n\n\n\n\nventa_nueva_linea: %s", venta_nueva_linea)

                    # Ensamblando la venta
                    venta_nueva = {
                        'name': post['DocNum'], 
                        'origin': post['DocNum'],
                        # 'priority': '0', 
                        'partner_id': cliente_id, 
                        # 'partner_ref': False, 
                        'currency_id': 2, 
                        'date_order': date_approve,
                        # 'date_approve': date_approve, 
                        # 'date_planned': '2021-04-23 10:00:00', 
                        # 'receipt_reminder_email': False, 
                        # 'reminder_date_before_receipt': 1, 
                        # 'notes': post['CardCode'], 
                        'user_id': uid,
                        'company_id': 1, 
                        'payment_term_id': 7, 
                        "fiscal_position_id":False,
                        "analytic_account_id":False,
                        "warehouse_id":1,
                        "incoterm":False,
                        "picking_policy":"direct",
                        "commitment_date":False,
                        "campaign_id":False,
                        "medium_id":False,
                        "source_id":False,
                        "signed_by":False,
                        "signed_on":False,
                        "signature":False,
                        "note":"",
                        "team_id":1,
                        "require_signature":True,
                        "require_payment":True,
                        "client_order_ref":False,
                        "show_update_pricelist":False,
                        "pricelist_id":1,
                        "partner_invoice_id":cliente_id,
                        "partner_shipping_id":cliente_id,
                        "sale_order_template_id":False,
                        "validity_date":False,
                        'order_line': [(0, False, line) for line in venta_nueva_linea],
                        }

                    nueva_venta = request.env['sale.order'].sudo().create(venta_nueva)
                    
                    return {
                        "saleOrderId": nueva_venta.id,
                        "saleOrderName": nueva_venta.name,
                        "Token": as_token,
                        "RespCode":0,
                        "RespMessage":"OV recibidas correctamente",
                        "json_recibido":post
                    }
                else:
                    res['error'] = "Estructura no Valida"
                    res['Token'] = as_token
                    res_json = json.dumps(res)
                    return res_json
            else:
                res['error'] = "Autenticación fallida"
                res['Token'] = as_token
                res_json = json.dumps(res)
                return res_json
        except Exception as e:
            return {
                    "Token": as_token,
                    "RespCode":-1,
                    "RespMessage": e
                }

    @http.route(['/tpco/odoo/ws023',], auth="public", type="json", method=['POST'], csrf=False)
    def WS023(self, **post):
        post = yaml.load(request.httprequest.data)
        res = {}
        token = uuid.uuid4().hex
        try:
            myapikey = request.httprequest.headers.get("Authorization")
            if myapikey == "123":
                res['token'] = token
                # request.session.logout()
                es_valido = self.validar_json(post, esquema=as_estructuras.esquema_ws023)

                if es_valido:
                    vals_picking = {}
                    for linea in post['params']:
                        docdate = post['params']['DocDate'].replace("T"," ")
                        sp = request.env['stock.picking']
                        sp_search = sp.sudo().search([('origin', '=', post['params']['DocNum'])])
                        if not sp_search:
                            #se seleccionan las ubicaciones si no esxiste se crea y se retorna el ID
                            slo = self.as_get_id('stock.location',post['params']['WarehouseCodeOrigin'])
                            sld = self.as_get_id('stock.location',post['params']['WarehouseCodeDestination'])
                            picking_type_id = request.env['stock.picking.type'].sudo().search([('default_location_src_id', '=', slo)])
                            picking = request.env['stock.picking'].sudo().create({
                                    'location_id': slo,
                                    'date': docdate,
                                    'date_done': docdate,
                                    'location_dest_id': sld,
                                    'origin': post['params']['DocNum'],
                                    'picking_type_id': picking_type_id.id,
                                    "company_id": request.env.user.company_id.id,
                                })
                                # move from shelf1
                            for move in post['params']['DatosProdOC']:
                                uom_id = self.as_get_uom_id('uom.uom',move)
                                if not uom_id:
                                    return {
                                        "Token": token,
                                        "RespCode": 0,
                                        "RespMessage": "Unidad de Medida no existe" 
                                    }
                                product_id = self.as_get_product_id(move,uom_id)
                                move1 = request.env['stock.move'].sudo().create({
                                    'name': move['ItemDescription'],
                                    'location_id': slo,
                                    'location_dest_id': sld,
                                    'picking_id': picking.id,
                                    'product_id': product_id,
                                    'product_uom': uom_id,
                                    'product_uom_qty': move['Quantity'],
                                    "company_id": request.env.user.company_id.id,
                                })
                                for move_line in move['Detalle']:
                                    lot_id = self.as_get_lot_id('stock.production.lot',move_line,product_id)
                                    move_line1 =request.env['stock.move.line'].sudo().create({
                                        'picking_id': move1.picking_id.id,
                                        'move_id': move1.id,
                                        'product_id': product_id,
                                        'qty_done': move_line['Quantity'],
                                        'product_uom_id': uom_id,
                                        'location_id': move1.location_id.id,
                                        'location_dest_id': move1.location_dest_id.id,
                                        'lot_id': lot_id,
                                        "company_id": request.env.user.company_id.id,
                                    })
                                picking.action_confirm()
                        else:
                            return {
                                    "Token": token,
                                    "RespCode": 0,
                                    "RespMessage": "OT ya existe " +str(sp_search.name) 
                                }
                    return {
                        "Token": token,
                        "RespCode": 0,
                        "RespMessage": "OT recibidas correctamente "+str(picking.name)
                    }
                else:
                    return {
                        "Token": token,
                        "RespCode": -2,
                        "RespMessage": "Error de validación en mensaje de entrada"
                    }
            else:
                return {
                    "Token": token,
                    "RespCode": -2,
                    "RespMessage": "Error de validación en mensaje de entrada"
                }

        except Exception as e:
            return {
                "Token": token,
                "RespCode": -1,
                "RespMessage": "Error de conexión",
                "error": e.args
            }

        
    def as_get_id(self,model,value):
        rw = request.env[model].sudo().search([('name','=',value)])
        rw_id = 0
        if rw:
            rw_id = rw.id
        else:
            rw_new_id = request.env[model].sudo().create({"name": value,})
            rw_id = rw_new_id.id
        return rw_id

    def as_get_uom_id(self,model,value):
        rw = request.env[model].sudo().search([('name','ilike',value['MeasureUnit'])],limit=1)
        rw_id = False
        if rw:
            rw_id = rw.id
        return rw_id

    def as_get_lot_id(self,model,value,product_id):
        rw = request.env[model].sudo().search([('name','=',value['DistNumber'])])
        rw_id = 0
        if rw:
            rw_id = rw.id
        else:
            rw_new_id = request.env[model].sudo().create({
                "name": value['DistNumber'],
                "product_id": product_id,
                "company_id": request.env.user.company_id.id,
                "create_date": value['DateProduction'].replace("T"," "),
                "expiration_date": value['DateExpiration'].replace("T"," "),
                })
            rw_id = rw_new_id.id
        return rw_id
        
    def as_get_product_id(self,linea,uom_id):
        producto = request.env['product.template']
        producto_search = producto.sudo().search([('default_code', 'ilike', linea['ItemCode'])])
        if producto_search.id:
            producto_id = producto_search.id
            product_product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', producto_id)])[0]
            product_product_id = product_product.id
        else:
            product_data = {
                "name": str(linea['ItemDescription']) or "",
                "type": "product",
                "categ_id": 1,
                "default_code": str(linea['ItemCode']) or "",
                "barcode": "",
                "list_price": 1,
                "standard_price": 1,
                "uom_id": uom_id,
                "uom_po_id": uom_id,
                "purchase_ok": True,
                "sale_ok": True,
                "tracking": 'lot',
                "company_id": request.env.user.company_id.id,
            }

            _logger.debug("\n\n\n\n\nproduct_data: %s", product_data)

            producto_nuevo = producto.sudo().create(product_data)
            producto_id = producto_nuevo.id
            product_product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', producto_id)])[0]
            product_product_id = product_product.id
        return product_product_id

    def validar_json(self, el_json, esquema):
        try:
            validate(instance=el_json, schema=esquema)
        except jsonschema.exceptions.ValidationError as err:
            return False
        return True
    
def as_convert(txt,digits=50,is_number=False):
    if is_number:
        num = re.sub("\D", "", txt)
        if num == '':
            return 0
        return int(num[0:digits])
    else:
        return txt[0:digits]           