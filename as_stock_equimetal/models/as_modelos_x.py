# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Product_template(models.Model):
    _inherit = 'product.template'

    as_contenido_envase = fields.Integer(string = 'Contenido envase')
    as_cantidad_envase = fields.Integer(string = 'Cantidad de envase')
    as_cantidad_unidades = fields.Integer(string = 'Cantidad unidades')