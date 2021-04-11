# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def as_get_date_lote(self):
        if self.lot_name:
            return self.lot_name
        else:
            return self.lot_id.name

    def as_barcode_1(self):
        codigo = '(01)'+str(self.product_id.barcode)+'(10)'+str(self.as_get_date_lote())+'(91)'+str(self.product_id.default_code)
        return codigo

    def as_barcode_2(self):
        codigo = '(37)'+str(self.product_id.as_cantidad_unidades)+'(3101)'+str(self.qty_done)+'(15)'+str(self.expiration_date.strftime('%d%m%Y'))
        return codigo

class StockMoveLine(models.Model):
    _inherit = 'stock.move'

    def as_get_date_lote(self):
        lotes = ''
        for lot in self.lot_ids:
            lotes+=str(lot.name)
        return lotes

    def as_barcode_1(self):
        fecha_vencimiento = ''
        for line in self.move_line_ids:
            if line.expiration_date:
                fecha_vencimiento = line.expiration_date.strftime('%d%m%Y')
        codigo = '(10)'+str(self.as_get_date_lote())+'(91)'+str(self.product_id.default_code)+'(37)'+str(self.product_id.as_cantidad_unidades)+'(3101)'+str(self.quantity_done)+'(11)'+str(fecha_vencimiento)
        return codigo

    def as_fecha_vencimiento(self):
        fecha_vencimiento = ''
        for line in self.move_line_ids:
            if line.expiration_date:
                fecha_vencimiento = line.expiration_date.strftime('%d%m%Y')
        return fecha_vencimiento
