# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.osv import expression
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)

class PurchaseImport(models.Model):
    _name = 'purchase.imports'
    _description = "Purchase Imports"
    
    
    READONLY_STATES = {
        'confirm': [('readonly', True)],
        'inprogress': [('readonly', True)],
        'cancel': [('readonly', True)],
        'close': [('readonly', True)],
        'deliver': [('readonly', True)],
    }
    
    name = fields.Char(
        'Name',
        required=True,
        default='New',
        index=True, 
        copy=False,
    )
    
    trading_id = fields.Many2one(
        'res.partner',
        string='Trading',
        required=True
    )
    supplier_importation_num = fields.Char(
        size=32,
        string="Reference"
    )

    date_origin = fields.Date(
        string='Estimated Date',
        required=True, 
    )
    date_realy = fields.Date(
        string='Actual Date'
    )

    date_out_origin = fields.Date(
        string='Estimated Date'
    )
    date_out_realy = fields.Date(
        string='Actual Date'
    )

    dates = fields.Date(
        string='Estimated Date',
        required=False,
    )
    dates_realy = fields.Date(
        string='Actual Date'
    )
    closing_date = fields.Date(
        string='Closing Date',
    )


    calculate_method = fields.Selection(
        selection=[
            ('price', 'By Price'),
            ('weight', 'By Weight')],
        required=False,
        string="Prorate Method"
    )
    incoterm_id = fields.Many2one(
        'account.incoterms',
        required=True,
        string='Incoterm'
    )
    origin = fields.Many2one(
        'stock.location',
        string='Origin'
    )
    destination = fields.Many2one(
        'stock.location',
        string="Destination"
    )
    caricom = fields.Boolean(
        string="Caricom"
    )
    value_flete = fields.Float(
        string="Freight"
    )
    flete_currency = fields.Float(
        string="Currency freight"
    )

    type_seguro = fields.Selection(
        selection=[
            ('price', 'Price'),
            ('porce', 'Percentage')],
            required=False,
            string="Insurance calculation",
    )


    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        required=True
    )
    date_cost = fields.Date(help="True in State is pending in this field", string="Statement date")
    currency_rate = fields.Float(help="True in State is pending in this field", string="Cost Rate")
    amount_total_weight = fields.Float(string="Total Weight")
    amount_total_products = fields.Float(string="Total Products")
    amount_total_products_adua = fields.Float(string="Total Customs Products")
    amount_total_transport = fields.Float(string="Total Transportation")
    amount_total_expenses = fields.Float(string="Total Other Expenses")
    amount_total_aranceles = fields.Float(string="Total Tariffs")
    amount_total_importation = fields.Float(string="Total Import")

    state = fields.Selection([
        ('draft', 'Draft'), 
        ('confirm', 'Confirmed'), 
        ('inprogress', 'In Progress'), 
        ('close','Closed'), 
        ('deliver', 'Delivered'), 
        ('cancel', 'Canceled')], default='draft', readonly=True)

    purchase_order_ids = fields.One2many('purchase.order', 'purchase_import_id')
    purchase_order_count = fields.Integer(compute="_compute_purchase_order_count")

    stock_picking_ids = fields.One2many('stock.picking', 'purchase_import_id')
    stock_pick_count = fields.Integer(compute='_compute_stock_picking_count')

    account_move_ids = fields.One2many('account.move', 'purchase_import_id')
    account_move_count = fields.Integer(compute='_compute_account_move_cont')
    account_payment_move_ids = fields.One2many('account.move', 'purchase_import_id', domain=[('payment_id', '!=', False)])

    account_payment_ids = fields.One2many('account.payment', 'purchase_import_id')
    import_advances_count = fields.Integer(compute='_compute_account_payment_cont')

    fob_invoice_count = fields.Integer(compute='_compute_fob_invoice_count')
    
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, states=READONLY_STATES, default=lambda self: self.env.company.id)
    
    
    
    #stock_landed_cost_line_ids = fields.One2many('purchase.imports.valuation.adjustment.lines', compute='_compute_stock_landed_cost_line_ids')
    stock_landed_cost_line_ids = fields.One2many('report.valuation.adjustment.lines', 'purchase_import_id', string='Productos')
    purchase_payment_move_ids = fields.One2many('account.payment', compute='_compute_purchase_payment_move_ids')
    stock_landed_cost_line2_ids = fields.One2many('report.valuation.adjustment.lines2', 'purchase_import_id', string='Productos')
    stock_landed_cost_ids = fields.One2many('stock.landed.cost', 'purchase_import_id')
    stock_landed_cost_count = fields.Integer('Número de Costos en el Destino', compute="_compute_stock_landed_cost_count", store=True)


    @api.onchange('date_cost','currency_id')
    def _onchange_date_cost_currency(self):
        if not self.currency_id:
            self.currency_rate = 1
        else:
            date = self.date_cost or self._context.get('date') or datetime.today()
            self.env['res.currency.rate'].flush(['rate', 'currency_id', 'company_id', 'name'])
            query = """SELECT c.id,
                COALESCE((SELECT r.rate FROM res_currency_rate r
                    WHERE r.currency_id = c.id AND r.name <= %s
                    AND (r.company_id IS NULL OR r.company_id = %s)
                    ORDER BY r.company_id, r.name DESC
                    LIMIT 1), 1.0) AS rate
                    FROM res_currency c
                WHERE c.id = %s"""
            company_obj = self.env['res.company'].browse(self.env.company.id)
            self._cr.execute(query, (date, company_obj.id, self.currency_id.id))
            currency_rates = dict(self._cr.fetchall())
            rate = currency_rates.get(self.currency_id.id) or 1.0
            if rate:
                self.currency_rate = 1 / rate if rate > 0 else 1


    @api.depends('stock_landed_cost_ids','stock_landed_cost_ids.cost_lines')
    def _compute_stock_landed_cost_count(self):
        for rec in self:
            rec.stock_landed_cost_count = 0
            for slc in rec.stock_landed_cost_ids:
                for cost in slc.cost_lines:
                    rec.stock_landed_cost_count += 1
            if not rec.stock_landed_cost_count:
                rec.stock_landed_cost_count = 1
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('trading_id', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
    
    @api.depends('purchase_order_ids')
    def _compute_purchase_payment_move_ids(self):
        self.purchase_payment_move_ids = [(5,)]
        list = []
        #for po in self.purchase_order_ids:
        #    for pay in po.payment_ids:
        #        list.append((4, pay.id))
        if list:
            self.purchase_payment_move_ids = list
        
    
    
    """
    @api.depends('name', 'trading_id')
    def name_get(self):
        result = []
        for pi in self:
            name = pi.name
            if pi.trading_id:
                name += ' (' + pi.trading_id + ')'
            result.append((pi.id, name))
        return result
    """
    
    
    """
    @api.depends('purchase_order_ids')
    def _compute_stock_landed_cost_line_ids(self):
        import_ids = self.env['stock.valuation.adjustment.lines'].search([('purchase_import_id', '=', self.id)])
        line_ids = []
        self.stock_landed_cost_line_ids = [(5,)]
        _logger.error('._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.._.')
        for line in import_ids:
            
            _logger.error('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq')
            valuation = {
                'name':line.cost_line_id.name,
                'product_id':line.product_id.id,
                'quantity':line.quantity,
                'former_cost':line.former_cost,
                'final_cost':line.final_cost,
                'additional_landed_cost':line.additional_landed_cost,
                'purchase_import_id': self.id,
            }
            _logger.error(valuation)
            #line_ids.append(valuation)
            _logger.error(line_ids)
            self.env['purchase.imports.valuation.adjustment.lines'].create(valuation)
            #self.stock_landed_cost_line_ids += sval
        return True
    """
        
    
    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        # Ensures default picking type and currency are taken from the right company.
        self_comp = self.with_company(company_id)
        if vals.get('name', 'New') == 'New':
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase.imports', sequence_date=seq_date) or '/'
        #vals, partner_vals = self._write_partner_values(vals)
        res = super(PurchaseImport, self_comp).create(vals)
        #if partner_vals:
        #    res.sudo().write(partner_vals)  # Because the purchase user doesn't have write on `res.partner`
        return res
    

    def set_to_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def set_to_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def set_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def set_to_inprogress(self):
        for rec in self:
            rec.state = 'inprogress'

    def set_to_close(self):
        for rec in self:
            
            if rec.currency_rate > 0: 
                rec.state = 'close'
                rec.closing_date = fields.Date.today()
            else:
                raise UserError('Debe registrar la TRM asociada a la importación')

    def action_purchase_quatation(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("purchase.purchase_rfq")
        action['domain'] = [
            ('purchase_import_id', '=', self.id),
        ]
        action['context'] = {'default_purchase_import_id':self.id,'default_partner_id' : self.trading_id.id}
        return action



    def _compute_purchase_order_count(self):
        count = self.env['purchase.order'].search_count([('purchase_import_id', '=', self.id)])
        self.purchase_order_count = count


    def action_operations_trans(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        picking_ids = self.purchase_order_ids.mapped('picking_ids').ids
        action['domain'] = [
            ('purchase_import_id', '=', self.id),
            ('id', 'in', picking_ids)
        ]
        action['context'] = {'purchase_import_id':self.id}
        return action

    def _compute_stock_picking_count(self):
        count = self.env['stock.picking'].search_count([('purchase_import_id', '=', self.id)])
        self.stock_pick_count = count

    def action_invoice_costs(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id('account.action_move_in_invoice_type')
        action['domain'] = [
            ('purchase_import_id', '=', self.id)
        ]
        action['context'] = {'default_purchase_import_id': self.id}
        return action

    def _compute_account_move_cont(self):
        count = self.env['account.move'].search_count([('purchase_import_id', '=', self.id)])
        self.account_move_count = count


    def action_import_advances(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id('account.action_account_payments_payable')
        action['domain'] = [
            ('purchase_import_id', '=', self.id)
        ]
        action['context'] = {'default_purchase_import_id': self.id}
        return action

    def _compute_account_payment_cont(self):
        #count = self.env['account.payment'].search_count([('purchase_import_id', '=', self.id)])
        self.import_advances_count = 0
        for pay in self.purchase_payment_move_ids:
            self.import_advances_count += 1

    def action_open_fob_invoices(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
        action['domain'] = [
            ('id', 'in', self.purchase_order_ids.mapped('order_line.invoice_lines.move_id').ids)
        ]
        action['context'] = {'default_purchase_import_id': self.id, 'default_partner_id': self.trading_id.id}
        return action

    def _compute_fob_invoice_count(self):
        count_id = self.env['purchase.imports'].name
        count = self.env['account.move'].search_count([('id', 'in', self.purchase_order_ids.mapped('order_line.invoice_lines.move_id').ids)])
        self.fob_invoice_count = count


    def comfirm_stock_landed_cost(self):
        #if not any(slc.state not in 'done' for slc in self.stock_landed_cost_ids):
        #    raise UserError('Todos los costos en destino se encuentran validados')

        for slc in self.stock_landed_cost_ids:
            slc.picking_ids = [(5,)]
            for po in slc.purchase_import_id.purchase_order_ids:
                for pi in po.picking_ids:
                    slc.picking_ids = [(4, pi.id)]
            slc.compute_landed_cost()
            if slc.state == 'draft':
                slc.button_validate()

                
    def compute_stock_landed_cost(self):
        #if not any(slc.state not in 'done' for slc in self.stock_landed_cost_ids):
        #    raise UserError('Todos los costos en destino se encuentran validados')

        for slc in self.stock_landed_cost_ids:
            slc.picking_ids = [(5,)]
            for po in slc.purchase_import_id.purchase_order_ids:
                for pi in po.picking_ids:
                    slc.picking_ids = [(4, pi.id)]
            slc.compute_landed_cost()

"""
class PurchaseImportValuationAdjustmentLines(models.Model):
    _name = 'purchase.imports.valuation.adjustment.lines'
    _description = "Purchase Imports Valuation Adjustment Lines"
    
    
    purchase_import_id = fields.Many2one('purchase.imports', 'Import')
    name = fields.Char('Description', store=True)
    product_id = fields.Many2one('poroduct.product', 'Producto', store=True)
    product_id = fields.Many2one('poroduct.product', 'Producto', store=True)
    quantity = fields.Integer('Cantidad')
    former_cost = fields.Float('Cantidad')
    final_cost = fields.Monetary(
        'New Value', compute='_compute_final_cost',
        store=True)
    additional_landed_cost = fields.Monetary(
        'Additional Landed Cost')
    currency_id = fields.Many2one('res.currency', related='purchase_import_id.currency_id')
"""