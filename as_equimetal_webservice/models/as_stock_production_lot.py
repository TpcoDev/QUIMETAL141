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

    @api.depends('name')
    def as_get_name(self):
        for lot in self:
            lot.name  = str(lot.name).upper()