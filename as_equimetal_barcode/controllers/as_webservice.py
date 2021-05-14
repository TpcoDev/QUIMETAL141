# -*- coding: utf-8 -*-
from odoo.tools.translate import _
import json
import sys
import uuid
from odoo import http
from odoo.http import request, Response
import jsonschema
from jsonschema import validate
import json
import logging
import biip
_logger = logging.getLogger(__name__)
from datetime import timedelta, datetime, date


class as_barcode_quimetal(http.Controller):

    @http.route(['/quimetal/barcode'], auth="public", type="http",csrf=False)
    def barcode(self, **post):
        # order_reference = row_id
        barcode = post.get('barcode') or None
        barcode = barcode.replace("|","\x1d")
        # barcode = '10455\x1d91MPFIL093\x1d3721\x1d310000031517210308'
        try:
            result =  request.env['gs1_barcode'].sudo().decode(barcode)
            # result = biip.parse(barcode,separator_chars=('\x1d'))
            # lote = result.gs1_message.get(ai="10").value
            # product_code = result.gs1_message.get(ai="91").value
            lote = result['10']
            product_code = result['91']
            product_id = request.env['product.product'].sudo().search([('default_code','=',product_code)],limit=1)
            if not product_id:
                vals2={
                    'type':True,
                    'lote': lote,
                    'barcode': barcode,
                    'product': False,
                }
            else:
                lot_id = request.env['stock.production.lot'].sudo().search([('name','=',lote)],limit=1)
                if lot_id:
                    vals2={
                        'type':True,
                        'lote': lote,
                        'barcode': barcode,
                        'product': product_code,
                    }
                    lot_id.message_post(body = barcode)
                else:
                    lot_id = request.env['stock.production.lot'].sudo().create({
                            'product_id': product_id.id,
                            'name': lote.name,
                            'company_id': request.env.company.id,
                        })
                    vals2={
                        'type':True,
                        'lote': lot_id.name,
                        'barcode': barcode,
                        'product': product_code,
                    }      
                    lot_id.message_post(body = barcode)     
        except Exception as e:
            vals2={
                'type':False,
                'barcode': barcode,
            
            }
        log_id = request.env['as.barcode.log'].sudo().create({
                            'name': barcode,
                            'as_json':json.dumps(vals2),
                    })
        # print (result.gs1_message)
        return json.dumps(vals2)

