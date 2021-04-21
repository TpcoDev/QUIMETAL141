# -*- coding: utf-8 -*-
from odoo.tools.translate import _
from odoo import http
from odoo import http
from odoo.http import request
from tabulate import tabulate
from datetime import datetime
from bs4 import BeautifulSoup
import json
import sys
import uuid
import yaml
import logging
_logger = logging.getLogger(__name__)

from werkzeug import urls
from werkzeug.wsgi import wrap_file

# class as_webservice(http.Controller):

#     def get_user_access_token(self):
#         return uuid.uuid4().hex

#     @http.route(['/api/ws001ok',], auth="public", type="json", method=['POST'], csrf=False)
#     def request_WS001(self, **post):
#         post = yaml.load(request.httprequest.data)
#         res = {}
#         token = uuid.uuid4().hex
#         try:
#             uid = request.session.authenticate(post['db'], post['login'], post['password'])
#             if uid:
#                 user = request.env['res.users'].sudo().browse(uid)
#                 res['token'] = token
#                 request.session.logout()
#                 return {			
#                     "Token": token,				
#                     "RespCode":0,				
#                     "RespMessage":"OC recibidas correctamente",
#                     "json_recibido":json.dumps(post)		
#                 }
#             else:
#                 res['error'] = "Login o Password erroneo"
#                 res_json = json.dumps(res)

#                 return res_json
#         except:
#             return {			
#                     "Token": token,		
#                     "RespCode":-1,		
#                     "RespMessage":"Error de conexión"		
#                 }

class as_webservice_quimetal(http.Controller):

    # WS001, de SAP a ODOO
    @http.route(['/tpco/odoo/ws001',], auth="public", type="json", method=['POST'], csrf=False)
    def WS001(self, **post):
        post = yaml.load(request.httprequest.data)
        res = {}
        token = uuid.uuid4().hex
        try:
            uid = request.session.authenticate(post['db'], post['login'], post['password'])


            if uid:
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

                    # Tratamiento de producto
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
                    producto_uom_search = producto_uom.sudo().search([('name', 'ilike', linea['MeasureUnit'])])
                    producto_uom_id = 0
                    if producto_uom_search.id:
                        producto_uom_id = producto_uom_search.id

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
                    'user_id': 1,
                    'company_id': 1, 
                    'payment_term_id': 7, 
                    'fiscal_position_id': False,
                    'order_line': [(0, False, line) for line in compra_nueva_linea],
                    }

                nueva_compra = request.env['purchase.order'].sudo().create(compra_nueva)
                
                res['token'] = token
                request.session.logout()
                return {
                    "purchase_id": nueva_compra.id,
                    "purchase_name": nueva_compra.name,
                    "Token": token,
                    "RespCode":0,
                    "RespMessage":"OC creada correctamente",
                    "json_recibido":post
                }
            else:
                res['error'] = "Login o Password erroneo"
                res['Token'] = token
                res_json = json.dumps(res)
                return res_json
        except Exception as e:
            return {
                    "Token": token,
                    "RespCode":-1,
                    "RespMessage": e
                }

def as_convert(txt,digits=50,is_number=False):
    if is_number:
        num = re.sub("\D", "", txt)
        if num == '':
            return 0
        return int(num[0:digits])
    else:
        return txt[0:digits]           