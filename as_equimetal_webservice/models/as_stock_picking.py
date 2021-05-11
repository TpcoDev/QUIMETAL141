# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.http import request
import requests, json

class AsStockPicking(models.Model):
    _inherit = 'stock.picking'

    as_enviado_sap = fields.Boolean(string='Enviado a SAP')

    def action_picking_sap(self):
        try:
            token = self.as_get_apikey(self.env.user.id)
            if token != None:
                headerVal = {}
                # headerVal = {'Authorization': token}
                requestBody = {
                    'res_id': self.name,
                }
                credentials = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                URL=credentials+'/tpco/odoo/ws005'
                r = requests.post(URL, json=requestBody, headers=headerVal)
                if r.ok:
                    text = r.text
                    info = json.loads(text)
                    if info['result']['RespCode'] == 0:
                        body =  "<b style='color:green'>EXITOSO ("+'WS005'+")!: </b><br>"
                        body += '<b>'+info['result']['RespMessage']+'</b>'                        
                    else:
                        body =  "<b style='color:red'>ERROR ("+'WS005'+")!: </b><br>"
                        body += '<b>'+info['result']['RespMessage']+'</b>'
                else:
                    body =  "<b style='color:red'>ERROR ("+'WS005'+")!:</b><br> <b> No aceptado por SAP</b><br>" 
            else:
                body =  "<b style='color:red'>ERROR ("+'WS005'+")!: </b><br> <b>El Token no encontrado!</b>"
        except Exception as e:
            body =  "<b style='color:red'>ERROR ("+'WS005'+")!: </b><b>"+ str(e)+"</b><br>"
            
        self.message_post(body = body)
        
    def as_get_apikey(self,user_id):
        query = self.env.cr.execute("""select key from res_users_apikeys where user_id ="""+str(user_id)+"""""")
        result = self.env.cr.fetchall()
        return result[0][0]
