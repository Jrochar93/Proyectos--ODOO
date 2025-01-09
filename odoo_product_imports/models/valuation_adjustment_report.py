# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, tools, api,_
from datetime import datetime
from odoo.osv import expression
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)


class ReportValuationAdjustmentLines(models.Model):
    _name = 'report.valuation.adjustment.lines'
    _auto = False
    _description = 'This is the lines in the Purchase Imports Valuation Adjustment Lines report'

    
    #name = fields.Char('Referencia Interna Odoo',readonly=True)
    product_id = fields.Many2one('product.product','Product',readonly=True)
    quantity = fields.Float('Cantidad',readonly=True)
    former_cost = fields.Float('Valor Original',readonly=True)
    final_cost = fields.Float('Nuevo Valor',readonly=True)
    additional_landed_cost = fields.Float('Costos en el Destino',readonly=True)
    purchase_import_id = fields.Many2one('purchase.imports', 'Importación')
    price_unit = fields.Float('precio Unitario')
    

    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_valuation_adjustment_lines')
        query = """
        CREATE or REPLACE VIEW report_valuation_adjustment_lines AS(

        select
        --sval.name as name,
        row_number() OVER (ORDER BY slc.purchase_import_id, sval.product_id) as id,
        sval.product_id as product_id,
        --sum(sval.quantity) as quantity,
        max(sval.quantity) as quantity,
        min(sval.former_cost) as former_cost,
        --max(sval.final_cost) as final_cost,
        min(sval.former_cost) + sum(sval.additional_landed_cost) as final_cost,
        sum(sval.additional_landed_cost) as additional_landed_cost,
        slc.purchase_import_id as purchase_import_id,
        (min(sval.former_cost) + sum(sval.additional_landed_cost)) / max(sval.quantity) as price_unit
        from stock_valuation_adjustment_lines sval
        left join stock_landed_cost slc on slc.id = sval.cost_id
        where 1=1
        group by slc.purchase_import_id, sval.product_id
        );
        """
        self.env.cr.execute(query)
        #(select to_char(mp.date_planned_start,'mm')) as month,
