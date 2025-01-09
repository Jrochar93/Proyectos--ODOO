# -*- coding: utf-8 -*-
from datetime import * 
from datetime import timedelta
from datetime import date, timedelta
import calendar

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import http.client
import json
import string
import math 

import logging
_logger = logging.getLogger(__name__)



class VtexOrdersContact(models.Model):
    _name = 'vtex.orders.contact'
    _description = 'Vtex Orders Contact'

    
    type_contact = fields.Selection(
        string='Type contac',
        selection=[
                    ('contact', 'Contact'), 
                    ('delivery', 'Delivery'), 
                    ('invoice', 'Invoice')
                   ]
    )
    addressType = fields.Char('addressType')
    receiverName = fields.Char('receiverName')
    addressId = fields.Char('addressId')
    versionId = fields.Char('versionId')
    entityId = fields.Char('entityId')
    postalCode  = fields.Char('postalCode')
    city  = fields.Char('city')
    state  = fields.Char('state')
    country  = fields.Char('country')
    street  = fields.Char('street')
    number   = fields.Char('number')
    neighborhood   = fields.Char('neighborhood')
    complement   = fields.Char('complement')
    reference   = fields.Char('reference')
    value  = fields.Char('value')

    shippingEstimateDate = fields.Char('shippingEstimateDate')
    shippingEstimate = fields.Char('shippingEstimate')
    deliveryCompany = fields.Char('deliveryCompany')

    courierId = fields.Char('courierId')
    courierName = fields.Char('courierName')
    warehouseId = fields.Char('warehouseId')
    dockId = fields.Char('dockId')
    accountCarrierName = fields.Char('accountCarrierName')

    courierNametrackingH = fields.Char('courierNametrackingH')
    trackingIdtrackingH = fields.Char('trackingIdtrackingH')
    trackingLabeltrackingH = fields.Char('trackingLabeltrackingH')
    trackingUrltrackingH = fields.Char('trackingUrltrackingH')


    sync_ok = fields.Boolean('Sync Ok',default=False)

    order_id = fields.Many2one('vtex.orders', string='Order ID')



class VtexOrdersTotals(models.Model):
    _name = 'vtex.orders.totals'
    _description = 'Vtex Orders total'

    type = fields.Selection(
        string='Type',
        selection=[
                    ('Items', 'Items'), 
                    ('Discounts', 'Discounts'), 
                    ('Shipping', 'Shipping'),
                    ('Tax', 'Tax')
                   ]
    )
    name = fields.Char('name')
    value = fields.Char('Precio')
    value_without_tax = fields.Char('Impuesto')
    value_sub_total = fields.Char('Sub-total')

    order_id = fields.Many2one('vtex.orders', string='Order ID')


class VtexOrdersPayment(models.Model):
    _name = 'vtex.orders.payment'
    _description = 'Vtex Orders Payment'

    name_payment = fields.Char('Name Payment')
    value = fields.Char('Precio')
    value_without_tax = fields.Char('Impuesto')
    value_sub_total = fields.Char('Sub-total')

    id_payment_data = fields.Char('Id')
    paymentSystem = fields.Char('paymentSystem')
    paymentSystemName = fields.Char('paymentSystemName')
    
    valuepaymentS = fields.Char('valuepaymentS')
    referenceValue = fields.Char('referenceValue')
    

    order_id = fields.Many2one('vtex.orders', string='Order ID')


class VtexOrdersItems(models.Model):
    _name = 'vtex.orders.items'
    _description = 'Vtex Orders Items'

    
    name = fields.Char('Name')
    quantity = fields.Char('Quantity')
    ean = fields.Char('EAN')
    refid = fields.Char('RefID')
    productid = fields.Char('productId')
    #price = fields.Float('price', digits=(12,2))
    price = fields.Char('Total VTEX')
    price_unit = fields.Char('Precio Unitario')

    price_sub_total = fields.Char('Sub-total sin iva')
    price_unit_without_tax = fields.Char('Precio unitario sin iva')

    price_without_tax = fields.Char('Impuesto')
    
    price_discount = fields.Char('Desc. sin iva')
    price_d_without_tax = fields.Char('Iva Desc.')

    price_total = fields.Char('Total')
    price_t_without_tax = fields.Char('Total sin iva')
    imageurl = fields.Char('imageUrl')

    brandName = fields.Char('brandName')
    brandId = fields.Char('brandId')

    order_id = fields.Many2one('vtex.orders', string='Order ID')




class VtexOrders(models.Model):
    _name = 'vtex.orders'
    _description = 'Vtex Orders'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'


    name = fields.Char('Nombre')
    order = fields.Char('# Pedido Vtex')

    # Data result
    orderId = fields.Char('orderId')
    sequence = fields.Char('sequence')

    marketplaceOrderId = fields.Char('marketplaceOrderId')
    marketplace_name = fields.Char('marketplace')
    marketplaceServicesEndpoint = fields.Char('marketplaceServicesEndpoint')
    origin = fields.Char('Origen')

    affiliateId = fields.Char('affiliateId')
    status = fields.Char('Estado VTEX',track_visibility='onchange')
    statusDescription = fields.Char('statusDescription')

    selectedSla = fields.Char('selectedSla')
    warehouseId = fields.Char('warehouseId')
    courierId = fields.Char('courierId')

    # client data

    email = fields.Char('email')
    firstName = fields.Char('firstName')
    lastName = fields.Char('lastName')
    documentType = fields.Char('documentType')
    document = fields.Char('document')
    phone = fields.Char('phone')
    corporateName = fields.Char('corporateName') 
    tradeName = fields.Char('tradeName')
    corporateDocument = fields.Char('corporateDocument')
    corporateDocument_f = fields.Char('Doc Corporate Format')
    stateInscription = fields.Char('stateInscription')
    corporatePhone = fields.Char('corporatePhone')
    isCorporate = fields.Boolean('isCorporate')
    userProfileId = fields.Char('userProfileId')
    userProfileVersion = fields.Char('userProfileVersion')
    customerClass = fields.Char('customerClass')

    # total order
    value = fields.Char('Total VTEX')
    creationDate = fields.Char('creationDate')
    
    customer = fields.Char('Customer')
    items = fields.Char('Items')
    result = fields.Text('result')

    contact_ids = fields.One2many('vtex.orders.contact', 'order_id', string='Contact')
    city_vtex = fields.Char('Ciudad Vtex',related='contact_ids.city')
    items_ids = fields.One2many('vtex.orders.items', 'order_id', string='Items ID')
    payment_ids = fields.One2many('vtex.orders.payment', 'order_id', string='Contact')

    total_ids = fields.One2many('vtex.orders.totals', 'order_id', string='total')

    # custom data 

    orderIdMarketplace_cd  = fields.Char('orderIdMarketplace_cd')
    paymentIdMarketplace_cd  = fields.Char('paymentIdMarketplace_cd')
    collector_id_cd  = fields.Char('collector_id_cd')
    total_paid_amount_cd  = fields.Char('total_paid_amount_cd')
    currency_id_cd  = fields.Char('currency_id_cd')
    shipment_id_cd  = fields.Char('shipment_id_cd')
     
    sync_ok = fields.Boolean('Sync Ok',default=False)

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('validate', 'Validado'),
        ('error', 'Error'),
        ('cancel', 'Cancelado'),
    ], string='Estado',default='draft')
    color = fields.Integer('Color')



    sale_order_id = fields.Many2one('sale.order', string='Pedido de Venta')
    

    state_order = fields.Selection(string='Estado Pedido', related='sale_order_id.state')
    amount_total_order = fields.Monetary(string='Total',related='sale_order_id.amount_total')
    currency_id = fields.Many2one(related='sale_order_id.currency_id', depends=['sale_order_id.currency_id'])
    
    #sale = fields.Char('Pedido')
    partner_id = fields.Many2one('res.partner', string='Contacto')
    partner_shipping_id = fields.Many2one('res.partner', string='Dirección de Entrega', domain=[('type','=','delivery')])

    city_shipping_id = fields.Many2one('res.city', string='Ciudad Pedido',related='partner_shipping_id.city_id')

    # Orden de Entrega
    stock_picking_id = fields.Many2one('stock.picking', readonly=True, string='# Entrega',store=True)
    state_picking = fields.Selection(string='Estado Entrega', related='stock_picking_id.state')
    nro_guia = fields.Char('Nro Guía', related='stock_picking_id.sale_order_guide')
    
    # Factura
    invoice_id = fields.Many2one('account.move', string='Factura', readonly=True,store=True)

    # ref de pago
    payment_id_mp = fields.Many2one('account.payment', string='Pago')
    payment_vtex_id_mp = fields.Many2one('vtex.orders.payments', string='Pago VTEX')

    # control de errores o advertencias
    control_access = fields.Boolean('Valida',default=True)

    #control de estados de cierre
    control_opt_order = fields.Selection([
        ('not_invoiced', 'Sin factura'),
        ('invoiced', 'Facturado'),
        ('pending_invoice', 'Pendiente de Factura'),
        ('order_cancel', 'Cancelado'),
    ], string='Estado de Facturación',default='not_invoiced')


    check_state_order = fields.Boolean('Check State Order',compute='get_check_state_order',default=False)

    
    @api.depends('check_state_order')
    def get_check_state_order(self):
        id_pick = False
        id_invoice = False
        _logger.info('Inicio funcion # orden de entrega y factura ')

        for rec in self:
            if rec.sale_order_id and rec.sale_order_id.state == 'sale' and rec.state == 'validate': 
                search_order_delivery = self.env['stock.picking'].search([
                                                                '&',
                                                                ('sale_id','=',rec.sale_order_id.id),
                                                                ('state','not in',['cancel']),
                                                                ])
                if search_order_delivery:
                    id_pick = search_order_delivery.id or False

            # FACTURA 
            if rec.sale_order_id and rec.sale_order_id.state == 'sale' and rec.state == 'validate' and len(rec.sale_order_id.ids) > 0: 
                invoice_ids = rec.sale_order_id.invoice_ids
                for rec_inv in invoice_ids:
                    if len(rec_inv) > 0:
                        # get id 
                        id_invoice = rec_inv.id or False

            rec.stock_picking_id = id_pick
            rec.invoice_id = id_invoice 
            rec.check_state_order = True
        _logger.info('Fin funcion # orden de entrega y factura')


    def digito_verificacion(self,rut):
        factores = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
        rut_ajustado=str(rut).rjust( 15, '0')
        s = sum(int(rut_ajustado[14-i]) * factores[i] for i in range(14)) % 11
        if s > 1:
            return 11 - s
        else:
            return s


    def sync_pay_vtex(self):
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        item_payment_ids = self.env['vtex.orders.payments.items']
        payment_vtex_id_mp =  self.env['vtex.orders.payments']
        payment_vtex = self.env['vtex.orders.payments']
        vals_updt = {}
        vals_payment = {}
        tax_details_list = []
        total_amount = total_amount_pay = total_commision_pay = total_shipping_pay = total_fee_pay =  total_fee_pay = cost_shipping_pay = am_f = am_iva = am_ica = 0
        for record in self:
            if not record.paymentIdMarketplace_cd:
                raise UserError("No ha encontrado un pago cargado para sincronizar")
            else:
                get_data_pay = item_payment_ids.search([
                                                    '|',
                                                    '|',
                                                    '|',
                                                    ('id_ref_shipping_pay','ilike',str(record.name)),
                                                    ('id_ref_shipping_pay','ilike',str(record.shipment_id_cd)),
                                                    ('id_ref_shipping_pay','ilike',str(record.paymentIdMarketplace_cd)),
                                                    ('id_oper_payment_market','ilike',str(record.paymentIdMarketplace_cd)),
                                            ])
                
                if get_data_pay:
                    # buscar si tiene generado el pago
                    recorset_pay_vtex = payment_vtex_id_mp.search([('order_vtex_id','=',record.id)])
                    if not recorset_pay_vtex:
                        # crear pago
                        date_order_vtx = record.creationDate[:10]
                        vals_payment = {
                            'name': str(record.name),
                            'partner_id': record.partner_id.id,
                            'amount': float(record.value),
                            'date': date_order_vtx,
                            'order_vtex_id': record.id,
                            }
                        res_payment = payment_vtex.sudo().create(vals_payment)
                        res_payment_val = res_payment.id
                        vals_update = {
                                'payment_vtex_id_mp': res_payment_val,
                        }
                        write_order = record.sudo().write(vals_update)
                    else:
                        res_payment = recorset_pay_vtex

                for record_p in get_data_pay:
                    tax_details = record_p.tax_details_pay
                    if tax_details != '' or tax_details != [] or tax_details != '[]' or tax_details != '[]':
                        tax_details_f1 = tax_details.replace('[','')
                        tax_details_f2 = tax_details_f1.replace(']','')
                        tax_details_f3 = tax_details_f2.replace('"fuente,','"fuente",')
                        tax_details_f4 = tax_details_f3.replace('"iva,','"iva",')
                        tax_details_f5 = tax_details_f4.replace('"ica,','"ica",')
                        tax_details_f6_f1 = tax_details_f5.replace(', "detail"', '", "detail"')
                        tax_details_f6 = tax_details_f6_f1.replace(' ', '')

                        tax_det = tax_details_f6.split(sep='{', maxsplit=1)
                        tax_det = tax_details_f6.split(sep='}', maxsplit=2)
                        tax_det = tax_details_f6.split(sep='{', maxsplit=3)

                        if  tax_details != '['']':
                            if len(tax_det) == 4:
                                # todos los impuestos
                                # crear diccionarios
                                dict_1 = "{"+tax_det[1]
                                dict_2 = "{"+tax_det[2]
                                dict_3 = "{"+tax_det[3]

                                # replace extra
                                dict_1_f = dict_1.replace('},','}')
                                dict_2_f = dict_2.replace('},','}')
                                dict_3_f = dict_3.replace('},','}')

                                dict_1_f_1 = json.loads(dict_1_f)
                                dict_2_f_2 = json.loads(dict_2_f)
                                dict_3_f_2 = json.loads(dict_3_f)

                                if dict_1_f_1['financial_entity'] == 'fuente':
                                    am_f = abs(float(dict_1_f_1['amount']))
                                if dict_2_f_2['financial_entity'] == 'iva':
                                    am_iva = abs(float(dict_2_f_2['amount']))
                                if dict_3_f_2['financial_entity'] == 'ica':
                                    am_ica = abs(float(dict_2_f_2['amount']))
                            else:
                                # crear diccionarios
                                dict_1 = "{"+tax_det[1]
                                dict_2 = "{"+tax_det[2]

                                # replace extra
                                dict_1_f = dict_1.replace('},','}')
                                dict_2_f = dict_2.replace('},','}')

                                dict_1_f1 = dict_1_f.replace('""','"')
                                dict_2_f1 = dict_2_f.replace('""','"')

                                dict_1_f_1 = json.loads(dict_1_f1)
                                dict_2_f_2 = json.loads(dict_2_f1)


                                if dict_1_f_1['financial_entity'] == 'fuente':
                                    am_f = abs(float(dict_1_f_1['amount']))
                                if dict_2_f_2['financial_entity'] == 'iva':
                                    am_iva = abs(float(dict_2_f_2['amount']))

                        
                    # separar los valores 
                    if abs(float(record_p.value_sale_pay)) > 0:
                        total_amount = abs(float(record_p.value_sale_pay))
                    if abs(float(record_p.amount_net_oper_pay)) > 0:
                        total_amount_pay = abs(float(record_p.amount_net_oper_pay))
                    if abs(float(record_p.commision_meli_tax_pay)) > 0:
                        total_commision_pay = abs(float(record_p.commision_meli_tax_pay))
                    if  abs(float(record_p.cost_shipping_pay))  > 0:
                        cost_shipping_pay = abs(float(record_p.cost_shipping_pay))
                    #if float(record_p.total_fee_pay) > 0:
                    #    total_fee_pay = record_p.total_fee_pay

                    vals_updt = {
                        'total_amount': total_amount,
                        'total_amount_pay': total_amount_pay,
                        'total_commision_pay': total_commision_pay,
                        'total_shipping_pay': cost_shipping_pay,
                        'total_fee_pay': 0,
                        'total_tax_pay': am_iva,
                        'total_ica_pay': am_ica,
                        'total_rtefuente_pay': am_f,
                    }
                    res_payment.write(vals_updt)



    def sync_json_draft(self):
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        config_discount = self.env['config.vtex.items.discount']
        brand_model = self.env['vtex.brand']
        delivery_carrier = self.env['delivery.carrier']

        if get_config == {}:
            raise ValueError("No ha encontrado una configuración para la sincronización valida, contactar con administrador")
        else:
            conn = http.client.HTTPSConnection(get_config['url_access'])
            selectedSla_location_id = False
            for rec in self:
                if rec.result:
                    conn = http.client.HTTPSConnection(get_config['url_access'])
                    headers = {
                            'Accept': "application/json",
                            'Content-Type': "application/json",
                            'X-VTEX-API-AppKey': str(get_config['api_key']),
                            'X-VTEX-API-AppToken': str(get_config['api_token']),
                            'vtexappkey-moreproducts-UZIUXU': str(get_config['account_name']),
                    }
                    payload = ''
                    order_id = str(rec.orderId)
                    conn.request("GET", "/api/oms/pvt/orders/"+order_id, payload, headers)
                    dict_upt = {}
                    dict_upt_contact = {}
                    dict_upt_payment = {}
                    dict_upt_general = {}

                    res = conn.getresponse()
                    data = res.read()
                    data_dict_json = json.loads(data)

                    items = data_dict_json['items']
                    trackingHintsIds = []
                    contactDataList = []
                    for i in range(len(items)):
                        dict_upt['result_data'] = data_dict_json
                        logisticsInfo = data_dict_json['shippingData']['logisticsInfo']
                        trackingHintsIds = data_dict_json['shippingData']['trackingHints']

                        if trackingHintsIds is not None:
                            for i_13 in range(len(trackingHintsIds)):
                                dict_upt_contact['trackingIdtrackingH'] = trackingHintsIds[i_13]['trackingId']
                                dict_upt_contact['trackingLabeltrackingH'] = trackingHintsIds[i_13]['trackingLabel']
                                dict_upt_contact['trackingUrltrackingH'] = trackingHintsIds[i_13]['trackingUrl']
                                dict_upt_contact['courierNametrackingH'] = trackingHintsIds[i_13]['courierName']
                                rec.contact_ids.write(dict_upt_contact) 

                    # Datos Pago vtex.orders.payment
                    paymentData = []
                    paymentsInfo = []
                    paymentsListData = []
                    paymentsListAdd = []
                    paymentData = data_dict_json['paymentData']
                    if paymentData is not None:
                        paymentsInfo = paymentData['transactions']

                        for i_p1 in range(len(paymentsInfo)):
                            paymentsListData = paymentsInfo[i_p1]['payments']
                            for i_p12 in range(len(paymentsListData)):
                                dict_upt_payment['id_payment_data'] = paymentsListData[i_p12]['id']
                                dict_upt_payment['paymentSystem'] = paymentsListData[i_p12]['paymentSystem']
                                dict_upt_payment['paymentSystemName'] = paymentsListData[i_p12]['paymentSystemName']
                                dict_upt_payment['valuepaymentS'] = paymentsListData[i_p12]['value']
                                dict_upt_payment['referenceValue'] = paymentsListData[i_p12]['referenceValue']
                                rec.payment_ids.write(dict_upt_payment) 
            
                    # custom data
                    customData = data_dict_json['customData']
                    if customData is not None:
                        customDataIds = []
                        fieldsListData = []
                        customDataIds = customData['customApps']
                        for ci_1 in range(len(customDataIds)):
                            fieldsListData = customDataIds[ci_1]['fields']
                            dict_upt_general['orderIdMarketplace_cd'] = fieldsListData['orderIdMarketplace']
                            dict_upt_general['paymentIdMarketplace_cd']  = fieldsListData['paymentIdMarketplace']
                            dict_upt_general['collector_id_cd']  = fieldsListData['collector_id']
                            dict_upt_general['total_paid_amount_cd']  = fieldsListData['total_paid_amount']
                            dict_upt_general['currency_id_cd']  = fieldsListData['currency_id']
                            dict_upt_general['shipment_id_cd']  = fieldsListData['shipment_id']
                            rec.write(dict_upt_general) 

    def _add_follower_if_invoiced(self):
        # Buscar órdenes en estados específicos y que no tengan seguidores
        orders_with_invoice_no_followers = self.env['vtex.orders'].search([
            ('status', '=', ['handling'])
        ])
        
        for order in orders_with_invoice_no_followers:
            # Agregar el vendedor como seguidor si existe y no hay seguidores
            if order.sale_order_id.user_id:
                partner_id = order.sale_order_id.user_id.partner_id.id  # Obtenemos el ID del partner del usuario
                order.message_subscribe(partner_ids=[partner_id])
                _logger.info(f'Se agregó el vendedor {order.sale_order_id.user_id.name} como seguidor en el pedido {order.name}')
            else:
                _logger.warning(f'No se pudo agregar el seguidor para el pedido {order.id} porque no tiene un vendedor asignado')


    
    def get_status_order_one(self):
        for rec in self:
            # get status orden
            statusOrden = 'invoice'
            data = self.get_status_order(rec.orderId,statusOrden)

      
    def sync_order_invoiced(self):
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        config_discount = self.env['config.vtex.items.discount']
        brand_model = self.env['vtex.brand']
        delivery_carrier = self.env['delivery.carrier']
        config_vtex_carrier = self.env['config.vtex.delivery.carrier']
        invoiceNumber = invoiceNumber = issuanceDate = invoiceValue = trackingNumber = courier = sale_order_url_guide = ''
        invoiceValue_vtex = value_order = 0
        invoice_diff = 0
        invoice_to_vtex = ''

        _logger.info('Inicio funcion # facturados')
        if get_config == {}:
            raise ValueError("No ha encontrado una configuración para la sincronización valida, contactar con administrador")
        else:
            for rec in self:
                if rec.result:
                    conn = http.client.HTTPSConnection(get_config['url_access'])
                    headers = {
                            'Accept': "application/json",
                            'Content-Type': "application/json",
                            'X-VTEX-API-AppKey': str(get_config['api_key']),
                            'X-VTEX-API-AppToken': str(get_config['api_token']),
                            'vtexappkey-moreproducts-UZIUXU': str(get_config['account_name']),
                    }
                    

                    order_id = str(rec.orderId)
                    if rec.status != 'invoiced':
                        if not rec.invoice_id.name:
                            raise ValueError("No ha encontrado un número de factura")
                        else:
                            invoiceNumber = rec.invoice_id.name
                        #   2023-09-17T16:15:20.0238420+00:00

                        issuanceDate = rec.invoice_id.date
                        inv_value_format = ("%.2f" % rec.invoice_id.amount_total)
                        inv_value_format_2 = inv_value_format.replace(".", "")
                        invoiceValue = inv_value_format_2

                        #Value order 
                        value_order = float(rec.value)
                        invoiceValue_vtex = math.ceil(float(inv_value_format))
                        value_order_vtex_f1 = math.ceil(float(value_order))

                        invoice_diff = invoiceValue_vtex - value_order_vtex_f1
                        if invoice_diff >= 1:
                            invoice_to_vtex = str(value_order_vtex_f1)+"00"
                        elif invoice_diff >= 0:
                            invoice_to_vtex = str(invoiceValue_vtex)+"00"
                        elif invoice_diff <= 0:
                            invoice_to_vtex = str(value_order_vtex_f1)+"00"

                        #if invoice_to_vtex == '00' or invoice_to_vtex == '0':
                        #    raise ("El valor que esta enviado es 0, por favor revisar")
                        
                        if rec.sale_order_id.nro_guia:
                            trackingNumber = rec.sale_order_id.nro_guia
                        else:
                            trackingNumber = rec.stock_picking_id.sale_order_guide

                        if rec.stock_picking_id.carrier_id:
                            courier = rec.stock_picking_id.carrier_id.name
                        else:
                            courier = rec.sale_order_id.carrier_id.name

                        # macth config 
                        if rec.stock_picking_id.carrier_id:
                            search_carrier = config_vtex_carrier.search([('delivery_carrier_id','=',rec.stock_picking_id.carrier_id.id)],limit=1)
                            if search_carrier.url_delivery and search_carrier.url_delivery != '':
                                if search_carrier.add_number_guide == True:
                                    #replace 
                                    url_temp_1 = search_carrier.url_delivery
                                    url_temp_2 = url_temp_1.replace("GUIA",trackingNumber)
                                    sale_order_url_guide = url_temp_2
                                else:
                                    sale_order_url_guide = search_carrier.url_delivery
                            else:
                                sale_order_url_guide = rec.stock_picking_id.sale_order_url_guide

                        payload = {
                            'type': 'Output',
                            'issuanceDate': str(issuanceDate),
                            'invoiceNumber': str(invoiceNumber),
                            'invoiceValue': str(invoice_to_vtex),
                            'trackingNumber': str(trackingNumber),
                            'courier': str(courier) ,
                            'trackingUrl': str(sale_order_url_guide) ,
                        }
                        _logger.info(payload)

                        order_id = str(rec.orderId)
                        conn.request("POST", "/api/oms/pvt/orders/"+str(order_id)+"/invoice", str(payload), headers)

                        res = conn.getresponse()
                        _logger.info(res)
                        _logger.info('Fin funcion # facturados')
                        get_status = self.get_status_order(str(order_id),'invoice')
                        if get_status[0] == True:
                            # actualizar en odoo el estado
                            rec.write({'status': get_status[1],'statusDescription': get_status[2]})
                        else:
                            # pendiente por sincronizar 
                            pass
                    else:
                        if rec.status == 'invoiced':
                           _logger.info("La orden ya fue cambiada a este estado")
                        else:
                            _logger.info("La orden no esta disponible para este cambio")



    def get_status_order(self,orderId,statusOrden):
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        config_discount = self.env['config.vtex.items.discount']
        brand_model = self.env['vtex.brand']
        delivery_carrier = self.env['delivery.carrier']
        list_data = []
        status = statusDescription = ''
        status_return = False

        if get_config == {}:
            raise ValueError("No ha encontrado una configuración para la sincronización valida, contactar con administrador")
        else:
            if orderId:
                conn = http.client.HTTPSConnection(get_config['url_access'])
                headers = {
                        'Accept': "application/json",
                        'Content-Type': "application/json",
                        'X-VTEX-API-AppKey': str(get_config['api_key']),
                        'X-VTEX-API-AppToken': str(get_config['api_token']),
                        'vtexappkey-moreproducts-UZIUXU': str(get_config['account_name']),
                }
                payload = ''
                orderId = str(orderId)
                conn.request("GET", "/api/oms/pvt/orders/"+str(orderId), payload, headers)
                res = conn.getresponse()
                data = res.read()
                dict_order = json.loads(data)
                status = dict_order['status']
                statusDescription = dict_order['statusDescription']
                status_return = True
                list_data.append(status_return)
                list_data.append(status)
                list_data.append(statusDescription)
                

            return list_data 




    def sync_start_handling(self):
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        config_discount = self.env['config.vtex.items.discount']
        brand_model = self.env['vtex.brand']
        delivery_carrier = self.env['delivery.carrier']

        if get_config == {}:
            raise ValueError("No ha encontrado una configuración para la sincronización valida, contactar con administrador")
        else:
            for rec in self:
                if rec.result:
                    conn = http.client.HTTPSConnection(get_config['url_access'])
                    headers = {
                            'Accept': "application/json",
                            'Content-Type': "application/json",
                            'X-VTEX-API-AppKey': str(get_config['api_key']),
                            'X-VTEX-API-AppToken': str(get_config['api_token']),
                            'vtexappkey-moreproducts-UZIUXU': str(get_config['account_name']),
                    }
                    payload = ''
                    order_id = str(rec.orderId)
                    if (rec.status == 'ready-for-handling' and rec.sale_order_id.state == 'sale'):
                        conn.request("POST", "/api/oms/pvt/orders/"+order_id+"/start-handling", payload, headers)
                        dict_upt = {}
                        dict_upt_contact = {}
                        res = conn.getresponse()
                        if res.status == 200:
                            vals_update = {
                                'status' : 'handling',
                                }
                            rec.write(vals_update)


                    else:
                        if rec.status == 'handling':
                            _logger.info("La orden ya fue cambiada a este estado")
                        else:
                            _logger.info("La orden no esta disponible para este cambio")

    def sync_order(self):
        session_company_id = self.env.user.company_id
        get_config = self.env['config.vtex.access'].get_config_vtex()
        vtex_validator_products = self.env['vtex.validator.products']
        prod_prod = self.env['product.product']
        prod_temp = self.env['product.template']
        obj_op = self.env['vtex.sync.operations']
        res_partner = self.env['res.partner']
        sale_order = self.env['sale.order']
        sale_order_line = self.env['sale.order.line']
        payment_vtex = self.env['vtex.orders.payments']
        sync_orders_auto = get_config['sync_orders_auto']
        sync_orders_handling_auto = get_config['sync_orders_handling_auto']
    
        colombian_edi_codes = self.env['l10n_co_edi.type_code']
        brand_model = self.env['vtex.brand']
        delivery_carrier = self.env['delivery.carrier']
    
        if not get_config:
            raise ValueError("No se ha encontrado una configuración válida para la sincronización. Contacte con el administrador.")
        else:
            conn = http.client.HTTPSConnection(get_config['url_access'])
            selectedSla_location_id = False
            street = partner_phone = partner_phone_delivery = email_partner = street = number = neighborhood = domain_document = reference = complement = ''
            nro_guia = url_guia = ''
            
            # Obtener rango de fechas del mes actual
            today = date.today()
            start_of_month = today.replace(day=1)
            _, last_day_of_month = calendar.monthrange(today.year, today.month)
            end_of_month = today.replace(day=last_day_of_month)
            
            for record in self:
                # Excluir órdenes fuera del rango del mes actual
                order_date = datetime.strptime(record.creationDate[:10], '%Y-%m-%d').date()
                if order_date < start_of_month or order_date > end_of_month:
                    _logger.info(f"Orden {record.name} excluida porque no pertenece al mes actual.")
                    continue
                
                # Excluir órdenes con affiliateId = 'FLB'
                if record.affiliateId == 'FLB':
                    _logger.info(f"Orden {record.name} excluida porque es de FLB.")
                    continue
    
                if record.isCorporate:
                    domain_document = [
                        '&', '&', '&',
                        ('active', '=', True),
                        ('type', '=', 'contact'),
                        ('company_type', '=', 'company'),
                        ('vat', '=', str(record.corporateDocument_f))
                    ]
                else:
                    domain_document = [
                        '&', '&',
                        ('active', '=', True),
                        ('type', '=', 'contact'),
                        ('vat', '=', str(record.document))
                    ]
                search_resp = res_partner.search(domain_document, limit=1)
    
                # Configuración de obligaciones FE
                colombian_edi_codes_ids = get_config['colombian_edi_codes_ids']
                if not colombian_edi_codes_ids:
                    raise UserError("No se ha encontrado el valor para obligaciones y responsabilidades FE.")
    
                # Si se encuentra el contacto, actualizar datos
                if search_resp:
                    id_res_partner = search_resp
                    partner_phone = record.phone or ''
                    name_partner = f"{record.firstName} {record.lastName}" if not record.isCorporate else record.corporateName
                    type_document = self.env['l10n_latam.identification.type'].search(
                        [('name', '=', 'NIT' if record.isCorporate else 'Cédula de ciudadanía')], limit=1
                    )
                    street = number = neighborhood = complement = ''
                    for rec_contact in record.contact_ids:
                        street = rec_contact.street or ''
                        number = rec_contact.number or ''
                        neighborhood = rec_contact.neighborhood or ''
                        complement = rec_contact.complement or ''
    
                    try:
                        vals_write_resp = {
                            'type': 'contact',
                            'company_type': 'company' if record.isCorporate else 'person',
                            'x_studio_type_person': 'Juridica' if record.isCorporate else 'Natural',
                            'x_studio_first_name': record.firstName,
                            'x_studio_surname': record.lastName,
                            'vat': record.document,
                            'l10n_latam_identification_type_id': type_document.id,
                            'phone': partner_phone,
                            'mobile': partner_phone,
                            'email': record.email or '',
                            'name': name_partner,
                            'street': f"{street} {number} {neighborhood}".strip(),
                            'street2': f"{complement} {neighborhood}".strip(),
                            'import_by_zip_code': True,
                            'zip': rec_contact.postalCode or '',
                            'l10n_co_edi_obligation_type_ids': [(6, 0, [colombian_edi_codes_ids.id])] if colombian_edi_codes_ids else [],
                        }
                        _logger.info(f"Intentando escribir en contacto para la orden: {record.name}, datos: {vals_write_resp}")
                        result_write = id_res_partner.sudo().write(vals_write_resp)
                    except Exception as e:
                        _logger.error(f"Error al crear contacto para la orden: {record.name}. Detalles: {e}")
                        continue  # Continuar con la siguiente orden


                    """vals_write_resp = {
                                'type': 'contact',
                                'company_type': company_type,
                                'x_studio_type_person': type_person,
                                'x_studio_first_name': str(record.firstName),
                                #'x_studio_other_name': str(record.firstName),
                                'x_studio_surname': str(record.lastName),
                                'vat': str(document),
                                'l10n_latam_identification_type_id': type_document.id,
                                'phone': str(partner_phone),
                                'mobile': str(partner_phone),
                                'email': email_partner,
                                #'x_studio_second_surname': str(record.firstName),
                                'name': str(name_partner),
                                'street': str(street)+' '+str(number) or ''+' '+str(neighborhood) or '',
                                'street2': (str(rec_contact.complement or '') + ' ' + str(rec_contact.neighborhood or '') + ' ' + str(rec_contact.reference or '')).strip(),
                                #'city': str(rec_contact.city),
                                'import_by_zip_code': True,
                                'zip': str(rec_contact.postalCode),
                                'l10n_co_edi_obligation_type_ids':  [(6,0,[colombian_edi_codes_ids.id])],
                                }
                    result_write = id_res_partner.sudo().write(vals_write_resp)"""


                    search_resp_delivery = res_partner.search([
                                                '&',
                                                '&',
                                                '&',
                                                ('company_type','in',['person']),
                                                ('type','=','delivery'),
                                                ('zip','=',str(rec_contact.postalCode)),
                                                ('parent_id','=',id_res_partner.id)
                                                ])
                    id_resp_delivery = search_resp_delivery

                    if not id_resp_delivery:
                        partner_phone_delivery = record.phone

                        for rec_contact in record.contact_ids:
                            if partner_phone_delivery == False:
                                partner_phone_delivery = ''

                            street = rec_contact.street
                            number = rec_contact.number
                            neighborhood = rec_contact.neighborhood
                            reference = rec_contact.reference
                            complement = rec_contact.complement

                            if neighborhood == False:
                                neighborhood = ''
                            if number == False:
                                number = ''
                            if neighborhood == False:
                                neighborhood = ''
                            if reference == False:
                                reference = ''
                            if complement == False:
                                complement = ''

                            vals_res_p_delivery = {
                                        'type': 'delivery',
                                        'company_type': 'person',
                                        'phone': partner_phone_delivery,
                                        'mobile': partner_phone_delivery,
                                        #'email': str(record.email),
                                        'parent_id': id_res_partner.id,
                                        'name': str(rec_contact.receiverName),
                                        'street': str(street)+' '+str(number) or ''+' '+str(neighborhood) or '',
                                        'street2': (str(rec_contact.complement or '') + ' ' + str(rec_contact.neighborhood or '') + ' ' + str(rec_contact.reference or '')).strip(),
                                        'x_studio_first_name': str(record.firstName),
                                        'x_studio_surname': str(record.lastName),
                                        'comment': str(reference),
                                        'import_by_zip_code': True,
                                        'zip': str(rec_contact.postalCode),
                                        'l10n_co_edi_obligation_type_ids':  [(6,0,[colombian_edi_codes_ids.id])],
                                        }
                            result_delivery = res_partner.sudo().create(vals_res_p_delivery)
                            id_resp_delivery = result_delivery

                else:
                    for rec_contact in record.contact_ids:
                        resp_acct1 = []
                        partner_phone = ''
                        partner_phone_delivery = ''
                        search_resp_acct1 = colombian_edi_codes.search([
                                                                        '&',
                                                                        ('name','ilike','R-99-PN'),
                                                                        ('type','=','obligation')
                                                                        ],limit=1)
                        
                        partner_phone = record.phone
                        partner_phone_delivery = record.phone

                        if partner_phone == False:
                            partner_phone = ''

                        name_partner = ''
                        type_document = False
                        doc_ft = 0
                        if record.isCorporate == True:
                            doc_ft = record.corporateDocument[:9]
                            dig_vf = self.digito_verificacion(doc_ft)
                            document = str(doc_ft)+"-"+str(dig_vf)
                            # tipo de documento 
                            type_document = self.env['l10n_latam.identification.type'].search([('name','=','NIT')],limit=1)
                            company_type = 'company'
                            type_person = 'Juridica'
                            name_partner = str(record.corporateName)
                        else:
                            document = record.document
                            type_document = self.env['l10n_latam.identification.type'].search([('name','=','Cédula de ciudadanía')],limit=1) 
                            company_type = 'person'
                            type_person = 'Natural'
                            name_partner = str(record.firstName)+" "+str(record.lastName)

                        # extract email
                        leng_email = len(str(record.email))
                        email_partner =  str(record.email)
                        find_condition = '.com-'
                        if find_condition in email_partner:
                            format_e1 = int(email_partner.find(find_condition))
                            format_e2 = email_partner[:format_e1+(len(find_condition)-1)]
                            email_partner = format_e2
                        else:
                            email_partner = ''

                        street = rec_contact.street
                        number = rec_contact.number
                        neighborhood = rec_contact.neighborhood
                        reference = rec_contact.reference

                        if neighborhood == False:
                            neighborhood = ''
                        if number == False:
                            number = ''
                        if neighborhood == False:
                            neighborhood = ''

                        if reference == False:
                                reference = ''

                        firstName = other_name = surName = secondsurName = ''

                        if record.marketplace_name == 'puntoscolombia':
                            string_name = str(record.firstName)
                            list_string = string_name.split(' ')
                            firstName = str(list_string[0])
                            other_name = str(list_string[1]) or ''
                            if len(list_string) > 2:
                                surName = str(list_string[2]) or ''
                            if len(list_string) > 3:
                                secondsurName = str(list_string[3]) or ''

                        else:
                            string_name1 = str(record.firstName)
                            string_name2 = str(record.lastName)

                            list_string1 = string_name1.split(' ')
                            list_string2 = string_name2.split(' ')
                            
                            firstName = str(list_string1[0])
                            if len(list_string1) >1:
                                other_name = str(list_string1[1]) or ''
                           
                            if len(list_string2) > 0:

                                if len(list_string2) == 1 :
                                    surName = str(list_string2[0])

                                if len(list_string2) > 1 :
                                    surName = str(list_string2[0])
                                    secondsurName = str(list_string2[1]) or ''
                                
                                if len(list_string2) > 2 :
                                    surName = str(list_string2[0])
                                    secondsurName = str(list_string2[1])+" "+ str(list_string2[2]) or ''


                        vals_res_p = {
                                    'type': 'contact',
                                    'company_type': company_type,
                                    'x_studio_type_person': type_person,
                                    'x_studio_first_name': str(firstName),
                                    'x_studio_other_name': str(other_name),
                                    'x_studio_surname': str(surName),
                                    'x_studio_second_surname': str(secondsurName),
                                    'vat': str(document),
                                    'l10n_latam_identification_type_id': type_document.id,
                                    'phone': str(partner_phone),
                                    'mobile': str(partner_phone),
                                    'email': email_partner,
                                    #'x_studio_second_surname': str(record.firstName),
                                    'name': str(name_partner),
                                    'street': str(street)+' '+str(number) or ''+' '+str(neighborhood) or '',
                                    'street2': (str(rec_contact.complement or '') + ' ' + str(rec_contact.neighborhood or '') + ' ' + str(rec_contact.reference or '')).strip(),
                                    #'city': str(rec_contact.city),
                                    'import_by_zip_code': True,
                                    'zip': str(rec_contact.postalCode),
                                    'l10n_co_edi_obligation_type_ids':  [(6,0,[colombian_edi_codes_ids.id])],
                                    

                                    }
                        result_contact = res_partner.sudo().create(vals_res_p)
                        id_res_partner = result_contact
                      

                        if partner_phone_delivery == False:
                            partner_phone_delivery = ''

                        vals_res_p_delivery = {
                                    'type': 'delivery',
                                    'company_type': 'person',
                                    'mobile': partner_phone_delivery,
                                    'phone': partner_phone_delivery,
                                    'x_studio_first_name': str(firstName),
                                    'x_studio_other_name': str(other_name),
                                    'x_studio_surname': str(surName),
                                    'x_studio_second_surname': str(secondsurName),
                                    'parent_id': id_res_partner.id,
                                    'name': str(rec_contact.receiverName),
                                    'street': str(street)+' '+str(number) or ''+' '+str(neighborhood) or '',
                                    'street2': (str(rec_contact.complement or '') + ' ' + str(rec_contact.neighborhood or '') + ' ' + str(rec_contact.reference or '')).strip(),
                                    'comment': str(reference),
                                    'import_by_zip_code': True,
                                    'zip': str(rec_contact.postalCode),
                                    }
                        result_delivery = res_partner.sudo().create(vals_res_p_delivery)
                        id_resp_delivery = result_delivery

                # pedido de Venta Revisar 
                search_so = sale_order.search([
                                                ('client_order_ref','=',str(record.name))
                                                ])
                if len(search_so) > 0:                    
                    _logger.info("El número de Orden %s ya esta sincronizado " % str(record.name)) 
                else:
                    # search canal de venta
                    vals_line_so = []
                    items_dict = {}
                    for lines in record.items_ids:
                        product_id = prod_temp.search([
                                                    '&',
                                                    ('default_code','=',lines.refid),
                                                    ('ref_id_vtex','=',lines.productid),
                                                    ])
                        if not product_id:
                            res_product = prod_temp.search([
                                                    '&',
                                                    ('default_code','=',lines.refid),
                                                    ('active','=',True),
                                                    ],limit=1)
                            if res_product:
                                res_search = res_product.search_id_vtex()
                                product_validate = True
                                product_id = res_search
                            else:
                                raise ValidationError("El sistema no ha logrado conseguir el Id Ref VTEX del producto %s" % str(lines.refid)) 
                        else:
                            product_validate = True

                        if product_validate:
                            items_dict = {
                                    'product_id': product_id.product_variant_id.id or False,
                                    'price_unit': lines.price_unit_without_tax,
                                    'product_uom_qty': lines.quantity,
                                    'x_studio_proposed_qty': lines.quantity,
                            }
                            vals_line_so.append((0,0,items_dict))
                        else:
                            raise ValidationError("El sistema no ha logrado conseguir el Id Ref VTEX del producto %s" % str(lines.refid)) 

                    """shipping_tot_val = 0
                    # validar si tiene envio
                    for shipping in record.total_ids:
                        if shipping.type == 'Shipping' and float(shipping.value) > 0:
                            shipping_tot_val = float(shipping.value) + float(shipping_tot_val)
                            #obtener producto por defecto
                            get_id_prd_default = get_config['product_shipment_id']
                            items_dict = {
                                'product_id': get_id_prd_default.product_variant_id.id or False,
                                'price_unit': shipping.value,
                                'product_uom_qty': 1,
                                'x_studio_proposed_qty': 1,

                            }
                            vals_line_so.append((0,0,items_dict))"""
                    shipping_tot_val = 0
                    # Validar si tiene envío
                    for shipping in record.total_ids:
                        if shipping.type == 'Shipping' and float(shipping.value) > 0:
                            # Quitar el 19% del valor de envío y redondear a entero
                            shipping_value_no_tax = round(float(shipping.value) / 1.19)
                            shipping_tot_val += shipping_value_no_tax
                            
                            # Obtener producto por defecto
                            get_id_prd_default = get_config['product_shipment_id']
                            items_dict = {
                                'product_id': get_id_prd_default.product_variant_id.id or False,
                                'price_unit': shipping_value_no_tax,
                                'product_uom_qty': 1,
                                'x_studio_proposed_qty': 1,
                            }
                            vals_line_so.append((0, 0, items_dict))


                    date_order_vtx = record.creationDate[:10]
                    time_order_vtx = str(record.creationDate[11:19])


                    new_time = datetime(year=int(date_order_vtx[0:4]), month=int(date_order_vtx[5:7]), day=int(date_order_vtx[8:10]), hour=int(time_order_vtx[:2]), minute=int(time_order_vtx[3:5]), second=int(time_order_vtx[6:8])) 
                    new_swipe_in = (new_time - timedelta(hours=1))
                    date_sale_order_mp = new_swipe_in

                    # Fecha maxima de entrega
                    for rec_data_max in record.contact_ids:
                        if rec_data_max.type_contact == 'delivery':
                            date_max_order = rec_data_max.shippingEstimateDate[0:10]
                            
                    

                    #validar origen de ubicacion
                    loc_multi_ids = get_config['loc_multi_ids']
                    for rec_loc in loc_multi_ids:
                        if rec_loc.name == record.warehouseId:
                            selectedSla_location_id = rec_loc.origin_id.id

                    if not selectedSla_location_id:
                        raise ValidationError("No se encontrado la ubicacion de origen para el tipo %s" % record.warehouseId)
                    
                    #marcas
                    commercial_user_id = False
                    for rec_brand in record.items_ids:
                        if rec_brand.brandId:
                            search_commercial = brand_model.search([('brand_id','=',str(rec_brand.brandId))])
                            if not search_commercial.commercial_user_id:
                                raise ValidationError("No se encontrado el vendedor para la marca %s" % rec_brand.brandName)
                            else:
                                commercial_user_id = search_commercial.commercial_user_id.id
                                team_id = get_config['team_id']

                    # Trasnportista
                    courier_id = False
                    delivery_carrier_ids = get_config['delivery_carrier_ids']
                    for rec_carrier in delivery_carrier_ids:
                        #if record.marketplace_name == 'MercadoLivre':
                        #    courier_id = False
                        #else:
                        format_carrier =  str(record.courierId)
                        if str(rec_carrier.name) == format_carrier.strip():
                            courier_id = rec_carrier.delivery_carrier_id.id

                        # numero de guia y url
                        for rec_guia in record.contact_ids:
                            if rec_guia.type_contact == 'delivery':
                                nro_guia = rec_guia.trackingIdtrackingH
                                url_guia = rec_guia.trackingUrltrackingH

                    if not courier_id:
                        raise ValidationError("No se encontrado el metodo de entrega para el codigo %s" % record.courierId)


                    # Canal de Venta
                    sale_channels_id = False
                    sale_channels_ids = get_config['sale_channels_ids']
                    for rec_sale_ch in sale_channels_ids:
                        if str(rec_sale_ch.name) == str(record.marketplace_name):
                            sale_channels_id = rec_sale_ch.channel_sale_id_mp.id
                        
                    
                    if not sale_channels_id:
                        raise ValidationError("No se encontrado el canal de venta %s" % record.marketplace_name)


                    
                    vals_so = {
                            'partner_id': id_res_partner.id ,
                            'partner_invoice_id': id_res_partner.id,
                            'partner_shipping_id': id_resp_delivery.id,
                            'payment_term_id': id_res_partner.property_payment_term_id.id,
                            'x_studio_location_id': selectedSla_location_id,
                            'date_order': date_order_vtx,
                            'date_sale_order_mp': date_sale_order_mp,
                            'x_studio_fecha_malla': date_order_vtx,
                            'client_order_ref':  str(record.name),
                            'x_studio_type_cross':  'factura',
                            'x_studio_min_ship_date':  date_order_vtx,
                            'x_studio_max_ship_date':  date_max_order,
                            'user_id': commercial_user_id,
                            'team_id': team_id.id,
                            'carrier_id': courier_id,
                            'order_line': vals_line_so,
                            'channel_sale_id_mp': sale_channels_id,
                            'nro_guia': str(nro_guia),
                            'url_guia': str(url_guia),

                            
                    }
                    result_so = sale_order.sudo().create(vals_so)

                    res_payment_val = False
                    # crear Pago
                    if get_config['sync_payment_auto'] == True:
                        vals_payment = {
                                'name': str(record.name),
                                'partner_id': id_res_partner.id,
                                'amount': float(record.value),
                                'date': date_order_vtx,
                                'order_vtex_id': record.id,
                            }
                        res_payment = payment_vtex.sudo().create(vals_payment)
                        res_payment_val = res_payment.id
                    else: 
                        res_payment_val = False
                    
                    if result_so:
                        # update venta y contacto
                        vals_update = {
                                'sale_order_id': result_so.id,
                                'partner_id': id_res_partner.id,
                                'partner_shipping_id': id_resp_delivery.id,
                                'payment_vtex_id_mp': res_payment_val,
                                'sync_ok': True,
                                'state': 'validate',
                        }
                        write_order = record.sudo().write(vals_update)

                        #Auto confirm order
                        if sync_orders_auto == True:
                            if result_so.id and result_so.state == 'draft':
                                #confirmar a pedido de venta
                                result_so.action_confirm()

                        if sync_orders_handling_auto == True:
                            if record.state == 'validate' and record.sale_order_id.state == 'sale':
                                record.sync_start_handling()
    def unlink(self):
        for rec in self:
            if rec.state == 'validate' or rec.sale_order_id.state == 'sale':
                raise ValidationError("El pedido  %s ha sido sincronizado no se puede eliminar " % str(rec.name)) 
        return super().unlink()


    def action_break_synch(self):
        for rec in self:
            # borrar pago
            if rec.payment_id_mp:
                rec.payment_id_mp.unlink()
            if rec.sale_order_id:
                rec.sale_order_id.unlink()
            if rec.partner_id:
                rec.partner_id.unlink()
                rec.partner_shipping_id.unlink()
            rec.write({'state': 'draft','sync_ok': False})
    


    def action_cancel(self):
        for record in self:
            record.write({'state': 'cancel','sync_ok': True,})

    def action_draft(self):
        for record in self:
            record.write({'state': 'draft','sync_ok': False,})



    def search_order(self):
        conn = http.client.HTTPSConnection("moreproducts.myvtex.com")
        payload = ''
        headers = {
        'X-VTEX-API-AppKey': 'vtexappkey-moreproducts-UZIUXU',
        'X-VTEX-API-AppToken': 'AWSDDYCEEWBFDDQYJQRZOWJSFBPADJUZQHAIHWULGTXOJNDCUTFVKVTWZPDJNAXBDRTZBSNNKJVNVXTUJWKCQDOMAXBZQFRNJNDOKWMBDOBQUNEKYDWFGHWTCDFWNATU',
        'vtexappkey-moreproducts-UZIUXU': 'vtexappkey-moreproducts-UZIUXU'
        }
        product_id = 'VTA-82492'
        conn.request("GET", "/api/oms/pvt/orders/"+str(self.order), payload, headers)

        res = conn.getresponse()
        data = res.read()
        person_dict = json.loads(data)
        items = person_dict['items']
        item_values = []
        for i in range(len(items)):
            
            item_values.append((0,0,{
                    'refid': items[i]['refId'],
                    'productid': items[i]['productId'],
                    'name': items[i]['name'],
                    'quantity': items[i]['quantity'],
                    'ean': items[i]['ean'],
                    'price': items[i]['price'],
                    'imageurl': items[i]['imageUrl'],
                    'order_id':self.id,
                }))
            
        totals = person_dict['totals']
        totals_values = []
        for i in range(len(totals)):
            totals_values.append((0,0,{
                    'type': totals[i]['id'],
                    'name': totals[i]['name'],
                    'value': totals[i]['value'],
                    'order_id':self.id,
                }))
            
        shippingData = person_dict['shippingData']['address']
        shippingDataList = []

        shippingDataList.append((0,0,{
                    'type_contact': 'delivery',
                    'addressType': shippingData['addressType'],
                    'receiverName': shippingData['receiverName'],
                    'addressType': shippingData['addressType'],
                    'receiverName': shippingData['receiverName'],
                    'addressId': shippingData['addressId'],
                    'versionId': shippingData['versionId'],
                    'entityId': shippingData['entityId'],
                    'postalCode': shippingData['postalCode'],
                    'city': shippingData['city'],
                    'state': shippingData['state'],
                    'country': shippingData['country'],
                    'street': shippingData['street'],
                    'number': shippingData['number'],
                    'neighborhood': shippingData['neighborhood'],
                    'complement': shippingData['complement'],
                    'reference': shippingData['reference'],
                    'order_id':self.id,
                }))
        

        orderId = person_dict['orderId']
        sequence = person_dict['sequence']

        marketplaceOrderId = person_dict['marketplaceOrderId']
        marketplaceServicesEndpoint = person_dict['marketplaceServicesEndpoint']
        origin = person_dict['origin']
        affiliateId = person_dict['affiliateId']
        status = person_dict['status']
        statusDescription = person_dict['statusDescription']

        #client data

        email = person_dict['clientProfileData']['email']
        firstName = person_dict['clientProfileData']['firstName']
        lastName = person_dict['clientProfileData']['lastName']
        documentType = person_dict['clientProfileData']['documentType']
        document = person_dict['clientProfileData']['document']
        phone = person_dict['clientProfileData']['phone']
        corporateName = person_dict['clientProfileData']['corporateName']
        value  = person_dict['value']

        # remove items old
        search_items = self.env['vtex.orders.items'].search([('order_id','=',self.id)])
        if search_items:
            for rec in search_items:
                rec.unlink()

        search_totals = self.env['vtex.orders.totals'].search([('order_id','=',self.id)])
        if search_totals:
            for rec_t in search_totals:
                rec_t.unlink()

        search_contacts = self.env['vtex.orders.contact'].search([('order_id','=',self.id)])
        if search_contacts:
            for rec_cont in search_contacts:
                rec_cont.unlink()

        search_payments = self.env['vtex.orders.payment'].search([('order_id','=',rec_data.id)])
        if search_payments:
            for rec_py in search_payments:
                if rec_py:
                    rec_py.unlink()

        creationDate = person_dict['creationDate']


        vals_update = {
                        'result': (json.dumps(person_dict, indent=4, separators=(". ", " = "))),
                        'customer':person_dict['clientProfileData'],
                        'items':person_dict['items'],
                        'orderId' : orderId,
                        'sequence' : sequence,
                        'creationDate': creationDate,

                        'email' : email,
                        'firstName' : firstName,
                        'lastName' : lastName,

                        'documentType' : documentType,
                        'document' : document,
                        'phone' : phone,
                        'corporateName' : corporateName,
                        'value': value,

                        'marketplaceOrderId' : marketplaceOrderId,
                        'marketplaceServicesEndpoint' : marketplaceServicesEndpoint,
                        'origin' : origin,

                        'affiliateId' : affiliateId,
                        'status' : status,
                        'statusDescription' : statusDescription,

                        'items_ids': item_values,
                        'total_ids': totals_values,
                        'contact_ids': shippingDataList,

                        }
        self.write(vals_update)

    def _get_order_canceled(self):
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        config_discount = self.env['config.vtex.items.discount']
        brand_model = self.env['vtex.brand']
        delivery_carrier = self.env['delivery.carrier']
        list_orders = []
        status = statusDescription = ''
        status_return = False
        _logger.info('Inicio Cron funcion # facturados')

        if get_config == {}:
            raise ValueError("No ha encontrado una configuración para la sincronización valida, contactar con administrador")
        else:
            conn = http.client.HTTPSConnection(get_config['url_access'])
            headers = {
                    'Accept': "application/json",
                    'Content-Type': "application/json",
                    'X-VTEX-API-AppKey': str(get_config['api_key']),
                    'X-VTEX-API-AppToken': str(get_config['api_token']),
                    'vtexappkey-moreproducts-UZIUXU': str(get_config['account_name']),
            }
            payload = ''
            conn.request("GET", "/api/oms/pvt/orders?f_status=canceled", payload, headers)
            res = conn.getresponse()
            data = res.read()
            order_dicts = json.loads(data)

            list_orders = order_dicts['list']
            for i_order in range(len(list_orders)):
                # search Orders
                orderId = str(order_dicts['list'][i_order]['orderId'])
                exist_order = self.env['vtex.orders'].search([('order','=',str(order_dicts['list'][i_order]['orderId']))])
                conn.request("GET", "/api/oms/pvt/orders/"+str(orderId), payload, headers)
                res_order = conn.getresponse()
                data_order = res_order.read()
                dict_order = json.loads(data_order)
                status = dict_order['status']
                if exist_order:
                    if exist_order.status != 'invoiced':
                        status = dict_order['status']
                        statusDescription = dict_order['statusDescription']
                        exist_order.write({'status': status, 'statusDescription': statusDescription})
    
        _logger.info('Fin Cron funcion # facturados')


    def _set_order_invoiced(self):
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        orders = self.env['vtex.orders']
    
        """
            Marcar según el día y revisar las órdenes con facturas y en estado handling o ready-for-handling
        """
        res_orders = orders.search([
                                    '&',
                                    ('invoice_id', '!=', False),
                                    ('status', 'in', ['handling','ready-for-handling']),
                                   ])
    
        for rec in res_orders:
            try:
                _logger.info(f"Procesando orden: {rec.name}")
                rec.sync_order_invoiced()
            except ValueError as ve:
                _logger.warning(f"Advertencia en la orden {rec.name}: {str(ve)}")
            except Exception as e:
                _logger.error(f"Error al sincronizar la orden {rec.name}: {str(e)}")
            finally:
                _logger.info(f"Finalizado el procesamiento de la orden: {rec.name}")

    def _set_order_handling(self):
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        orders = self.env['vtex.orders']
    
        """
            Marcar según el día y revisar las órdenes con facturas y en estado handling o ready-for-handling
        """
        res_orders = orders.search([
                                    '&',
                                    ('sale_order_id', '!=', False),           
                                    ('status', 'in', ['ready-for-handling']),
                                   ])
    
        for rec in res_orders:
            try:
                _logger.info(f"Procesando orden: {rec.name}")
                rec.sync_start_handling()
            except ValueError as ve:
                _logger.warning(f"Advertencia en la orden {rec.name}: {str(ve)}")
            except Exception as e:
                _logger.error(f"Error al sincronizar la orden {rec.name}: {str(e)}")
            finally:
                _logger.info(f"Finalizado el procesamiento de la orden: {rec.name}")


    # cron de operaciones
    def _get_order_invoiced(self):
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        config_discount = self.env['config.vtex.items.discount']
        brand_model = self.env['vtex.brand']
        delivery_carrier = self.env['delivery.carrier']
        list_orders = []
        status = statusDescription = ''
        status_return = False
        _logger.info('Inicio Cron funcion # facturados')

        if get_config == {}:
            raise ValueError("No ha encontrado una configuración para la sincronización valida, contactar con administrador")
        else:
            conn = http.client.HTTPSConnection(get_config['url_access'])
            headers = {
                    'Accept': "application/json",
                    'Content-Type': "application/json",
                    'X-VTEX-API-AppKey': str(get_config['api_key']),
                    'X-VTEX-API-AppToken': str(get_config['api_token']),
                    'vtexappkey-moreproducts-UZIUXU': str(get_config['account_name']),
            }
            payload = ''
            conn.request("GET", "/api/oms/pvt/orders?f_status=invoiced", payload, headers)
            res = conn.getresponse()
            data = res.read()
            order_dicts = json.loads(data)

            list_orders = order_dicts['list']
            for i_order in range(len(list_orders)):
                # search Orders
                orderId = str(order_dicts['list'][i_order]['orderId'])
                exist_order = self.env['vtex.orders'].search([('order','=',str(order_dicts['list'][i_order]['orderId']))])
                conn.request("GET", "/api/oms/pvt/orders/"+str(orderId), payload, headers)
                res_order = conn.getresponse()
                data_order = res_order.read()
                dict_order = json.loads(data_order)
                status = dict_order['status']
                if exist_order:
                    if exist_order.status != 'invoiced':
                        status = dict_order['status']
                        statusDescription = dict_order['statusDescription']
                        exist_order.write({'status': status, 'statusDescription': statusDescription})

        _logger.info('Fin Cron funcion # facturados')

    def calcular_dv(self,numero):
        iPrimos = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
        partner = numero
        iChequeo = iResiduo = DigitoNIT = 0
        sTMP = sTmp1 = sTMP2  = ''
        if partner:
            try:
                dev_ref = partner.strip()
                for i in range(0, len(dev_ref)):
                    sTMP = dev_ref[len(dev_ref)-(i +1)]
                    iChequeo = iChequeo + (int(sTMP) * iPrimos[i])
                iResiduo = iChequeo % 11
                if iResiduo <= 1:
                    if iResiduo == 0:
                        DigitoNIT = 0
                    if iResiduo == 1:
                        DigitoNIT = 1
                else:
                    DigitoNIT = 11 - iResiduo
            except:
                pass


            return DigitoNIT


    @api.model
    def _get_order_ready_of_handing(self):
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        config_discount = self.env['config.vtex.items.discount']
        config_discount_tag = self.env['config.vtex.tag.discount']
        _logger.info('Inicio Cron funcion # ready-for-handling')
        list_orders = []
        list_orders_h = []
        if get_config == {}:
            raise ValueError("No ha encontrado una configuración para la sincronización valida, contactar con administrador")
        else:
            conn = http.client.HTTPSConnection(get_config['url_access'])
            conn_handling = http.client.HTTPSConnection(get_config['url_access'])
            get_headers = {
                    'Accept': "application/json",
                    'Content-Type': "application/json",
                    'X-VTEX-API-AppKey': str(get_config['api_key']),
                    'X-VTEX-API-AppToken': str(get_config['api_token']),
                    'vtexappkey-moreproducts-UZIUXU': str(get_config['account_name']),
            }
            payload = ''

            # Validar ordenes en estado handling
            _logger.info('Inicio Validación ordenes funcion # handling')
            conn_handling.request("GET", "/api/oms/pvt/orders?f_status=handling", payload, get_headers)
            result_handling = conn_handling.getresponse()
            data_handling = result_handling.read()
            order_dicts_handling = json.loads(data_handling)

            list_orders_h = order_dicts_handling['list']
            for i_order_h in range(len(list_orders_h)):
                exist_order_h = self.env['vtex.orders'].search([('order','=',str(order_dicts_handling['list'][i_order_h]['orderId']))])
                if exist_order_h and exist_order_h.status == 'ready-for-handling':
                    orderId_h = str(order_dicts_handling['list'][i_order_h]['orderId'])
                    _logger.info('Revisando orden #'+str(orderId_h))
                    conn_handling.request("GET", "/api/oms/pvt/orders/"+str(orderId_h), payload, get_headers)  
                    res_h2 = conn_handling.getresponse()
                    data_h2 = res_h2.read()
                    dict_data_h2 = json.loads(data_h2)
                    orderId_h2 = dict_data_h2['orderId']
                    status_h2 = dict_data_h2['status']
                    if status_h2 == 'handling':
                        exist_order_h.write({'status': 'handling'})
            
            _logger.info('Fin Validación ordenes funcion # handling')
                        
                        
            
            conn.request("GET", "/api/oms/pvt/orders?f_status=ready-for-handling", payload, get_headers)
            res = conn.getresponse()
            data = res.read()
            order_dicts = json.loads(data)

            list_orders = order_dicts['list']

            sync_orders_handling_auto = get_config['sync_orders_handling_auto']

            """for i_order in range(len(list_orders)):
                #create Orders
                exist_order = self.env['vtex.orders'].search([('order','=',str(order_dicts['list'][i_order]['orderId']))])
                if not exist_order:
                    vals_create = {
                            'name': order_dicts['list'][i_order]['orderId'] , 
                            'order': order_dicts['list'][i_order]['orderId'],
                            'status': 'ready-for-handling'
                            } 
                    res_create = self.env['vtex.orders'].sudo().create(vals_create)

            
            last_search_order = self.env['vtex.orders'].search([('status','=','ready-for-handling')])"""
            
            for i_order in range(len(list_orders)):
                # Obtener los detalles de la orden
                orderId = str(order_dicts['list'][i_order]['orderId'])
                conn.request("GET", "/api/oms/pvt/orders/" + orderId, payload, get_headers)
                res_order = conn.getresponse()
                order_data = json.loads(res_order.read())
                
                # Excluir órdenes con affiliateId "FLB"
                if order_data.get('affiliateId') == 'FLB':
                    _logger.info(f'Omitiendo orden {orderId} con affiliateId FLB')
                    continue  # Saltar esta orden y pasar a la siguiente

                # Crear o procesar la orden si no existe
                exist_order = self.env['vtex.orders'].search([('order', '=', orderId)])
                if not exist_order:
                    vals_create = {
                        'name': orderId, 
                        'order': orderId,
                        'status': 'ready-for-handling'
                    }
                    res_create = self.env['vtex.orders'].sudo().create(vals_create)

            last_search_order = self.env['vtex.orders'].search([('status', '=', 'ready-for-handling')])

            for rec_data in last_search_order:
                # si esta generado un pedido con estado sale
                if rec_data.sale_order_id and rec_data.sale_order_id.state == 'sale' and rec_data.status == 'ready-for-handling':
                    # actualizar solo el estado si esta marcado como handling automatico

                    if rec_data.status == 'ready-for-handling':
                        if sync_orders_handling_auto == True:
                            if rec_data.state == 'validate' and rec_data.sale_order_id.state == 'sale':
                                rec_data.sync_start_handling()

                                #rec_data.write(vals_update)
                else:
                    order_exist = self.env['vtex.orders'].search([('order','=',str(rec_data.name))])
                    courierNametrackingH = trackingIdtrackingH = trackingLabeltrackingH = trackingUrltrackingH = fieldsListData = orderIdMarketplace_cd = paymentIdMarketplace_cd = collector_id_cd = total_paid_amount_cd = currency_id_cd = customData = shipment_id_cd = id_payment_data = paymentSystem = paymentSystemName = valuepaymentS =  referenceValue = ''

                    # sync_orders_auto
                    sync_orders_auto = get_config['sync_orders_auto']
                    if order_exist:
                        # datos de la orden
                        price_total_vtex = price_without_tax = price_sub_total = price_discount_l_f = pd_l_without_tax = pd_l_without_tax = price_without_tax = price_sub_total = price_total = qt = price_unit = price_unit_without_tax = price_t_without_tax = 0

                        conn.request("GET", "/api/oms/pvt/orders/"+str(rec_data.name), payload, get_headers)  
                        res = conn.getresponse()
                        data = res.read()
                        person_dict = json.loads(data)
                        items = person_dict['items']
                        
                        list_tags_price = []
                        item_values = []
                        discountTagList = []

                        for i in range(len(items)):
                            qt = int(items[i]['quantity'])
                            additionalInfo = []
                            additionalInfo = items[i]['additionalInfo']

                
                            brandId = items[i]['additionalInfo']['brandId']
                            brandName =  items[i]['additionalInfo']['brandName']

                            #precio total de vtex
                            price_total_vtex = (float(items[i]['price']) / 100  * qt)
                            price_unit =(float(items[i]['price']) / 100)


                            price_sub_total = ((price_unit / 1.19) * qt)
                            price_unit_without_tax = (abs(price_unit / 1.19))

                            price_without_tax = (abs(price_unit / 1.19 - price_unit))   

                            price_total =  (float(price_unit)  * qt)
                            price_t_without_tax =  (float(price_unit_without_tax) * qt)

                            list_tags_price = items[i]['priceTags']

                            # tag descuento DISCOUNT@MARKETPLACE
                            if list_tags_price != []:
                                price_discount_l_f = price_discount_l_f = 0 
                                for i_disc in range(len(list_tags_price)):
                                    is_shipp_not_apply = True
                                    type_line_disc = self._get_type_disc(list_tags_price[i_disc]['name'],config_discount_tag)
                                    find_condition = 'discount@price-'
                                    search_identifier = config_discount.search([
                                                                                '&',
                                                                                ('name','=',list_tags_price[i_disc]['name']),
                                                                                ('identifier','=',list_tags_price[i_disc]['identifier']),
                                                                                ])
                                    
                                    if not search_identifier:
                                        #crear
                                        if not list_tags_price[i_disc]['identifier']:
                                            list_tags_price[i_disc]['identifier'] = list_tags_price[i_disc]['name']
                                        if find_condition in list_tags_price[i_disc]['name']:
                                            is_shipp_not_apply = False
                                        vals_discount = {
                                                    'name': list_tags_price[i_disc]['name'],
                                                    'identifier': list_tags_price[i_disc]['identifier'],
                                                    'is_shipping_not_apply': is_shipp_not_apply,
                                                    'config_vtex_id': get_config['id'], 
                                                    }
                                        res_create = config_discount.sudo().create(vals_discount)
                                        name_discount = res_create.name
                                        identifier_discount = res_create.identifier
                                        is_shipping_not_apply = res_create.is_shipping_not_apply

                                    else:
                                        for rec2 in search_identifier:
                                            name_discount = rec2.name
                                            identifier_discount = rec2.identifier
                                            is_shipping_not_apply = rec2.is_shipping_not_apply
                                    
                                    #if (list_tags_price[i_disc]['name'] == name_discount or list_tags_price[i_disc]['identifier'] == identifier_discount) and not is_shipping_not_apply:
                                    if type_line_disc != 'shipping':
                                        # descuento 
                                        price_discount_l_f = self._get_price_disc(list_tags_price[i_disc]['value'],qt)
                                        price_discount_l_value = self._get_price_disc(list_tags_price[i_disc]['value'],qt)
                                        pd_l_without_tax = price_discount_l_f - (price_discount_l_f / 1.19)

                                        price_unit = abs(price_unit) - price_discount_l_value
                                        price_unit_without_tax = (abs(price_unit / 1.19))   

                                        price_without_tax = price_unit_without_tax - pd_l_without_tax
                                        price_sub_total = price_sub_total - price_discount_l_f
                                        price_total = price_sub_total
                            
                            item_values.append((0,0,{
                                    'refid': items[i]['refId'],
                                    'productid': items[i]['productId'],
                                    'name': items[i]['name'],
                                    'quantity': items[i]['quantity'],
                                    'ean': items[i]['ean'],
                                    'price': ("%.2f" % price_total_vtex),
                                    'price_unit': ("%.2f" % price_unit),
                                    'price_unit_without_tax': ("%.2f" % price_unit_without_tax),
                                    'price_without_tax': ("%.2f" % price_without_tax),
                                    'price_discount': ("%.2f" % price_discount_l_f),
                                    'price_d_without_tax': ("%.2f" % pd_l_without_tax),
                                    'price_sub_total': ("%.2f" % price_sub_total),
                                    'price_total': ("%.2f" % price_total),
                                    'price_t_without_tax': ("%.2f" % price_t_without_tax),
                                    'imageurl': items[i]['imageUrl'],
                                    'brandId': brandId,
                                    'brandName': brandName,
                                    'order_id':rec_data.id,
                                }))
                        
                        totals = person_dict['totals']
                        totals_values = []
                        
                        for i in range(len(totals)):
                            value_without_tax = value_sub_total = value = 0
                            value = float(totals[i]['value']) / 100 
                            

                            if totals[i]['id'] == 'Items':
                                value_without_tax = abs(value / 1.19 - value)
                                value_sub_total = value / 1.19

                            totals_values.append((0,0,{
                                    'type': totals[i]['id'],
                                    'name': totals[i]['name'],
                                    'value': ("%.2f" % value),
                                    'value_without_tax': ("%.2f" % value_without_tax),
                                    'value_sub_total': ("%.2f" % value_sub_total),
                                    'order_id':rec_data.id,
                                }))
                        
                        # shippingData
                        shippingData = []
                        shippingData = person_dict['shippingData']
                        shippingData_address = person_dict['shippingData']['address']
                        shippingDataList = []
                        deliveryIds = []
                        
                        logisticsInfo = person_dict['shippingData']['logisticsInfo']
                    
                        
                        for i2 in range(len(logisticsInfo)):
                            selectedSla = logisticsInfo[i2]['selectedSla']
                            shippingEstimateDate = logisticsInfo[i2]['shippingEstimateDate']
                            shippingEstimate = logisticsInfo[i2]['shippingEstimate']
                            deliveryCompany = logisticsInfo[i2]['deliveryCompany']

                            deliveryIds = logisticsInfo[i2]['deliveryIds']
                            
                            # logistics IDS
                            for i_12 in range(len(deliveryIds)):
                                courierId = deliveryIds[i_12]['courierId']
                                courierName = deliveryIds[i_12]['courierName']
                                warehouseId = deliveryIds[i_12]['warehouseId']
                                accountCarrierName = deliveryIds[i_12]['accountCarrierName']


                        trackingHintsIds = person_dict['shippingData']['trackingHints']

                        if trackingHintsIds is not None:
                            for i_13 in range(len(trackingHintsIds)):
                                courierNametrackingH = trackingHintsIds[i_13]['courierName']
                                trackingIdtrackingH = trackingHintsIds[i_13]['trackingId']
                                trackingLabeltrackingH = trackingHintsIds[i_13]['trackingLabel']
                                trackingUrltrackingH = trackingHintsIds[i_13]['trackingUrl']

                        if 'x' in shippingData_address['receiverName'] :
                            receiverName_f = shippingData_address['receiverName']
                            receiverName_f_2 = receiverName_f.replace("x",'')
                            shippingData_address['receiverName'] = receiverName_f_2 or ''
                        

                        shippingDataList.append((0,0,{
                                    'type_contact': 'delivery',
                                    'addressType': shippingData_address['addressType'],
                                    'receiverName': shippingData_address['receiverName'],
                                    'addressType': shippingData_address['addressType'],
                                    'addressId': shippingData_address['addressId'],
                                    'versionId': shippingData_address['versionId'],
                                    'entityId': shippingData_address['entityId'],
                                    'postalCode': shippingData_address['postalCode'],
                                    'city': shippingData_address['city'],
                                    'state': shippingData_address['state'],
                                    'country': shippingData_address['country'],
                                    'street': shippingData_address['street'],
                                    'number': shippingData_address['number'],
                                    'neighborhood': shippingData_address['neighborhood'],
                                    'complement': shippingData_address['complement'],
                                    'reference': shippingData_address['reference'],
                                    'shippingEstimateDate': shippingEstimateDate,
                                    'shippingEstimate': shippingEstimate,
                                    'deliveryCompany': deliveryCompany,
                                    'courierId' : courierId,
                                    'courierName' : courierName,
                                    'warehouseId' : warehouseId,
                                    'courierId' : courierId,
                                    'accountCarrierName' : accountCarrierName,
                                    
                                    'courierNametrackingH': courierNametrackingH,
                                    'trackingIdtrackingH': trackingIdtrackingH,
                                    'trackingLabeltrackingH': trackingLabeltrackingH,
                                    'trackingUrltrackingH': trackingUrltrackingH,

                                    'order_id':rec_data.id,
                                }))
                        

                        orderId = person_dict['orderId']
                        sequence = person_dict['sequence']

                        marketplaceOrderId = person_dict['marketplaceOrderId']
                        marketplaceServicesEndpoint = person_dict['marketplaceServicesEndpoint']
                        origin = person_dict['origin']
                        affiliateId = person_dict['affiliateId']
                        status = person_dict['status']
                        statusDescription = person_dict['statusDescription']
                        creationDate = person_dict['creationDate']

                        marketplace_name = person_dict['marketplace']['name']


                        #client data

                        email = person_dict['clientProfileData']['email']
                        firstName = person_dict['clientProfileData']['firstName']
                        lastName = person_dict['clientProfileData']['lastName']

                        if len(lastName) == 1  and  lastName == 'x':
                            lastName = ''


                        phone = person_dict['clientProfileData']['phone']
                        corporateName = person_dict['clientProfileData']['corporateName']
                        value  = person_dict['value']
                        value_format = float(person_dict['value']) / 100 

                        #validar datos de documentos 1356850508990-01 MLT-42561045116



                        isCorporate = person_dict['clientProfileData']['isCorporate']

                        corporateDocument = corporateDocument_f = ''

                        if isCorporate == True or isCorporate == 'true':
                            isCorporate = True
                            documentType = person_dict['clientProfileData']['documentType']
                            corporateDocument = str(person_dict['clientProfileData']['corporateDocument'])
                            document = ''
                            doc_ft = corporateDocument[:9]
                            digito_vf = self.calcular_dv(doc_ft)
                            corporateDocument_f = str(doc_ft)+"-"+str(digito_vf)

                        else:
                            isCorporate = False
                            documentType = person_dict['clientProfileData']['documentType']
                            document = str(person_dict['clientProfileData']['document'])

                        # Datos Pago vtex.orders.payment
                        paymentData = []
                        paymentsInfo = []
                        paymentsListData = []
                        paymentsListAdd = []
                        paymentData = person_dict['paymentData']
                        if paymentData is not None:
                            paymentsInfo = paymentData['transactions']

                            for i_p1 in range(len(paymentsInfo)):
                                paymentsListData = paymentsInfo[i_p1]['payments']
                                for i_p12 in range(len(paymentsListData)):
                                    id_payment_data = paymentsListData[i_p12]['id']
                                    paymentSystem = paymentsListData[i_p12]['paymentSystem']
                                    paymentSystemName = paymentsListData[i_p12]['paymentSystemName']
                                    valuepaymentS = paymentsListData[i_p12]['value']
                                    referenceValue = paymentsListData[i_p12]['referenceValue']
                                    paymentsListAdd.append((0,0,{                              
                                            'id_payment_data': id_payment_data,
                                            'paymentSystem': paymentSystem,
                                            'paymentSystemName': paymentSystemName,
                                            'valuepaymentS': valuepaymentS,
                                            'referenceValue': referenceValue,
                                            'order_id':rec_data.id,
                                        }))
                        

                        # custom data
                        customData = person_dict['customData']
                        if customData is not None:
                            customDataIds = []
                            fieldsListData = []
                            customDataIds = customData['customApps']
                            for ci_1 in range(len(customDataIds)):
                                fieldsListData = customDataIds[ci_1]['fields']
                                orderIdMarketplace_cd = fieldsListData['orderIdMarketplace']
                                paymentIdMarketplace_cd = fieldsListData['paymentIdMarketplace']
                                collector_id_cd = fieldsListData['collector_id']
                                total_paid_amount_cd = fieldsListData['total_paid_amount']
                                currency_id_cd = fieldsListData['currency_id']
                                shipment_id_cd = fieldsListData['shipment_id']


                        # remove items old
                        search_items = self.env['vtex.orders.items'].search([('order_id','=',rec_data.id)])
                        if search_items:
                            for rec in search_items:
                                if rec:
                                    rec.unlink()

                        search_totals = self.env['vtex.orders.totals'].search([('order_id','=',rec_data.id)])
                        if search_totals:
                            for rec_t in search_totals:
                                if rec_t:
                                    rec_t.unlink()

                        search_contacts = self.env['vtex.orders.contact'].search([('order_id','=',rec_data.id)])
                        if search_contacts:
                            for rec_cont in search_contacts:
                                if rec_cont:
                                    rec_cont.unlink()

                        search_payments = self.env['vtex.orders.payment'].search([('order_id','=',rec_data.id)])
                        if search_payments:
                            for rec_py in search_payments:
                                if rec_py:
                                    rec_py.unlink()


                        vals_update = {
                                        'result': (json.dumps(person_dict, indent=4, separators=(". ", " = "))),
                                        'customer':person_dict['clientProfileData'],
                                        'items':person_dict['items'],
                                        'orderId' : orderId,
                                        'sequence' : sequence,
                                        'creationDate': creationDate,

                                        'email' : email,
                                        'firstName' : firstName,
                                        'lastName' : lastName,
                                        'documentType' : documentType,
                                        'document' : document,
                                        'phone' : phone,
                                        'corporateName' : corporateName,
                                        'corporateDocument': corporateDocument,
                                        'corporateDocument_f': corporateDocument_f,
                                        'selectedSla': selectedSla,
                                        'warehouseId' : warehouseId,
                                        'courierId': courierId,
                                        'isCorporate': isCorporate,
                                        'value': value_format,

                                        'marketplaceOrderId' : marketplaceOrderId,
                                        'marketplace_name': marketplace_name,
                                        'marketplaceServicesEndpoint' : marketplaceServicesEndpoint,
                                        'origin' : origin,

                                        'affiliateId' : affiliateId,
                                        'status' : status,
                                        'statusDescription' : statusDescription,

                                        'orderIdMarketplace_cd' : orderIdMarketplace_cd,
                                        'paymentIdMarketplace_cd' : paymentIdMarketplace_cd,
                                        'collector_id_cd' : collector_id_cd,
                                        'total_paid_amount_cd' : total_paid_amount_cd,
                                        'currency_id_cd' : currency_id_cd,
                                        'shipment_id_cd' : shipment_id_cd,
                                        'items_ids': item_values,
                                        'total_ids': totals_values,
                                        'contact_ids': shippingDataList,
                                        'payment_ids': paymentsListAdd,

                                        }
                        rec_data.write(vals_update)

                        if sync_orders_auto == True:
                            rec_data.sync_order()
                #print(Flag)
                _logger.info('Fin Cron funcion # ready-for-handling')

    @api.model
    def _get_order_ready_of_handing_FLB(self):
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        payment_vtex = self.env['vtex.orders.payments']
        config_discount = self.env['config.vtex.items.discount']
        _logger.info('Inicio Cron función para procesar órdenes con affiliateId FLB')

        conn = http.client.HTTPSConnection(get_config['url_access'])
        get_headers = {
            'Accept': "application/json",
            'Content-Type': "application/json",
            'X-VTEX-API-AppKey': str(get_config['api_key']),
            'X-VTEX-API-AppToken': str(get_config['api_token']),
            'vtexappkey-moreproducts-UZIUXU': str(get_config['account_name']),
        }
        payload = ''

        def convert_vtex_date(vtex_date):
            """Convierte la fecha de VTEX al formato que espera Odoo."""
            try:
                vtex_date_clean = vtex_date.split('.')[0]  # Eliminar milisegundos
                return datetime.strptime(vtex_date_clean, '%Y-%m-%dT%H:%M:%S')
            except Exception as e:
                _logger.error(f"Error al convertir la fecha {vtex_date}: {str(e)}")
                return False

        try:
            # Obtener todas las órdenes "ready-for-handling" desde VTEX
            conn.request("GET", "/api/oms/pvt/orders?f_status=ready-for-handling", payload, get_headers)
            res = conn.getresponse()
            data = res.read()
            orders = json.loads(data).get('list', [])

            if not orders:
                _logger.info("No se encontraron órdenes para procesar.")
                return

            for order_summary in orders:
                orderId = order_summary.get('orderId')

                # Obtener detalles de la orden específica
                conn.request("GET", f"/api/oms/pvt/orders/{orderId}", payload, get_headers)
                res_order = conn.getresponse()
                order_data = json.loads(res_order.read())

                # Excluir órdenes que no sean de "FLB"
                if order_data.get('affiliateId') != 'FLB':
                    _logger.info(f'Omitiendo orden {orderId} con affiliateId distinto de FLB')
                    continue

                # Crear o procesar la orden en VTEX si no existe
                exist_order = self.env['vtex.orders'].search([('order', '=', orderId)])

                # Procesar cliente (partner)
                client_data = order_data['clientProfileData']
                partner = self.env['res.partner'].search([('vat', '=', client_data['document'])], limit=1)

                # Inicializar id_resp_delivery como False
                id_resp_delivery = False

                # Asegurarse de inicializar 'colombian_edi_codes_ids'
                colombian_edi_codes_ids = get_config.get('colombian_edi_codes_ids')

                if not partner:
                    # Verificar si es persona jurídica o natural
                    if client_data['isCorporate']:
                        type_document = self.env['l10n_latam.identification.type'].search([('name', '=', 'NIT')], limit=1)
                        company_type = 'company'
                        type_person = 'Juridica'
                        document = client_data['corporateDocument']
                    else:
                        type_document = self.env['l10n_latam.identification.type'].search([('name', '=', 'Cédula de ciudadanía')], limit=1)
                        company_type = 'person'
                        type_person = 'Natural'
                        document = client_data['document']

                    partner_vals = {
                        'name': f"{client_data['firstName']} {client_data['lastName']}",
                        'x_studio_first_name': client_data['firstName'],
                        'x_studio_surname': client_data['lastName'],
                        'email': client_data['email'],
                        'phone': client_data['phone'],
                        'vat': document,
                        'import_by_zip_code': True,
                        'l10n_latam_identification_type_id': type_document.id,
                        'street': order_data['shippingData']['address']['street'],
                        'street2': order_data['shippingData']['address']['complement'],
                        'city': order_data['shippingData']['address']['city'],
                        'city_id': self.env['res.city'].search([('name', 'ilike', order_data['shippingData']['address']['city'])], limit=1).id,
                        'state_id': self.env['res.city'].search([('name', 'ilike', order_data['shippingData']['address']['city'])], limit=1).state_id.id,
                        'zip': self.env['res.city'].search([('name', 'ilike', order_data['shippingData']['address']['city'])], limit=1).zipcode,
                        'country_id': self.env['res.country'].search([('code', 'ilike', order_data['shippingData']['address']['country'])], limit=1).id,
                        'l10n_co_edi_obligation_type_ids': [(6, 0, [colombian_edi_codes_ids.id])] if colombian_edi_codes_ids else [],
                        'x_studio_type_person': type_person,
                    }
                    partner = self.env['res.partner'].sudo().create(partner_vals)
                    _logger.info(f'Creado cliente {partner.name} ({partner.email})')

                # Crear un nuevo contacto de entrega siempre que la información cambie
                shipping_data = order_data['shippingData']['selectedAddresses'][0]
                street = shipping_data.get('street', '')
                number = shipping_data.get('number', '')
                neighborhood = shipping_data.get('neighborhood', '')
                complement = shipping_data.get('complement', '')
                reference = shipping_data.get('reference', '')

                # Buscar un contacto de entrega existente con los mismos datos
                existing_delivery_contact = self.env['res.partner'].search([
                    ('parent_id', '=', partner.id),
                    ('type', '=', 'delivery'),
                    ('street', '=', f"{street} {number} {neighborhood}".strip()),
                    ('street2', '=', complement),
                    ('zip', '=', self.env['res.city'].search([('name', 'ilike', order_data['shippingData']['address']['city'])], limit=1).zipcode),
                    ('phone', '=', client_data['phone'])
                ], limit=1)

                if existing_delivery_contact:
                    _logger.info(f'El contacto de entrega ya existe para {partner.name} en dirección: {existing_delivery_contact.street}')
                    id_resp_delivery = existing_delivery_contact
                else:
                    # Crear un nuevo contacto de entrega basado en la nueva dirección
                    vals_res_p_delivery = {
                        'type': 'delivery',
                        'company_type': 'person',
                        'phone': client_data['phone'],
                        'mobile': client_data['phone'],
                        'parent_id': partner.id,
                        'name': shipping_data['receiverName'],
                        'street': f"{street} {number} {neighborhood}".strip(),
                        'street2': complement,
                        'x_studio_first_name': client_data['firstName'],
                        'x_studio_surname': client_data['lastName'],
                        'comment': reference,
                        'import_by_zip_code': True,
                        'zip': self.env['res.city'].search([('name', 'ilike', order_data['shippingData']['address']['city'])], limit=1).zipcode,
                        'l10n_co_edi_obligation_type_ids': [(6, 0, [colombian_edi_codes_ids.id])] if colombian_edi_codes_ids else [],
                    }
                    result_delivery = self.env['res.partner'].sudo().create(vals_res_p_delivery)
                    _logger.info(f'Creado nuevo contacto de entrega para {partner.name} en dirección: {vals_res_p_delivery["street"]}')
                    id_resp_delivery = result_delivery

                if not exist_order:
                    vals_create = {
                        'name': orderId,
                        'order': orderId,
                        'status': 'ready-for-handling',
                        'marketplaceOrderId': order_data['marketplaceOrderId'],
                        'sequence': order_data['sequence'],
                        'affiliateId': order_data['affiliateId'],
                        'origin': order_data['origin'],
                        'statusDescription': order_data['statusDescription'],
                        'value': float(order_data['value']) / 100,
                        'creationDate': convert_vtex_date(order_data['creationDate']),
                        'marketplace_name': order_data['marketplace']['name'],
                        'marketplaceServicesEndpoint': order_data['marketplaceServicesEndpoint'],
                        'partner_id': partner.id,
                        'partner_shipping_id': id_resp_delivery.id,
                        'email': partner.email,
                        'firstName': partner.x_studio_first_name,
                        'lastName': partner.x_studio_surname,
                        'documentType': partner.l10n_latam_identification_type_id.id if partner.l10n_latam_identification_type_id else False,
                        'document': partner.vat,
                        'phone': partner.phone,
                        'orderId': orderId,
                    }
                    rec_data = self.env['vtex.orders'].sudo().create(vals_create)
                    _logger.info(f'Creada orden en VTEX {orderId}')
                else:
                    _logger.info(f'La orden {orderId} ya existe, no se realiza ninguna acción.')
                    continue

                 # Crear la orden de venta (sale.order)
                sale_order_exist = self.env['sale.order'].search([('client_order_ref', '=', orderId)], limit=1)
                if not sale_order_exist:
                    # Crear líneas de la orden de venta (Sale Order Lines)
                    # Procesar líneas de producto
                    sale_order_lines = []
                    for item in order_data['items']:
                        product = self.env['product.product'].search([('default_code', '=', item.get('refId'))], limit=1)
                        if not product:
                            _logger.info(f"Producto no existe en Odoo {item.get('refId')}")
                            continue

                        # Calcular el precio con descuento (si aplica)
                        price_unit_with_tax = float(item.get('price', 0)) / 100
                        discount_value = 0
                        if item.get('priceTags'):
                            for price_tag in item['priceTags']:
                                if 'DISCOUNT@SELLERPRICE' in price_tag.get('name', ''):
                                    discount_value = abs(float(price_tag.get('value', 0)) / 100)

                        price_unit_final = price_unit_with_tax - discount_value
                        price_unit_without_tax = price_unit_final / 1.19  # Asumiendo que la tasa de IVA es 19%

                        sale_order_line_vals = {
                            'product_id': product.id,
                            'x_studio_proposed_qty': item.get('quantity', 1),
                            'product_uom_qty': item.get('quantity', 1),
                            'price_unit': price_unit_without_tax,
                        }
                        sale_order_lines.append((0, 0, sale_order_line_vals))

                    # Lógica de inserción del envío, solo una vez por orden
                    # Agregamos una bandera para controlar la inserción única del producto de envío
                    shipping_added = False

                    logistics_info = order_data.get('shippingData', {}).get('logisticsInfo', [])
                    for logistics in logistics_info:
                        if not shipping_added:  # Verificar si ya se ha agregado el producto de envío
                            shipping_price_with_tax = float(logistics.get('price', 0)) / 100
                            if shipping_price_with_tax == 0:
                                _logger.info(f"No se agrega línea de envío ya que el valor del envío es 0 para la orden {orderId}.")
                                continue  # No agregar la línea de envío si el precio es 0

                            shipping_price_without_tax = shipping_price_with_tax / 1.19  # Asumiendo IVA 19%

                            # Obtener el producto de envío y agregar la línea solo una vez
                            get_id_prd_default = get_config.get('product_shipment_id')
                            if get_id_prd_default:
                                shipping_vals = {
                                    'product_id': get_id_prd_default.product_variant_id.id or False,
                                    'price_unit': shipping_price_without_tax,
                                    'product_uom_qty': 1,
                                    'x_studio_proposed_qty': 1,
                                }
                                sale_order_lines.append((0, 0, shipping_vals))

                            # Marcar como agregado para que no se repita la inserción del producto de envío
                            shipping_added = True

                    # Asignar el canal de venta basado en el nombre del marketplace
                    sale_channels_id = False
                    sale_channels_ids = get_config['sale_channels_ids']
                    for rec_sale_ch in sale_channels_ids:
                        if str(rec_sale_ch.name) == str(order_data['marketplace']['name']):
                            sale_channels_id = rec_sale_ch.channel_sale_id_mp.id

                    if not sale_channels_id:
                        _logger.info(f"No se encontró el canal de venta para {order_data['marketplace']['name']}")

                    # Obtener el impuesto predeterminado para los productos
                    tax_id = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('company_id', '=', company.id)], limit=1)

                    # Obtener el courierId del JSON y limpiar espacios adicionales
                    courier_id_json = order_data['shippingData']['logisticsInfo'][0]['deliveryIds'][0].get('courierId', '').strip()

                    # Buscar el delivery_carrier_id en la tabla config_vtex_delivery_carrier usando el courierId obtenido
                    delivery_carrier_record = self.env['config.vtex.delivery.carrier'].search([('name', 'ilike', courier_id_json)], limit=1)

                    # Agregar más detalles de depuración para verificar si encontró el registro y el delivery_carrier_id
                    if delivery_carrier_record:
                        _logger.info("Método de entrega encontrado: %s" % delivery_carrier_record.delivery_carrier_id)
                    else:
                        _logger.info("No se encontró método de entrega para el código: %s" % courier_id_json)

                    # Verifica si el campo delivery_carrier_id está correctamente relacionado
                    if delivery_carrier_record and delivery_carrier_record.delivery_carrier_id:
                        courier_id = delivery_carrier_record.delivery_carrier_id if delivery_carrier_record else False
                    else:
                        courier_id = False

                    if not courier_id:
                        raise ValidationError("No se ha encontrado el método de entrega para el código %s" % courier_id_json)


                    # Obtener el team_id y el vendedor (comercial_user_id)
                    brand_id = order_data['items'][0]['additionalInfo'].get('brandId', '')
                    brand_record = self.env['vtex.brand'].search([('brand_id', '=', brand_id)], limit=1)
                    commercial_user_id = False
                    team_id = '8'  # Valor por defecto si no se encuentra el team_id
                    items = order_data['items']
                    for item in items:
                        if 'brandId' in item['additionalInfo']:
                            brand_id = item['additionalInfo']['brandId']
                            brand_record = self.env['vtex.brand'].search([('brand_id', '=', str(brand_id))], limit=1)
                            if not brand_record:
                                _logger.info(f"No se encontró la marca con ID {brand_id}")
                            if not hasattr(brand_record, 'team_id'):
                                _logger.warning(f'El campo team_id no existe en vtex.brand. Se usará el valor por defecto.')
                            if not brand_record.commercial_user_id:
                                _logger.info(f"No se encontró el vendedor para la marca {brand_record.brandName}")
                            commercial_user_id = brand_record.commercial_user_id.id
                            team_id = brand_record.team_id.id if hasattr(brand_record, 'team_id') and brand_record.team_id else '8'
                    # Extraer número de guía y URL de la guía
                    nro_guia = ''
                    url_guia = ''
                    # Extraer y mapear el orderNumber desde customApps
                    custom_data = order_data.get('customData', {}).get('customApps', [])
                    order_number = None
                    if custom_data:
                        order_number = custom_data[0].get('fields', {}).get('orderNumber', '')
                        nro_guia = order_number
                    if 'customData' in order_data and 'customApps' in order_data['customData']:
                        url_guia = order_data['customData']['customApps'][0]['fields'].get('shippingParcel', '')

                    vals_so = {
                        'partner_id': partner.id,
                        'partner_invoice_id': partner.id,
                        'partner_shipping_id': id_resp_delivery.id,
                        'payment_term_id': partner.property_payment_term_id.id,
                        'date_order': convert_vtex_date(order_data['creationDate']),
                        'date_sale_order_mp': convert_vtex_date(order_data['creationDate']),  # Fecha de creación de la venta
                        'x_studio_fecha_malla': convert_vtex_date(order_data['creationDate']),  # Fecha personalizada
                        'x_studio_min_ship_date': convert_vtex_date(order_data['creationDate']),
                        'x_studio_max_ship_date': convert_vtex_date(order_data['shippingData']['logisticsInfo'][0].get('shippingEstimateDate', '')),
                        'client_order_ref': orderId,
                        'team_id': team_id,
                        'user_id': commercial_user_id,
                        'carrier_id': courier_id.id if courier_id else False,
                        'order_line': sale_order_lines,
                        'channel_sale_id_mp': sale_channels_id,
                        'nro_guia': nro_guia,
                        'url_guia': url_guia,
                        'x_studio_type_cross': 'factura',  # Esto lo puedes ajustar si varía
                    }
                    sale_order = self.env['sale.order'].sudo().create(vals_so)
                    _logger.info(f'Creada orden de venta SO para la orden {orderId}')
                else:
                    sale_order = sale_order_exist
                    _logger.info(f'Orden de venta para {orderId} ya existe')

                # Confirmar automáticamente la orden si la configuración lo permite
                sync_orders_auto = get_config.get('sync_orders_auto', False)
                if sync_orders_auto and sale_order.state == 'draft' and sale_order.order_line:
                    sale_order.action_confirm()
                    _logger.info(f'Orden de venta {orderId} confirmada en Odoo')

                # Actualizar el estado de manejo si la orden está validada
                sync_orders_handling_auto = get_config.get('sync_orders_handling_auto', False)
                if sync_orders_handling_auto and rec_data.state == 'validate' and sale_order.state == 'sale':
                    rec_data.sync_start_handling()
                    _logger.info(f'Orden de venta {orderId} lista para manejo en VTEX')

                # Procesar los ítems
                item_values = []
                items = order_data['items']
                for i in range(len(items)):
                    qt = int(items[i]['quantity'])
                    price_total_vtex = (float(items[i]['price']) / 100)
                    price_unit = price_total_vtex / qt
                    price_unit_without_tax = price_unit / 1.19  # Asumiendo que la tasa de IVA es 19%
                    price_without_tax = price_unit_without_tax * qt
                    price_sub_total = price_without_tax * qt
                    price_discount_l_f = 0
                    if items[i]['priceTags']:
                        for price_tag in items[i]['priceTags']:
                            if 'DISCOUNT@SELLERPRICE' in price_tag['name']:
                                price_discount_l_f = abs(float(price_tag['value']) / 100)

                    item_values.append((0, 0, {
                        'refid': items[i]['refId'],
                        'productid': items[i]['productId'],
                        'name': items[i]['name'],
                        'quantity': items[i]['quantity'],
                        'ean': items[i]['ean'],
                        'price': ("%.2f" % price_total_vtex),
                        'price_unit': ("%.2f" % price_unit),
                        'price_unit_without_tax': ("%.2f" % price_unit_without_tax),
                        'price_without_tax': ("%.2f" % price_without_tax),
                        'price_discount': ("%.2f" % price_discount_l_f),
                        'price_sub_total': ("%.2f" % price_sub_total),
                        'order_id': rec_data.id,
                    }))

                # Procesar los totales
                totals_values = []
                totals = order_data['totals']
                for i in range(len(totals)):
                    value = float(totals[i]['value']) / 100
                    value_without_tax = value / 1.19
                    value_sub_total = value_without_tax
                    totals_values.append((0, 0, {
                        'type': totals[i]['id'],
                        'name': totals[i]['name'],
                        'value': ("%.2f" % value),
                        'value_without_tax': ("%.2f" % value_without_tax),
                        'value_sub_total': ("%.2f" % value_sub_total),
                        'order_id': rec_data.id,
                    }))

                # Procesar los datos de envío
                shippingDataList = []
                shipping_data_address = order_data['shippingData']['address']
                logisticsInfo = order_data['shippingData']['logisticsInfo']

                # Procesar solo una vez los datos de logística
                if logisticsInfo:
                    # Tomar el primer valor de logisticsInfo si existen múltiples valores
                    selectedSla = logisticsInfo[0]['selectedSla']
                    shippingEstimateDate = logisticsInfo[0].get('shippingEstimateDate', '')
                    shippingEstimate = logisticsInfo[0].get('shippingEstimate', '')
                    deliveryCompany = logisticsInfo[0].get('deliveryCompany', '')

                    # Procesar deliveryIds
                    courierId = ''
                    courierName = ''
                    warehouseId = ''
                    accountCarrierName = ''
                    if logisticsInfo[0].get('deliveryIds'):
                        delivery = logisticsInfo[0]['deliveryIds'][0]  # Solo tomar el primer deliveryId si existen múltiples
                        courierId = delivery.get('courierId', '')
                        courierName = delivery.get('courierName', '')
                        warehouseId = delivery.get('warehouseId', '')
                        accountCarrierName = delivery.get('accountCarrierName', '')

                    # Procesar trackingHints
                    trackingHintsIds = order_data['shippingData'].get('trackingHints', [])
                    courierNametrackingH = ''
                    trackingIdtrackingH = ''
                    trackingLabeltrackingH = ''
                    trackingUrltrackingH = ''
                    if trackingHintsIds:
                        trackingHint = trackingHintsIds[0]  # Solo tomar el primer trackingHint si existen múltiples
                        courierNametrackingH = trackingHint.get('courierName', '')
                        trackingIdtrackingH = trackingHint.get('trackingId', '')
                        trackingLabeltrackingH = trackingHint.get('trackingLabel', '')
                        trackingUrltrackingH = trackingHint.get('trackingUrl', '')

                    # Insertar los datos de envío una sola vez
                    postal_code = shipping_data_address.get('postalCode', '000')
                    shippingDataList.append((0, 0, {
                        'type_contact': 'delivery',
                        'receiverName': shipping_data_address['receiverName'],
                        'addressType': shipping_data_address['addressType'],
                        'postalCode': postal_code,
                        'city': shipping_data_address['city'],
                        'state': shipping_data_address['state'],
                        'country': shipping_data_address['country'],
                        'street': shipping_data_address['street'],
                        'number': shipping_data_address['number'],
                        'neighborhood': shipping_data_address['neighborhood'],
                        'complement': shipping_data_address['complement'],
                        'reference': shipping_data_address['reference'],
                        'shippingEstimateDate': shippingEstimateDate,
                        'shippingEstimate': shippingEstimate,
                        'deliveryCompany': deliveryCompany,
                        'courierId': courierId,
                        'courierName': courierName,
                        'warehouseId': warehouseId,
                        'accountCarrierName': accountCarrierName,
                        'order_id': rec_data.id,
                    }))

                # Procesar los pagos
                paymentsListAdd = []
                paymentData = order_data.get('paymentData', {}).get('transactions', [])
                for transaction in paymentData:
                    payments = transaction['payments']
                    for payment in payments:
                        paymentsListAdd.append((0, 0, {
                            'id_payment_data': payment.get('id'),
                            'paymentSystem': payment.get('paymentSystem'),
                            'paymentSystemName': payment.get('paymentSystemName'),
                            'valuepaymentS': payment.get('value'),
                            'referenceValue': payment.get('referenceValue'),
                            'order_id': rec_data.id,
                        }))
                
                # Crear Pago si la configuración lo permite
                res_payment_val = False
                if get_config['sync_payment_auto']:
                    vals_payment = {
                        'name': str(orderId),
                        'partner_id': partner.id,
                        'amount': float(order_data['value']) / 100,
                        'date': sale_order.date_order,
                        'order_vtex_id': rec_data.id,
                    }
                    res_payment = payment_vtex.sudo().create(vals_payment)
                    res_payment_val = res_payment.id
                else: 
                    res_payment_val = False

                # Actualizar la orden VTEX con los datos adicionales
                vals_update = {
                    'items_ids': item_values,
                    'total_ids': totals_values,
                    'contact_ids': shippingDataList,
                    'payment_ids': paymentsListAdd,
                    'sale_order_id': sale_order.id,
                    'sync_ok': True,
                    'state': 'validate',
                    'payment_vtex_id_mp': res_payment_val,
                    'result': json.dumps(order_data, indent=4, separators=(". ", " = ")),  # Guardar el JSON completo de order_data
                }

                # Lógica de procesamiento de picking (si existe o no)
                picking = self.env['stock.picking'].search([('sale_id', '=', sale_order.id)], limit=1)
                if picking:
                    vals_update['stock_picking_id'] = picking.id
                    _logger.info(f'Existe entrega para {orderId} - {picking.name}')

                rec_data.sudo().write(vals_update)
                _logger.info(f'Actualizada la orden {orderId} con los datos de la entrega y otros campos.')

            
        except Exception as e:
            _logger.error(f"Error en la sincronización: {str(e)}")
            raise ValidationError(f"Error en la sincronización: {str(e)}")



    def _get_type_disc(self,name_disc,model_tag):
        type_route = False
        res = model_tag.search([('active','=',True)])
        for rec in res:
            if rec.name in name_disc:      
                type_route = rec.type_route

        return type_route

    def _get_price_disc(self,value_item,qty):
        return abs(float(value_item) / 100 ) / qty
