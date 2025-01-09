# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, tools, api,_
from datetime import datetime
from odoo.osv import expression
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)


class ReportValuationAdjustmentLines2(models.Model):
    _name = 'report.valuation.adjustment.lines2'
    _auto = False
    _description = 'This is the lines in the Purchase Imports Valuation Adjustment Lines report'


    #name = fields.Char('Referencia Interna Odoo',readonly=True)
    product_id = fields.Many2one('product.product','Product',readonly=True)
    quantity = fields.Float('Cantidad',readonly=True)
    former_cost = fields.Float('Valor Original',readonly=True)
    final_cost = fields.Float('Nuevo Valor',readonly=True)
    additional_landed_cost = fields.Float('Costos en el Destino',readonly=True)
    purchase_import_id = fields.Many2one('purchase.imports', 'Importación')
    standard_price = fields.Float('Costo Estandar')
    price_unit = fields.Float('precio Unitario')


    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_valuation_adjustment_lines2')
        query = """
        CREATE or REPLACE VIEW report_valuation_adjustment_lines2 AS(
        
        select 
        max(subquery.id) as id,
        subquery.product_id as product_id,
        max(subquery.quantity) as quantity,
        min(subquery.former_cost) as former_cost,
        min(subquery.former_cost) + max(subquery.additional_landed_cost) as final_cost,
        max(subquery.additional_landed_cost) as additional_landed_cost,
        subquery.purchase_import_id as purchase_import_id,
        (min(subquery.former_cost) + max(subquery.additional_landed_cost)) / max(subquery.quantity) as price_unit,
        min(subquery.former_cost) / max(subquery.quantity) as standard_price
        from (
            select
            row_number() OVER (ORDER BY slc.purchase_import_id, sval.product_id) as id,
            sval.product_id as product_id,
            sum(sval.quantity) as quantity,
            sum(sval.former_cost) as former_cost,
            min(sval.former_cost) / imp.stock_landed_cost_count + sum(sval.additional_landed_cost) as final_cost,
            sum(sval.additional_landed_cost) as additional_landed_cost,
            slc.purchase_import_id as purchase_import_id,
            (sum(sval.former_cost) + sum(sval.additional_landed_cost)) / sum(sval.quantity) as price_unit,
            sval.cost_line_id as cost_line_id
            from stock_valuation_adjustment_lines sval
            left join stock_landed_cost slc on slc.id = sval.cost_id
            left join purchase_imports imp on imp.id = slc.purchase_import_id
            where 1=1
            group by slc.purchase_import_id, sval.product_id, imp.stock_landed_cost_count,sval.cost_line_id
        ) as subquery
        group by subquery.product_id,subquery.purchase_import_id);
        """
        self.env.cr.execute(query)
        #(select to_char(mp.date_planned_start,'mm')) as month,
