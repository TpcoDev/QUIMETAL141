# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import logging
from psycopg2 import Error, OperationalError
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

_logger = logging.getLogger(__name__)


class as_stock_production_lot(models.Model):
    _inherit = "stock.production.lot"

    @api.model_create_multi
    def create(self, vals_list):
        res = super(as_stock_production_lot, self).create(vals_list)
        for lot in res:
            lot.name = str(lot.name).upper()
        return res

    # @api.depends('name')
    # def as_get_name(self):
    #     for lot in self:
    #         lot.name  = str(lot.name).upper()

class as_stock_move_line(models.Model):
    _inherit = "stock.move.line"

    @api.onchange('lot_name')
    def as_name_lot(self):
        for line in self:
            line.lot_name = str(line.lot_name).upper()

    @api.onchange('product_id', 'product_uom_id')
    def _onchange_product_id(self):
        as_vencimiento = self.self.expiration_date
        res = super(as_stock_move_line, self)._onchange_product_id()
        self.expiration_date = as_vencimiento
        return res

