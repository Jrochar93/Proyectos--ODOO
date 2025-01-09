# -*- coding: utf-8 -*-

import json
import time
from ast import literal_eval
from collections import defaultdict
from datetime import date
from itertools import groupby
from operator import attrgetter, itemgetter
from collections import defaultdict

from odoo import SUPERUSER_ID, _, api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
from odoo.tools.misc import format_date

import logging

_logger = logging.getLogger(__name__)


class StockPick(models.Model):
    _inherit = 'stock.picking'

    purchase_import_id = fields.Many2one(
        'purchase.imports',
        string='Import'
    )

    def write(self, vals):
        res = super(StockPick, self).write(vals)
        active_model = self.env['stock.picking'].browse(self.env.context.get('active_model'))
        #if active_model == 'stock.picking':
        if self.env.context.get('active_model') == 'stock.picking':
            _logger.info('Inicio funcion Confirma los costos en el destino cuando se valida el último picking eniendo en cuenta que el estado del picking es un campo computado.')
            active_id = self.env['stock.picking'].browse(self.env.context.get('active_id'))
            if active_id:
                if 'date_done' in vals and vals.get('date_done'):
                    """
                    Confirma los costos en el destino cuando se valida el último picking
                    Teniendo en cuenta que el estado del picking es un campo computado.
                    """
                    purchase_import_id = active_id.purchase_import_id
                    slc_active = None
                    for slc in purchase_import_id.stock_landed_cost_ids:
                        for pick in slc.picking_ids:
                            if pick.id == active_id.id:
                                slc_active = slc

                    if slc_active:
                        count = 0
                        for picking in slc_active.picking_ids:
                            if picking.state not in ('done','cancel'):
                                count+=1
                        if count == 1:
                            purchase_import_id.compute_stock_landed_cost()
                            _logger.info('compute_stock_landed_cost')
                            purchase_import_id.comfirm_stock_landed_cost()
                            _logger.info('comfirm_stock_landed_cost')
                            

            _logger.info('Fin funcion Confirma los costos en el destino')

            

        return res
