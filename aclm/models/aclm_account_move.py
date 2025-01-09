from odoo import api, fields, models

class AclmAccountMove(models.Model):
    _inherit = "account.move"

    partner_x_studio_cod_de_marco = fields.Char(related="partner_id.x_studio_cod_de_marco")
    custom_name = fields.Char(compute="_compute_custom_name", store=True)
    partner_custom_name = fields.Char(related='partner_id.x_studio_holding', store=True, string="Cliente")

    @api.depends('name', 'partner_x_studio_cod_de_marco')
    def _compute_custom_name(self):
        for rec in self:
            if rec.partner_x_studio_cod_de_marco and rec.name:
                rec.custom_name = rec.name.replace(rec.partner_x_studio_cod_de_marco, '').strip()
            else:
                rec.custom_name = rec.name