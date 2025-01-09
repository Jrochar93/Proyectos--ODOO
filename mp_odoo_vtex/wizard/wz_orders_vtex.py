# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import xlrd
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import openpyxl
import base64
from io import BytesIO
import logging
from unidecode import unidecode
import http.client
import json
import logging

_logger = logging.getLogger(__name__)


class WzConfirmOrdersSaleVtex(models.TransientModel):
    _name = "wz.confirm.orders.sale.vtex"
    _description = "Confirmar multiple pedidos de ventas"

    order_ids_mp = fields.Many2many('vtex.orders', string='Pedidos de Venta')

    @api.onchange('order_ids_mp')
    def list_order_ids(self):
        list_orders = []
        for record in self.env['vtex.orders'].browse(self._context['active_ids']):
            if record.sale_order_id.state == 'draft':
                list_orders.append(record.id)
            else:
                if record.sale_order_id.state == 'sale':
                    raise ValidationError("El pedido de venta %s ya ha sido confirmado" % (record.sale_order_id.name))
        
        self.order_ids_mp = [(6,self,list_orders)]
            

    def confirm_vtex_to_order(self):
        session_company_id = self.env.user.company_id
        get_config = self.env['config.vtex.access'].get_config_vtex()
        vtex_validator_products = self.env['vtex.validator.products']
        vtex_order = self.env['vtex.orders']

        if get_config == {}:
            raise ValueError("No ha encontrado una configuración para la sincronización valida, contactar con administrador")
        else:
            conn = http.client.HTTPSConnection(get_config['url_access'])
            selectedSla_location_id = False
            for record in self.order_ids_mp:
                if record.sale_order_id and record.sale_order_id.state == 'draft':
                    #confirmar a pedido de venta
                    record.sale_order_id.action_confirm()



class WzSyncMultipleOrdersVtex(models.TransientModel):
    _name = "wz.sync.multiple.orders.vtex"
    _description = "Sincronizar multiple pedidos de ventas"

    order_ids_mp = fields.Many2many('vtex.orders',  'order_cofirm_vtex_wz', string='Pedidos de Venta')
    order_to_invoice_ids_mp = fields.Many2many('vtex.orders', 'order_invoices_vtex_wz',string='Pedidos de Venta')
    order_to_handling_ids_mp = fields.Many2many('vtex.orders', 'order_handling_vtex_wz',string='Pedidos de Venta')



    @api.onchange('order_ids_mp')
    def list_order_ids(self):
        list_orders = []
        for record in self.env['vtex.orders'].browse(self._context['active_ids']):
            if record.state == 'draft':
                list_orders.append(record.id)
            else:
                raise ValidationError("La orden %s ya ha sido sincronizada" % (record.name))


        self.order_ids_mp = [(6,self,list_orders)]

    @api.onchange('order_to_invoice_ids_mp')
    def list_order_to_invoice_ids_mp(self):
        list_orders = []
        for record in self.env['vtex.orders'].browse(self._context['active_ids']):
            if record.state == 'validate' and record.status != 'invoiced':
                list_orders.append(record.id)
            else:
                raise ValidationError("La orden %s ya ha sido sincronizada" % (record.name))


        self.order_to_invoice_ids_mp = [(6,self,list_orders)]



    @api.onchange('order_to_handling_ids_mp')
    def list_order_to_handling_ids_mp(self):
        list_orders = []
        for record in self.env['vtex.orders'].browse(self._context['active_ids']):
            if record.status != 'handling':
                list_orders.append(record.id)
            else:
                raise ValidationError("La orden %s ya ha sido sincronizada" % (record.name))


        self.order_to_handling_ids_mp = [(6,self,list_orders)]


    def sync_multiple_orders(self):
        for record in self.order_ids_mp:
            if record.state == 'draft':
                record.sync_order()
    
    def sync_invoice_orders(self):
        for record in self.order_to_invoice_ids_mp:
            if record.state == 'validate':
                record.sync_order_invoiced()

    def sync_handling_orders(self):
        for record in self.order_to_handling_ids_mp:
            if record.state == 'validate':
                record.sync_start_handling()



class WzGeProductsVtex(models.TransientModel):
    _name = "wz.get.products.vtex"
    _description = "Sincronizar masivo productos"

    from_id = fields.Integer('Desde')
    to_id = fields.Integer('Hasta')
    validate_exist = fields.Boolean('Validar Existentes',default=False)

    def get_ref_id_vtex(self):
        session_company_id = self.env.user.company_id
        get_config = self.env['config.vtex.access'].get_config_vtex()
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
            validate_exist = self.validate_exist
            payload = ''
            _logger.info('Inicio Cron funcion buscar productos')
            conn.request("GET", "/api/catalog_system/pvt/products/GetProductAndSkuIds?_from="+str(self.from_id)+"&_to="+str(self.to_id),  payload, headers)
            res = conn.getresponse()
            data = res.read()
            product_dicts = json.loads(data)
            list_products_data = []

            list_products_data = product_dicts['data']
            list_products_range = product_dicts['range']['total']

            

            cont = int(self.from_id)
            for i in range(len(list_products_data)):
                if cont <= int(self.to_id):
                    list_sku = []
                    id_vtex = list_products_data[str(cont)]
                    list_sku = list_products_data[str(cont)]
                    for i2 in range(len(list_sku)):
                        id_vtex2 = list_sku[i2]
                        if id_vtex2:
                            conn.request("GET", "/api/catalog/pvt/product/"+str(id_vtex2), payload, headers)  
                            _logger.info('Buscando producto '+str(id_vtex2))
                            res_p = conn.getresponse()
                            data_p = res_p.read()
                            if data_p.decode("utf-8") != '':
                                product_dicts_data = json.loads(data_p)  
                                ref_internal_vtex = product_dicts_data['RefId']
                                search_p = self.env['product.template'].search([
                                                                                '&',
                                                                                ('default_code','=',str(ref_internal_vtex)),
                                                                                ('sync_vtex','=',validate_exist)
                                                                                ])
                                if search_p:
                                    conn.request("GET", "/api/catalog_system/pvt/products/productgetbyrefid/"+str(ref_internal_vtex), 
                                    payload, headers)
                                    dict_upt = {}
                                    dict_sku = ''
                                    res_p_vtex = conn.getresponse()
                                    data_p_vtex = res_p_vtex.read()
                                    if res_p_vtex.status == 200:
                                        _logger.info('Update producto '+str(ref_internal_vtex))
                                        dict_product = json.loads(data_p_vtex)
                                        dict_upt['ref_id_vtex'] = dict_product['Id']
                                        dict_upt['vtex'] = True
                                        dict_upt['sync_vtex'] = True
                                        dict_upt['response_data'] = (json.dumps(dict_product, indent=4, separators=(". ", " = "))),

                                        if 'BrandId' in dict_product:
                                            id_brand = self.env['vtex.brand'].search([('brand_id','=',str(dict_product['BrandId']))])
                                            dict_upt['brand_vtex_id'] = id_brand.id
                                        if 'CategoryId' in dict_product:
                                            id_category = self.env['vtex.category'].search([('category_id','=',str(dict_product['CategoryId']))])
                                            dict_upt['categ_vtex_id'] = id_category.id

                                        if 'Description' in dict_product:
                                            dict_upt['description_e_commerce'] = dict_product['Description']
                                        if 'DescriptionShort' in dict_product:
                                            dict_upt['description_short'] = dict_product['DescriptionShort']
                                                    


                                        # search sku
                                        conn.request("GET", "/api/catalog/pvt/stockkeepingunit?refId="+str(dict_product['RefId']), payload, headers)

                                        res_sku = conn.getresponse()
                                        data_sku = res_sku.read()

                                        if data_sku:
                                            dict_sku = json.loads(data_sku)
                                            dict_upt['ref_id_vtex_sku'] = dict_sku['Id']
                                            dict_upt['is_sku_mp'] = True
                                            dict_upt['product_sku_id'] = search_p.id

                                        if 'BrandId' in dict_product:
                                            id_brand = self.env['vtex.brand'].search([('brand_id','=',str(dict_product['BrandId']))])
                                            dict_upt['brand_vtex_id'] = id_brand.id, 

                                        search_p.write(dict_upt)
                                    else:
                                        # search sku
                                        conn.request("GET", "/api/catalog/pvt/stockkeepingunit?refId="+str(ref_internal_vtex), payload, headers)
                                        res_sku = conn.getresponse()
                                        data_sku = res_sku.read()
                                        _logger.info('Update SKU '+str(ref_internal_vtex))
                                        if data_sku:
                                            dict_sku = json.loads(data_sku)
                                            dict_upt['ref_id_vtex_sku'] = dict_sku['Id']
                                            dict_upt['is_sku_mp'] = True
                                            dict_upt['vtex'] = True
                                            dict_upt['ref_id_vtex'] = dict_sku['ProductId']

                                            # search by id product
                                            conn.request("GET", "/api/catalog/pvt/product/"+str(dict_sku['ProductId']), payload, headers)
                                            res_product = conn.getresponse()
                                            data_product = res_product.read()

                                            if res_product.status == 200:
                                                if data_product:
                                                    dict_product = json.loads(data_product)
                                                    if 'BrandId' in dict_product:
                                                        id_brand = self.env['vtex.brand'].search([('brand_id','=',str(dict_product['BrandId']))])
                                                        dict_upt['brand_vtex_id'] = id_brand.id
                                                    if 'CategoryId' in dict_product:
                                                        id_category = self.env['vtex.category'].search([('category_id','=',str(dict_product['CategoryId']))])
                                                        dict_upt['categ_vtex_id'] = id_category.id

                                                    if 'Description' in dict_product:
                                                        dict_upt['description_e_commerce'] = dict_product['Description']
                                                    if 'DescriptionShort' in dict_product:
                                                        dict_upt['description_short'] = dict_product['DescriptionShort']
                                cont = cont + 1


    
class WzGetOrdersVtex(models.TransientModel):
    _name = "wz.get.orders.vtex"
    _description = "Obtener pedidos de ventas"

    date_start = fields.Date('Fecha inicio')
    date_end = fields.Date('Fecha final')
    get_one_order = fields.Boolean('Buscar # Pedido',default=False)
    order_vtex = fields.Char('# Pedido')

    state_vtex = fields.Selection([
        ('waiting-for-sellers-confirmation', 'Waiting for seller confirmation'),
        ('payment-pending', 'Payment Pending'),
        ('payment-approved', 'Payment Approved'),
        ('ready-for-handling', 'Ready for Handling'),
        ('handling', 'Handling'),
        ('invoiced', 'Invoiced'),
        ('canceled', 'Canceled'),
    ], string='Estado VTEX')

    
    def get_orders_vtex(self):
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        config_discount = self.env['config.vtex.items.discount']
        config_discount_tag = self.env['config.vtex.tag.discount']
        _logger.info('Inicio Cron funcion # ready-for-handling')
        list_orders = []
        if get_config == {}:
            raise ValueError("No ha encontrado una configuración para la sincronización valida, contactar con administrador")
        else:
            conn = http.client.HTTPSConnection(get_config['url_access'])
            payload = ''
            headers = {
                    'Accept': "application/json",
                    'Content-Type': "application/json",
                    'X-VTEX-API-AppKey': str(get_config['api_key']),
                    'X-VTEX-API-AppToken': str(get_config['api_token']),
                    'vtexappkey-moreproducts-UZIUXU': str(get_config['account_name']),
            }
            list_orders = []
            config_discount = self.env['config.vtex.items.discount']

            # sync_orders_auto
            sync_orders_auto = get_config['sync_orders_auto']

            # BUSCAR SOLO UN PEDIDO
            if self.get_one_order == True:
                order_vtex = str(self.order_vtex)
                conn.request("GET", "/api/oms/pvt/orders/"+str(self.order_vtex), payload, headers)

                res_one = conn.getresponse()
                data_one = res_one.read()
                order_dicts_one = json.loads(data_one)
                list_orders = order_dicts_one

            else:
                conn.request("GET", "/api/oms/pvt/orders?f_creationDate=creationDate%3A%5B"+str(self.date_start)+"T00%3A01%3A00.000Z%20TO%20"+str(self.date_end)+"T23%3A59%3A59.999Z%5D&f_status="+str(self.state_vtex), payload, headers)
                res_range_date = conn.getresponse()
                data_range_date = res_range_date.read()
                order_dicts_data_range_date = json.loads(data_range_date)
                list_orders = order_dicts_data_range_date['list']


            if 'error' in list_orders:
                raise UserError("El numero de Orden  %s no se ha encontrado " % str(self.order_vtex)) 
            
            for i_order in range(len(list_orders)):
                #create Orders
                if self.get_one_order == True:
                    exist_order = self.env['vtex.orders'].search([('order','=',str(self.order_vtex))])
                    if not exist_order:
                        vals_create = {'name': str(self.order_vtex), 'order': str(self.order_vtex),'status': str(self.state_vtex)} 
                        res_create = self.env['vtex.orders'].sudo().create(vals_create)
                else:
                    exist_order = self.env['vtex.orders'].search([('order','=',str(order_dicts_data_range_date['list'][i_order]['orderId']))])
                    if not exist_order:
                        vals_create = {'name': order_dicts_data_range_date['list'][i_order]['orderId'] , 'order': order_dicts_data_range_date['list'][i_order]['orderId'],'status': str(self.state_vtex)} 
                        res_create = self.env['vtex.orders'].sudo().create(vals_create)

            last_search_order = self.env['vtex.orders'].search([ 
                                                                '&',
                                                                ('status','=', str(self.state_vtex)),
                                                                ('state','!=', 'validate'),
                                                                ])
            for rec_data in last_search_order:
                order_exist = self.env['vtex.orders'].search([('order','=',str(rec_data.name))])
                courierNametrackingH = trackingIdtrackingH = trackingLabeltrackingH = trackingUrltrackingH = fieldsListData = orderIdMarketplace_cd = paymentIdMarketplace_cd = collector_id_cd = total_paid_amount_cd = currency_id_cd = customData = shipment_id_cd = id_payment_data = paymentSystem = paymentSystemName = valuepaymentS =  referenceValue = ''

                # sync_orders_auto
                sync_orders_auto = get_config['sync_orders_auto']
                if order_exist:
                    # datos de la orden
                    conn.request("GET", "/api/oms/pvt/orders/"+str(rec_data.name), payload, headers)  
                    res = conn.getresponse()
                    data = res.read()
                    person_dict = json.loads(data)
                    items = person_dict['items']
                    
                    list_tags_price = []
                    item_values = []
                    discountTagList = []


                    price_total_vtex = price_without_tax = price_sub_total = price_discount_l_f = pd_l_without_tax = pd_l_without_tax = price_without_tax = price_sub_total = price_total = qt = price_unit = price_unit_without_tax = price_t_without_tax = 0

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
            
        _logger.info('Fin Cron funcion # ready-for-handling')

    def _get_type_disc(self,name_disc,model_tag):
        type_route = False
        res = model_tag.search([('active','=',True)])
        for rec in res:
            if rec.name in name_disc:      
                type_route = rec.type_route

        return type_route

    def _get_price_disc(self,value_item,qty):
        return abs(float(value_item) / 100 ) / qty


    def digito_verificacion(self,rut):
        factores = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
        #rut_ajustado=string.rjust(str(rut), 15, '0')
        rut_ajustado=str(rut).rjust( 15, '0')
        s = sum(int(rut_ajustado[14-i]) * factores[i] for i in range(14)) % 11
        if s > 1:
            return 11 - s
        else:
            return s
        
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

            """self.dev_ref = str(DigitoNIT)
            coeficientes = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
            sumatoria = 0
            cnt = 0
            dv = None
            # Convierte número en string y lo itera de atras hacia adelante
            for digito in str(numero)[::-1]:
                sumatoria += int(digito) * coeficientes[cnt]
                cnt += 1
            residuo = sumatoria % 11
            if residuo > 1:
                dv = 11 - residuo
            else:
                dv = residuo
            return dv"""

            return DigitoNIT

        
class WzValidateOrdersPaymentsInvoicedVtex(models.TransientModel):
    _name = "wz.validate.orders.payments.invoiced.vtex"
    _description = "Buscar y actualizar factura y pago en ordenes"

    start_date = fields.Date('Fecha de Inicio')
    end_date = fields.Date('Fecha de Inicio')

    type_process = fields.Selection([
        ('invoice', 'Factura'),
        ('payment', 'Pago'),
    ], string='Tipo de Proceso')


    def get_data_to_orders_vtex(self):
        vtex_orders = self.env['vtex.orders']
        payment_vtex_id_mp =  self.env['vtex.orders.payments']
        vals_updt = {}
        vals_updt_pay = {}
        

        res_orders = vtex_orders.search([
                                    '&',
                                    '&',
                                    ('create_date','>',self.start_date),
                                    ('create_date','<=',self.end_date),
                                    ('state','in',['validate'])
                                ])
        for rec in res_orders:
            # FACTURA 
            if self.type_process == 'invoice':
                if rec.sale_order_id and rec.sale_order_id.state == 'sale' and rec.state == 'validate': 
                    invoice_ids = rec.sale_order_id.invoice_ids
                    for rec_inv in invoice_ids:
                        if len(rec_inv) > 0:
                            # get id 
                            id_invoice = rec_inv.id or False
                            vals_updt['invoice_id'] = id_invoice
                            
                    rec.write(vals_updt)
                    vals_updt['invoice_id'] = False
            if self.type_process == 'payment':
                #pagos 
                if rec.sale_order_id and rec.sale_order_id.state == 'sale' and rec.state == 'validate': 
                    invoice_ids = rec.sale_order_id.invoice_ids
                    for rec_inv in invoice_ids:
                        if len(rec_inv) > 0:
                            # get id 
                            id_invoice = rec_inv.id or False
                            vals_updt_pay['invoice_id'] = id_invoice
                            vals_updt_pay['order_vtex_id'] = rec.id
                            
                        res_pay = payment_vtex_id_mp.search([('order_vtex_id','=',rec.id)])
                        if res_pay:
                            res_pay.write(vals_updt_pay)
                        vals_updt_pay['invoice_id'] = False
                        vals_updt_pay['order_vtex_id'] = False


            
