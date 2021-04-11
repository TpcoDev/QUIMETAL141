# -*- coding: utf-8 -*-
from odoo.tools.translate import _
from odoo import http
from odoo import http
from odoo.http import request
from tabulate import tabulate
from bs4 import BeautifulSoup
import json
import sys
import uuid
import yaml
import logging
_logger = logging.getLogger(__name__)

from werkzeug import urls
from werkzeug.wsgi import wrap_file

class as_webservice(http.Controller):

    def get_user_access_token(self):
        return uuid.uuid4().hex

    @http.route(['/api/ws001ok',], auth="public", type="json", method=['POST'], csrf=False)
    def request_WS001(self, **post):
        post = yaml.load(request.httprequest.data)
        res = {}
        token = uuid.uuid4().hex
        try:
            uid = request.session.authenticate(post['db'], post['login'], post['password'])
            if uid:
                user = request.env['res.users'].sudo().browse(uid)
                res['token'] = token
                request.session.logout()
                return {			
                    "Token": token,				
                    "RespCode":0,				
                    "RespMessage":"OC recibidas correctamente",
                    "json_recibido":json.dumps(post)		
                }
            else:
                res['error'] = "Login o Password erroneo"
                res_json = json.dumps(res)

                return res_json
        except:
            return {			
                    "Token": token,		
                    "RespCode":-1,		
                    "RespMessage":"Error de conexión"		
                }		