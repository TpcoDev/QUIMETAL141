# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PickingType(models.Model):
    _inherit = "stock.picking.type"

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
    as_send_automatic = fields.Boolean(string='Enviar Correo al confirmar')