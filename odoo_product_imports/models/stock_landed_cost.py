# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero
import logging

_logger = logging.getLogger(__name__)


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    purchase_import_id = fields.Many2one(
        'purchase.imports',
        string='Import'
    )

    @api.onchange('purchase_import_id')
    def _onchange_purchase_import_id(self):
        #import_id = self.env['purchase.imports'].browse(self.purchase_import_id)
        self.picking_ids = [(5,)]
        for po in self.purchase_import_id.purchase_order_ids:
            for pi in po.picking_ids:
                self.picking_ids = [(4, pi.id)]

    @api.onchange('vendor_bill_id')
    def _onchange_vendor_bill_id(self):
        for rec in self:
            if rec.vendor_bill_id.purchase_import_id:
                rec.purchase_import_id = rec.vendor_bill_id.purchase_import_id.id
                rec._onchange_purchase_import_id()

    def button_validate(self):
        # Llamar a la super para realizar la validación normal
        res = super(StockLandedCost, self).button_validate()
        
        for cost in self:
            # Verificar si todos los picking están en estado 'done'
            if any(picking.state != 'done' for picking in cost.picking_ids):
                raise UserError(_('Los movimientos de inventario deben estar en estado terminado'))

            # Verificar si algún producto tiene volumen 0.0
            for pick in cost.picking_ids:
                for sm in pick.move_ids_without_package:
                    if sm.product_id.volume == 0.0:
                        raise UserError(
                            _('No es posible validar debido al producto %s que tiene un volumen igual a cero.')
                            % (sm.product_id.product_tmpl_id.name)
                        )
                        
            # Asignar la importación a los asientos contables creados
            for account_move in cost.account_move_id:  # El asiento contable asociado al costo
                if cost.purchase_import_id:  # Usamos purchase_import_id en lugar de purchase_id
                    # Asignar la importación desde el pedido de compra si está disponible
                    account_move.import_reference = cost.purchase_import_id.name

        return res


    def get_valuation_lines(self):
        self.ensure_one()
        lines = []
        detail_msg = ''
        for move in self._get_targeted_move_ids():
            # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
            if move.product_id.cost_method not in ('fifo', 'average') or move.state == 'cancel' or not move.product_qty:
                detail_msg = ' - '.join([move.name, move.product_id.display_name, move.picking_id.name])
                continue
            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                'quantity': move.product_qty,
                'former_cost': sum(move.stock_valuation_layer_ids.mapped('value')),
                'weight': move.product_id.weight * move.product_qty,
                'volume': move.product_id.volume * move.product_qty
            }
            lines.append(vals)

        if not lines:
            target_model_descriptions = dict(self._fields['target_model']._description_selection(self.env))
            raise UserError(_("You cannot apply landed costs on the chosen %s(s). Landed costs can only be applied for products with FIFO or average costing method. %s", target_model_descriptions[self.target_model], detail_msg))
        return lines


class StockLandedCostLines(models.Model):
    _inherit = 'stock.landed.cost.lines'

    purchase_import_id = fields.Many2one(
        'purchase.imports',
        string='Import',
        related='cost_id.purchase_import_id',
        readonly=True,
        store=True
    )

class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'


    purchase_import_id = fields.Many2one(
        'purchase.imports',
        string='Import',
        related='cost_id.purchase_import_id',
        readonly=True,
        store=True
    )
