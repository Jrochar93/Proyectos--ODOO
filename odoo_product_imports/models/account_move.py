# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    purchase_import_id = fields.Many2one(
        'purchase.imports',
        string='Import'
    )

    def button_create_landed_costs(self):
        """Create a `stock.landed.cost` record associated to the account move of `self`, each
        `stock.landed.costs` lines mirroring the current `account.move.line` of self.
        """
        self.ensure_one()
        landed_costs_lines = self.line_ids.filtered(lambda line: line.is_landed_costs_line)
        picking_ids = []
        for po in self.purchase_import_id.purchase_order_ids:
            for pi in po.picking_ids:
                picking_ids = [(4, pi.id)]
         
        landed_costs = self.env['stock.landed.cost'].create({
            'vendor_bill_id': self.id,
            'purchase_import_id': self.purchase_import_id.id,
            'picking_ids': picking_ids,
            'cost_lines': [(0, 0, {
                'product_id': l.product_id.id,
                'name': l.product_id.name,
                'account_id': l.product_id.product_tmpl_id.get_product_accounts()['stock_input'].id,
                #'price_unit': l.currency_id._convert(l.price_subtotal, l.company_currency_id, l.company_id, l.move_id.date),
                'price_unit': l.currency_id._convert_per_document(l.price_subtotal, l.company_currency_id, l.company_id, l.move_id.date, l.move_id.invoice_exchange_rate) if l.move_id.invoice_exchange_rate > 1 and l.move_id.invoice_has_exchange_rate else l.currency_id._convert(l.price_subtotal, l.company_currency_id, l.company_id, l.move_id.date),
                'split_method': l.product_id.split_method_landed_cost or 'equal',
            }) for l in landed_costs_lines],
        })
        action = self.env["ir.actions.actions"]._for_xml_id("stock_landed_costs.action_stock_landed_cost")
        return dict(action, view_mode='form', res_id=landed_costs.id, views=[(False, 'form')])
