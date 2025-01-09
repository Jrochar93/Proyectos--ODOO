# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    purchase_import_id = fields.Many2one(
        'purchase.imports',
        string='Import'
    )

