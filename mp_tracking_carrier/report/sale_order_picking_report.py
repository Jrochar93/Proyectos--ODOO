
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrderTrkGuideCarrierReport(models.Model):
    _name = "sale.order.trk.guide.carrier.report"
    _description = "Listado de pedidos con ordenes de entrega"
    _auto = False
    _order = 'date_order desc'

    stock_picking_id = fields.Many2one('stock.picking', string='Movimiento')
    sale_order_id = fields.Many2one('sale.order', string='Pedido de Venta')
    name_sale = fields.Char('Pedido')
    state_order = fields.Selection(string='Estado Pedido', related='sale_order_id.state')
    state_picking = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'En Espera'),
        ('assigned', 'Preparado'),
        ('done', 'Terminado'),
        ('cancel', 'Cancelado')
        ], string='Estado Picking', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Contacto', related='sale_order_id.partner_id')
    partner_shipping_id = fields.Many2one('res.partner', string='Direccion de entrega', related='sale_order_id.partner_shipping_id')
    phone_partner = fields.Char(string='Telefono', related ='partner_id.phone')
    n_oc = fields.Char('O.C.')
    city_id = fields.Many2one('res.city', string='Ciudad')

    street_shipping = fields.Char('Calle')
    street2_shipping = fields.Char('Punto de Referencia')

    date_order = fields.Date('Fecha Confirmación')

    date_min_order = fields.Date('Fecha Minima')
    date_max_order = fields.Date('Fecha Maxima')

    carrier_id = fields.Many2one('delivery.carrier', string='Transportista')
    guide_order = fields.Char('Nro Guía')

    date_scheduled_time_ol = fields.Datetime('Fecha de alistamiento')

    team_id_order = fields.Many2one('crm.team', string='Equipo de Ventas')
    channel_sale_order = fields.Many2one('sale.channels', string='Canal de Ventas')

    number_of_packages = fields.Integer('Nro Paquetes')

    date_unique_delivey_mp = fields.Datetime('Fecha única de Entrega')
    qty_delivered_order = fields.Integer('Cantidad Unidades')
    price_subtotal_order = fields.Float('Subtotal Orden')

    mp_valor_declarado = fields.Float('Valor Declarado')

    _depends = {
        'account.move': [
            'name', 'state', 'move_type', 'partner_id', 'invoice_user_id', 'fiscal_position_id',
            'invoice_date', 'invoice_date_due', 'invoice_payment_term_id', 'partner_bank_id', 'partner_shipping_id',
        ],
        'account.move.line': [
            'quantity', 'price_subtotal', 'amount_residual', 'balance', 'amount_currency',
            'move_id', 'product_id', 'product_uom_id', 'account_id', 'analytic_account_id',
            'journal_id', 'company_id', 'currency_id', 'partner_id',
        ],
        'sale.order': [
            'name', 'partner_id',
        ],
        'product.product': ['product_tmpl_id', 'default_code'],
        'product.template': ['categ_id'],
        'uom.uom': ['category_id', 'factor', 'name', 'uom_type'],
        'res.currency.rate': ['currency_id', 'name'],
        'res.partner': ['country_id'],
    }

    @api.model
    def _select(self):
        return '''
        SELECT 
            so.id as id,
            so.id as sale_order_id,
            so.name as name_sale,
            so.state as state_order,
            so.client_order_ref as n_oc,
            so.date_order as date_order,
            partner.name as cliente,
            partner_shipping.name as direccion_entrega,
            partner_shipping.street as street_shipping,
            partner_shipping.street2 as street2_shipping,
            partner_shipping.city_id as city_id,
            so.x_studio_max_ship_date as date_min_order, 
            so.x_studio_min_ship_date as date_max_order,
            so.picking_id as stock_picking_id,
            stock_p.state as state_picking,
            stock_p.carrier_id as carrier_id,
            stock_p.sale_order_guide as guide_order,
            stock_p.x_studio_scheduled_time_ol as date_scheduled_time_ol,
            so.team_id as team_id_order,
            so.channel_sale_id_mp as channel_sale_order,
            stock_p.x_studio_number_of_packages as number_of_packages,
            stock_p.date_unique_delivey_mp as date_unique_delivey_mp,
            
            (SELECT SUM(price_subtotal)
            FROM sale_order_line as sub_total_line
            WHERE so.id = sub_total_line.order_id) AS price_subtotal_order,
            
            (SELECT SUM(qty_delivered)
            FROM sale_order_line as qty_total_line 
            WHERE so.id = qty_total_line.order_id) AS qty_delivered_order,

            CASE
                WHEN (SELECT SUM(price_subtotal) FROM sale_order_line as sub_total_line WHERE so.id = sub_total_line.order_id) >= 500000 THEN 250000
                ELSE (SELECT SUM(price_subtotal) FROM sale_order_line as sub_total_line WHERE so.id = sub_total_line.order_id) / 2
            END AS mp_valor_declarado
        
        FROM sale_order so
            INNER JOIN res_partner partner ON partner.id = so.partner_id
            INNER JOIN res_partner partner_shipping ON partner_shipping.id = so.partner_shipping_id
            INNER JOIN stock_picking stock_p ON stock_p.id = so.picking_id
    
            WHERE 
            so.state = 'sale' 
            ORDER BY so.name DESC
        '''

    def init(self):
        # Obtener la consulta SQL
        sql_query = """
            CREATE or REPLACE VIEW sale_order_trk_guide_carrier_report AS (
                %s
            )
        """ % self._select()

        # Imprimir la consulta SQL para verificar
        _logger.info("Consulta SQL para crear la vista:")
        _logger.info(sql_query)

        # Ejecutar la consulta SQL para crear la vista
        self._cr.execute(sql_query)    

        # Log para verificar si se ejecuta la consulta
        _logger.info("Consulta SQL ejecutada para crear la vista")
