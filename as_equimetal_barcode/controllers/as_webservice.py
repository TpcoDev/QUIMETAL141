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
import yaml
import logging
import biip
_logger = logging.getLogger(__name__)
from datetime import timedelta, datetime, date


class as_barcode_quimetal(http.Controller):

    @http.route(['/quimetal/barcode'], auth="public", type="http",csrf=False)
    def barcode(self, **post):
        # order_reference = row_id
        barcode = post.get('barcode') or None
        # barcode = '10455 91MPFIL093 3721 310000031517210308'
        try:
            result = biip.parse(barcode,separator_chars=(' '))
            lote = result.gs1_message.get(ai="10").value
            product_code = result.gs1_message.get(ai="91").value
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
        except Exception as e:
            vals2={
                'type':False,
                'barcode': barcode,
            
            }
       
        # print (result.gs1_message)
        return json.dumps(vals2)

