# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    
    purchase_import_id = fields.Many2one(
        'purchase.imports',
        string='Import'
    )
    
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({
            'purchase_import_id': self.purchase_import_id.id
        })
        return res
