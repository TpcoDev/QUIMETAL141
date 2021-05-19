# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockMoveLine(models.Model):
    _inherit = 'stock.picking'

    partner_id = fields.Many2one(  'res.partner', 'Contact', check_company=True, states={'cancel': [('readonly', True)]})

    def action_picking_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'stock.picking',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def _find_mail_template(self, force_confirmation_template=False):
        if self.location_id.as_plantilla == '1':
            template_id = self.env['ir.model.data'].xmlid_to_res_id('as_stock_equimetal.stock_picking_mail_templateD', raise_if_not_found=False)
        else:
            template_id = self.env['ir.model.data'].xmlid_to_res_id('as_stock_equimetal.stock_picking_mail_templateO', raise_if_not_found=False)

        return template_id