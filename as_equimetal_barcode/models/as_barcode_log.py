# -*- coding: utf-8 -*-
from odoo import models, fields, api,_

class StockProductionLor(models.Model):
    """"creado modelo para verificar que se esta scaneando"""
    _name = 'as.barcode.log'
    _description = 'Heredando modelo de lote'

    name = fields.Char(string='barcode')
    as_json = fields.Char(string='json respuesta')
