# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.http import request
import requests, json

address_webservice = {
    'WS005':'/tpco/odoo/ws005',
    'WS004':'/tpco/odoo/ws004',
    'WS006':'/tpco/odoo/ws006',
    'WS099':'/tpco/odoo/ws099',
    'WS018':'/tpco/odoo/ws018',
    'WS021':'/tpco/odoo/ws021',
}

class AsStockPicking(models.Model):
    _inherit = 'stock.picking'

    as_enviado_sap = fields.Boolean(string='Enviado a SAP')
    as_webservice = fields.Selection(
        [
            ('WS005','WS005'),
            ('WS004','WS004'),
            ('WS006','WS006'),
            ('WS099','WS099'),
            ('WS018','WS018'),
            ('WS021','WS021'),
        ],
        string="Webservice",
    )
    as_ot_sap = fields.Integer(string='OT SAP')
    as_num_factura = fields.Char(string='Num de Factura')

    def action_picking_sap(self):
        webservice = self.as_webservice
        try:
            token = self.as_get_apikey(self.env.user.id)
            if token != None:
                headerVal = {}
                # headerVal = {'Authorization': token}
                requestBody = {
                    'res_id': self.name,
                }
                credentials = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                URL=credentials+address_webservice[webservice]
                r = requests.post(URL, json=requestBody, headers=headerVal)
                if r.ok:
                    text = r.text
                    info = json.loads(text)
                    if info['result']['RespCode'] == 0:
                        body =  "<b style='color:green'>EXITOSO ("+webservice+")!: </b><br>"
                        body += '<b>'+info['result']['RespMessage']+'</b>'                        
                    else:
                        body =  "<b style='color:red'>ERROR ("+webservice+")!: </b><br>"
                        body += '<b>'+info['result']['RespMessage']+'</b>'
                else:
                    body =  "<b style='color:red'>ERROR ("+webservice+")!:</b><br> <b> No aceptado por SAP</b><br>" 
            else:
                body =  "<b style='color:red'>ERROR ("+webservice+")!: </b><br> <b>El Token no encontrado!</b>"
        except Exception as e:
            body =  "<b style='color:red'>ERROR ("+webservice+")!: </b><b>"+ str(e)+"</b><br>"
            
        self.message_post(body = body)
        
    def as_get_apikey(self,user_id):
        query = self.env.cr.execute("""select key from res_users_apikeys where user_id ="""+str(user_id)+"""""")
        result = self.env.cr.fetchall()
        return result[0][0]

    def as_assemble_picking_json(self,webservice):
        picking_line = []
        vals_picking_line = {}
        for picking in self:
            #se ensamblan los stock.move
            for move_stock in picking.move_ids_without_package:
                move = []
                vals_move_line = {}
                for move_line in move_stock.move_line_ids:
                    vals_move_line.update({
                        "distNumber": move_line.lot_id.name,
                        "quantity": move_line.qty_done,
                        "dateProduction": str(move_line.lot_id.create_date.strftime('%Y-%m-%dT%H:%M:%S')),
                        "dateExpiration":  str(move_line.lot_id.create_date.strftime('%Y-%m-%dT%H:%M:%S')),
                    })
                    move.append(vals_move_line)
                vals_picking_line.update({
                    "itemCode": move_stock.product_id.default_code,
                    "itemDescription": move_stock.product_id.name,
                    "quantity": move_stock.quantity_done,
                    "measureUnit": move_stock.product_uom.name,
                    "lote": move,
                })
                picking_line.append(vals_picking_line)
            if webservice == 'WS005':
                vals_picking = {
                    "docNum": str(picking.name),
                    "docDate": str(picking.date_done.strftime('%Y-%m-%dT%H:%M:%S')),
                    "docNumSAP": int(picking.as_ot_sap),
                    "warehouseCodeOrigin": picking.location_id.name,
                    "warehouseCodeDestination": picking.location_dest_id.name,
                    "cardCode": picking.partner_id.vat,
                    "cardName": picking.partner_id.name,
                    "detalle": picking_line,
                }
            elif webservice in ('WS004'):
                vals_picking = {
                    "docNum": str(picking.name),
                    "docNumSAP": str(picking.as_ot_sap),
                    "docDate": str(picking.date_done.strftime('%Y-%m-%dT%H:%M:%S')),
                    "warehouseCodeOrigin": picking.location_id.name,
                    "warehouseCodeDestination": picking.location_dest_id.name,
                    "detalle": picking_line,
                }
            elif webservice in ('WS006','WS099'):
                vals_picking = {
                    "docNum": str(picking.name),
                    "docDate": str(picking.date_done.strftime('%Y-%m-%dT%H:%M:%S')),
                    "warehouseCodeOrigin": picking.location_id.name,
                    "warehouseCodeDestination": picking.location_dest_id.name,
                    "detalle": picking_line,
                }
            elif webservice in ('WS018'):
                vals_picking = {
                    "docNum": str(picking.name),
                    "DocDueDate": str(picking.date_done.strftime('%Y-%m-%dT%H:%M:%S')),
                    "warehouseCodeOrigin": picking.location_id.name,
                    "warehouseCodeDestination": picking.location_dest_id.name,
                    "cardCode": picking.partner_id.vat,
                    "cardName": picking.partner_id.name,
                    "numFactura": str(picking.as_num_factura),
                    "numGuiaDesp": str(picking.l10n_latam_document_number),
                    "numOVAsoc": picking.origin,
                    "detalle": picking_line,
                }
            elif webservice in ('WS021'):
                vals_picking = {
                    "docNum": str(picking.name),
                    "docDate": str(picking.date_done.strftime('%Y-%m-%dT%H:%M:%S')),
                    "warehouseCodeDestination": picking.location_dest_id.name,
                    "numFactura": str(picking.as_num_factura),
                    "numGuiaDesp": str(picking.l10n_latam_document_number),
                    "detalle": picking_line,
                }
            self.message_post(body = vals_picking)
        return vals_picking