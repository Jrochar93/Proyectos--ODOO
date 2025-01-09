# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import http.client
import json

import logging
_logger = logging.getLogger(__name__)




class ConfigVtexAccess(models.Model):
    _name = 'config.vtex.access'
    _description = 'Configuration of accessories to VTEX'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    url_access = fields.Char('Url')
    account_name = fields.Char('Account Name')
    environment = fields.Char('Environment')
    api_key = fields.Char('Api Key')
    api_token = fields.Char('Api Token')
    user = fields.Char('user')
    password = fields.Char('password')
    type_conexion = fields.Selection([
        ('test', 'Testing'),
        ('prod', 'Production'),
    ], string='Type Conexion')


    catalog_api_ids = fields.One2many('config.vtex.catalog.api', 'config_vtex_id', string='List Catalog API')

    
    # Config general
    product_shipment_id = fields.Many2one('product.template', string='Producto para envio', required=True)
    team_id = fields.Many2one('crm.team', string='Equipo de Ventas')
    warehouse_id = fields.Many2one('stock.warehouse', string='Almacén por defecto')
    origin_id = fields.Many2one('stock.location', string='Ubicacion por defecto')
    location_multiple = fields.Boolean('Multiple Ubicaciones',default=False)

    # Pedidos automaticos
    sync_orders_auto = fields.Boolean('Confirmar Pedidos Automaticos',default=False)
    sync_orders_handling_auto = fields.Boolean('Pedidos a Handling Automaticos',default=False)
    sync_order_to_invoiced = fields.Boolean('Facturación automática',default=False)
    days_to_review_invoiced = fields.Integer('Días validar facturas')


    journal_default_id = fields.Many2one('account.journal', string='Diario contable predeterminado')
    sync_payment_auto = fields.Boolean('Crear pago automatico',default=True)
    date_account = fields.Date('Fecha Contable')

    loc_multi_ids = fields.One2many('config.vtex.location.multi', 'config_vtex_id', string='Multiples Ubicaciones Origen')
    delivery_carrier_ids = fields.One2many('config.vtex.delivery.carrier', 'config_vtex_id', string='Métodos de envío')
    config_items_disc_ids = fields.One2many('config.vtex.items.discount', 'config_vtex_id', string='Etiquetas de Descuentos')

    config_tag_discounts_ids = fields.One2many('config.vtex.tag.discount', 'config_vtex_id', string='Tag de Descuentos')

    sale_channels_ids = fields.One2many('config.vtex.sales.team', 'config_vtex_id', string='Canales de Ventas')

    # pagos 
    config_pay_ids = fields.One2many('vtex.config.payments.orders', 'config_vtex_id', string='Pagos')

    # responsabilidades FE por defecto
    colombian_edi_codes_ids = fields.Many2many('l10n_co_edi.type_code', 'order_colombian_edi_code_vtex_df', string='Obligaciones y Responsabilidades FE',required=True)

    
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

    def get_config_vtex(self):
        act_company = self.env.company
        listD = []
        dict_data = {}
        headers = {}
        data_c = self.search([('company_id','=',act_company.id)])
        if data_c:
            dict_data = {
                'id': data_c.id,
                'environment': data_c.environment,
                'url_access': data_c.url_access,
                'api_key': data_c.api_key,
                'api_token': data_c.api_token,
                'account_name': data_c.account_name,
                'type_conexion': data_c.type_conexion,
                'valid' : True,
                'product_shipment_id': data_c.product_shipment_id or False,
                'loc_multi_ids': data_c.loc_multi_ids,
                'journal_default_id': data_c.journal_default_id,
                'sync_payment_auto': data_c.sync_payment_auto,
                'date_account': data_c.date_account,
                'delivery_carrier_ids': data_c.delivery_carrier_ids,
                'team_id': data_c.team_id,
                'sale_channels_ids': data_c.sale_channels_ids,
                'colombian_edi_codes_ids': data_c.colombian_edi_codes_ids,
                'config_pay_ids': data_c.config_pay_ids,
                'sync_orders_auto' : data_c.sync_orders_auto,
                'sync_orders_handling_auto': data_c.sync_orders_handling_auto,
            }


            return dict_data

    @api.model
    def _get_order_product_ref(self):
        pass
        
    def gen_view_regenerate_pays(self):
        try:
            form_view_id = self.env.ref("mp_odoo_vtex.wz_rec_pays_vtex_view_form").id
        except Exception as e:
            form_view_id = False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Recalcular Pagos',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wz.recalculate.orders.pays.vtex',
            'views': [(form_view_id, 'form')],
            'target': 'new',
        }

    def get_status_orders_payments_invoiced(self):
        try:
            form_view_id = self.env.ref("mp_odoo_vtex.wz_orders_payments_invoiced_view_form").id
        except Exception as e:
            form_view_id = False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Recalcular Facturas Facturas/Pagos de pedidos',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wz.validate.orders.payments.invoiced.vtex',
            'views': [(form_view_id, 'form')],
            'target': 'new',
        }


    @api.model
    def _get_order_ready_of_handing(self):
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        config_discount = self.env['config.vtex.items.discount']

        if get_config == {}:
            raise ValueError("No ha encontrado una configuración para la sincronización valida, contactar con administrador")
        else:
            conn = http.client.HTTPSConnection(get_config['url_access'])
            get_headers = {
                    'Accept': "application/json",
                    'Content-Type': "application/json",
                    'X-VTEX-API-AppKey': str(get_config['api_key']),
                    'X-VTEX-API-AppToken': str(get_config['api_token']),
                    'vtexappkey-moreproducts-UZIUXU': str(get_config['account_name']),
            }
            payload = ''

            conn.request("GET", "/api/oms/pvt/orders?f_status=ready-for-handling", payload, get_headers)
            res = conn.getresponse()
            data = res.read()
            order_dicts = json.loads(data)

        list_orders = order_dicts['list']
        for i_order in range(len(list_orders)):
            #create Orders
            exist_order = self.env['vtex.orders'].search([('order','=',str(order_dicts['list'][i_order]['orderId']))])

            if not exist_order:
                vals_create = {'name': order_dicts['list'][i_order]['orderId'] , 'order': order_dicts['list'][i_order]['orderId'],'status': 'ready-for-handling'} 
                res_create = self.env['vtex.orders'].sudo().create(vals_create)

        last_search_order = self.env['vtex.orders'].search([('status','=','ready-for-handling')])
        for rec_data in last_search_order:
            order_exist = self.env['vtex.orders'].search([('order','=',str(rec_data.name))])
            price_total_vtex = price_without_tax = price_sub_total = price_discount_l_f = pd_l_without_tax = pd_l_without_tax = price_without_tax = price_sub_total = price_total = qt = price_unit = price_unit_without_tax = price_t_without_tax = 0

            courierNametrackingH = trackingIdtrackingH = trackingLabeltrackingH = trackingUrltrackingH = ''

            if order_exist:
                # datos de la orden
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
                        for i_disc in range(len(list_tags_price)):
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
                                vals_discount = {
                                            'name': list_tags_price[i_disc]['name'],
                                            'identifier': list_tags_price[i_disc]['identifier'],
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
                                    
                            if (list_tags_price[i_disc]['name'] == name_discount or list_tags_price[i_disc]['identifier'] == identifier_discount) and not is_shipping_not_apply:
                                # descuento 
                                price_discount_l_f = abs(float(list_tags_price[i_disc]['value']) / 100 ) / qt
                                price_discount_l_value = abs(float(list_tags_price[i_disc]['value']) / 100 ) / qt

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

                # remove items old
                search_items = self.env['vtex.orders.items'].search([('order_id','=',rec_data.id)])
                if search_items:
                    for rec in search_items:
                        rec.unlink()

                search_totals = self.env['vtex.orders.totals'].search([('order_id','=',rec_data.id)])
                if search_totals:
                    for rec_t in search_totals:
                        rec_t.unlink()

                search_contacts = self.env['vtex.orders.contact'].search([('order_id','=',rec_data.id)])
                if search_contacts:
                    for rec_cont in search_contacts:
                        rec_cont.unlink()


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

                                'items_ids': item_values,
                                'total_ids': totals_values,
                                'contact_ids': shippingDataList,

                                }
                rec_data.write(vals_update)

    


    @api.model
    def _get_masters_data(self):
        # search brand
        category_model = self.env['vtex.category']
        category_specification= self.env['vtex.category.specification']
        _logger.info('Incio funcion # _get_masters_data')
        conn = http.client.HTTPSConnection("moreproducts.myvtex.com")
        payload = ''
        headers = {
        'X-VTEX-API-AppKey': 'vtexappkey-moreproducts-UZIUXU',
        'X-VTEX-API-AppToken': 'AWSDDYCEEWBFDDQYJQRZOWJSFBPADJUZQHAIHWULGTXOJNDCUTFVKVTWZPDJNAXBDRTZBSNNKJVNVXTUJWKCQDOMAXBZQFRNJNDOKWMBDOBQUNEKYDWFGHWTCDFWNATU',
        'vtexappkey-moreproducts-UZIUXU': 'vtexappkey-moreproducts-UZIUXU'
        }

        conn.request("GET", "/api/catalog_system/pvt/brand/list", payload, headers)

        res = conn.getresponse()
        data = res.read()
        person_dict = json.loads(data)
        brand_model = self.env['vtex.brand']
        for i in range(len(person_dict)):
            search_brand = brand_model.search([('brand_id','=',str(person_dict[i]['id']))])
            if not search_brand:
                vals_dict = {
                            'brand_id': person_dict[i]['id'],
                            'name': person_dict[i]['name'],
                            'is_active': person_dict[i]['isActive'],
                            'title': person_dict[i]['title'],
                            'meta_tag_description': person_dict[i]['metaTagDescription'],
                            'image_url': person_dict[i]['imageUrl'],
                }
                res_create_brand = brand_model.sudo().create(vals_dict)

        category_dict_f = {}
        for rang in range(1,300):
            conn.request("GET", "/api/catalog/pvt/category/"+(str(rang)), payload, headers)
            res = conn.getresponse()
            data_categ = res.read()
            if len(data_categ) > 0:
                category_dict_f = json.loads(data_categ)
                search_category = category_model.search([('category_id','=',str(category_dict_f['Id']))])
                parent_p = False
                if not search_category:
                    vals_cate_all = {
                                'category_id': category_dict_f['Id'],
                                'name': category_dict_f['Name'],
                                'has_children': category_dict_f['HasChildren'],
                                'title': category_dict_f['Title'],
                                'description': category_dict_f['Description'],
                                'keywords': category_dict_f['Keywords'],
                                'is_active': category_dict_f['IsActive'],
                                'global_category_id': category_dict_f['GlobalCategoryId'],
                                'father_category_id': category_dict_f['FatherCategoryId'],
                                'link_id': category_dict_f['LinkId'],
                                'parent_id': parent_p,
                    }
                    recorset_data = category_model.sudo().create(vals_cate_all) 

        search_cat = category_model.search([])
        for rec_upt in search_cat:
            res_parent_id = category_model.search([('father_category_id','=',rec_upt.father_category_id)],limit=1)
            if res_parent_id:
                rec_upt.write({'parent_id': res_parent_id.id })

        for rang2 in range(0,10):
            conn.request("GET", "/api/catalog_system/pub/category/tree/"+str(rang2), payload, headers)

            res = conn.getresponse()
            data_categ = res.read()
            category_dict = json.loads(data_categ)

        
        item_children_lv1 = []
        for ii in range(len(category_dict)):
            children = [] 
            item_children_lv1 =  category_dict[ii]['children']
            


        item_children = []
        for i in range(len(category_dict)):
            children = [] 
            conn.request("GET", "/api/catalog/pvt/category/"+(str(category_dict[i]['id'])), payload, headers)

            res_lv2 = conn.getresponse()
            data_lv2 = res_lv2.read()
            category_dict_lv2 = json.loads(data_lv2)

            search_category = category_model.search([('category_id','=',str(category_dict[i]['id']))])
            if not search_category:
                if category_dict[i]['hasChildren'] == True:
                    vals_dict_category = {
                                'category_id': category_dict[i]['id'],
                                'name': category_dict[i]['name'],
                                'has_children': category_dict[i]['hasChildren'],
                                'title': category_dict[i]['Title'],
                                'meta_tag_description': category_dict[i]['MetaTagDescription'],
                                'url': category_dict[i]['url'],
                    }

                    res_create_category_dict = category_model.sudo().create(vals_dict_category) 

        _logger.info('Fin funcion # _get_masters_data')

class ConfigVtexCatalogApi(models.Model):
    _name = 'config.vtex.catalog.api'
    _description = 'List Catalog API'

    name = fields.Char('Name')
    url_access = fields.Char('Url')
    method = fields.Selection([
        ('get', 'GET'),
        ('put', 'PUT'),
        ('post', 'POST'),
        ('patch', 'PATCH'),
        ('delete', 'DELETE'),
    ], string='Method')

    type_interface = fields.Selection([
        ('product', 'Products'),
        ('order', 'Orders'),
        ('inventory', 'Inventory'),
        ('pricelist', 'Priceslist'),
        ('brand', 'Brand'),
        ('category', 'Category'),
    ], string='Type interface')

    config_vtex_id = fields.Many2one('config.vtex.access', string='Config VTEX')

class ConfigVtexLocationMulti(models.Model):
    _name = 'config.vtex.location.multi'
    _description = 'Multiples Ubicaciones Origen'

    name = fields.Char('Valor condicional',required=True)
    origin_id = fields.Many2one('stock.location', string='Ubicacion por defecto',required=True)

    config_vtex_id = fields.Many2one('config.vtex.access', string='Config VTEX')

class ConfigVtexDeliveryCarrier(models.Model):
    _name = 'config.vtex.delivery.carrier'
    _description = 'Metodos de Envio'

    name = fields.Char('Valor condicional',required=True)
    url_delivery = fields.Char('URL')
    add_number_guide = fields.Boolean('Agregar Nro Guía')
    delivery_carrier_id = fields.Many2one('delivery.carrier', string='Método de envío',required=True)

    config_vtex_id = fields.Many2one('config.vtex.access', string='Config VTEX')

class ConfigVtexItemsDiscount(models.Model):
    _name = 'config.vtex.items.discount'
    _description = 'Items de descuentos'

    name = fields.Char('Name')
    identifier = fields.Char('identifier')
    active = fields.Boolean('Active',default=True)
    is_shipping_not_apply = fields.Boolean('N/A Descuento de Envio',default=True)

    config_vtex_id = fields.Many2one('config.vtex.access', string='Config VTEX')


class ConfigVtexTagDiscount(models.Model):
    _name = 'config.vtex.tag.discount'
    _description = 'Tag de descuentos'

    name = fields.Char('Name')
    active = fields.Boolean('Active',default=True)

    type_route = fields.Selection([
        ('seller', 'seller price'),
        ('shipping_marketplace', 'shipping marketplace'),
        ('price', 'price'),
        ('shipping', 'shipping'),
        ('marketplace', 'marketplace'),
    ], string='Tipo de Ruta')

    config_vtex_id = fields.Many2one('config.vtex.access', string='Config VTEX')

class ConfigVtexSalesTeam(models.Model):
    _name = 'config.vtex.sales.team'
    _description = 'Canal de Ventas '

    channel_sale_id_mp = fields.Many2one('sale.channels', string='Canal de Venta')
    name = fields.Char('Nombre condicional',required=True)

    config_vtex_id = fields.Many2one('config.vtex.access', string='Config VTEX')

class VtexBrand(models.Model):
    _name = 'vtex.brand'
    _description = 'List Brand'

    brand_id = fields.Char('Brand Id')
    name = fields.Char('Name')
    is_active = fields.Boolean('is Active')
    title = fields.Char('Title')
    meta_tag_description = fields.Char('Meta Tag Description')
    image_url = fields.Char('Image Url')
    commercial_user_id = fields.Many2one('res.users', string='Vendedor', domain="[('active','=',True)]")

    def name_get(self):
        result = []
        for record in self:
            if record.brand_id:
                name = '['+str(record.brand_id)+'] ' + str(record.name)
            else:
                name = record.name
            
            result.append((record.id, name))
        return result
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = [
                '|', '|',('brand_id', '=ilike', name), ('name', operator, name), ('title', operator, name)
            ]
        records = self.search(domain + args, limit=limit)
        return records.name_get()



class VtexCategory(models.Model):
    _name = 'vtex.category'
    _description = 'List Category'

    category_id = fields.Char('Category Id')
    name = fields.Char('Name')
    has_children = fields.Boolean('Has Children')
    url = fields.Char('Url')
    title = fields.Char('Title')
    meta_tag_description = fields.Char('Meta Tag Description')
    description = fields.Char('Description')
    keywords = fields.Char('Keywords')
    is_active = fields.Boolean('IsActive')
    global_category_id = fields.Char('GlobalCategoryId')
    father_category_id = fields.Char('FatherCategoryId')
    link_id = fields.Char('LinkId')
    parent_id = fields.Many2one('vtex.category', string='Padre')

    category_specification_ids = fields.One2many('vtex.category.specification', 'category_id', string='Category Specification')
   
    def name_get(self):
        result = []
        for record in self:
            if record.category_id:
                name = '['+str(record.category_id)+'] ' + str(record.name)
            else:
                name = record.name
            
            result.append((record.id, name))
        return result
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = [
                '|', '|',('category_id', '=ilike', name), ('name', operator, name), ('title', operator, name)
            ]
        records = self.search(domain + args, limit=limit)
        return records.name_get()


class VtexCategorySpecification(models.Model):
    _name = 'vtex.category.specification'
    _description = 'List Category'

    categ_specification_id = fields.Char('Category Specification Id')
    name = fields.Char('Name')
    has_children = fields.Boolean('Has Children')
    url = fields.Char('Url')
    title = fields.Char('Title')
    meta_tag_description = fields.Char('Meta Tag Description')

    category_id = fields.Many2one('vtex.category', string='Category')



class VtexProductCategorySpecs(models.Model):
    _name = 'vtex.product.category.specs'
    _description = 'List Category'
    _rec_name = 'Name'

    Name = fields.Char('Name')
    CategoryId = fields.Char('CategoryId')
    FieldId = fields.Char('FieldId')
    IsActive = fields.Boolean('IsActive')
    IsStockKeepingUnit = fields.Boolean('IsStockKeepingUnit')

    category_id = fields.Many2one('vtex.category', string='Category')

    FieldTypeId = fields.Char('FieldTypeId')
    FieldGroupId = fields.Char('FieldGroupId')
    Description = fields.Char('Description')
    
    Position = fields.Char('Position')
    IsFilter = fields.Char('IsFilter')
    IsRequired = fields.Char('IsRequired')

    IsOnProductDetails = fields.Char('IsOnProductDetails')
    IsSideMenuLinkActive = fields.Char('IsSideMenuLinkActive')
    IsWizard = fields.Char('IsWizard')

    IsSideMenuLinkActive = fields.Char('IsSideMenuLinkActive')
    DefaultValue = fields.Char('DefaultValue')

    sku_values_ids = fields.One2many('vtex.sku.map.specs', 'specs_id', string='Sku Values')

    def _get_product_specs(self):
        session_company_id = self.env.user.company_id
        company = self.env.company
        get_config = self.env['config.vtex.access'].get_config_vtex()
        vtex_validator_products = self.env['vtex.validator.products']
        prod_prod = self.env['product.product']
        prod_temp = self.env['product.template']
        category_model = self.env['vtex.category']
        specs_product_model = self.env['vtex.product.category.specs']
        mode = 'search_specs'

        if get_config == {}:
            raise ValueError("No ha encontrado una configuración para la sincronización valida, contactar con administrador")
        else:
            conn = http.client.HTTPSConnection(get_config['url_access'])
            get_headers = {
                    'Accept': "application/json",
                    'Content-Type': "application/json",
                    'X-VTEX-API-AppKey': str(get_config['api_key']),
                    'X-VTEX-API-AppToken': str(get_config['api_token']),
                    'vtexappkey-moreproducts-UZIUXU': str(get_config['account_name']),
            }
            payload = ''
            search_categ_vtex = category_model.search([('category_id','!=',False)])
            for rec in search_categ_vtex:
                conn.request("GET", "/api/catalog_system/pub/specification/field/listTreeByCategoryId/"+str(rec.category_id)+"", payload, get_headers)
                data_dict = {}
                dict_sku = ''
                res = conn.getresponse()
                data = res.read()
                category_dict = json.loads(data)
                for i in range(len(category_dict)):
                    specs_products = self.search([('FieldId','=',str(category_dict[i]['FieldId']))])
                    children = [] 
                    sku_val = []
                    sku_item_values = []

                    if not specs_products:
                        conn.request("GET", "/api/catalog/pvt/specification/"+str(category_dict[i]['FieldId']), payload, get_headers)

                        dict_specification = {}
                        res_specification = conn.getresponse()
                        data_specification = res_specification.read()
                        dict_specification = json.loads(data_specification)
                        
                        conn.request("GET", "/api/catalog_system/pub/specification/fieldvalue/"+str(category_dict[i]['FieldId'])+"", payload,get_headers)
                        sku_values = conn.getresponse()
                        data_sku_values = sku_values.read()
                        dict_sku_values = json.loads(data_sku_values)

                        _logger.info('dict_specification',dict_specification)

                        # set Color
                        if category_dict[i]['FieldId'] == '18' or category_dict[i]['FieldId'] == 18:
                            for i_sku in range(len(dict_sku_values)):
                                sku_item_values.append((0,self,{
                                                            'FieldValueId': dict_sku_values[i_sku]['FieldValueId'],
                                                            'Value': dict_sku_values[i_sku]['Value'],
                                                            'IsActive': dict_sku_values[i_sku]['IsActive'],
                                                            'Position': dict_sku_values[i_sku]['Position'],
                                                            'FieldId': category_dict[i]['FieldId'],

                                }))

                        
                        vals_dict = {
                                    
                                    'Name': category_dict[i]['Name'],
                                    'CategoryId': category_dict[i]['CategoryId'],
                                    'FieldId': category_dict[i]['FieldId'],
                                    'IsActive': category_dict[i]['IsActive'],
                                    'IsStockKeepingUnit': category_dict[i]['IsStockKeepingUnit'],
                                    'FieldTypeId': dict_specification['FieldTypeId'],
                                    'FieldGroupId': dict_specification['FieldGroupId'],
                                    'Description': dict_specification['Description'],
                                    'Position': dict_specification['Position'],
                                    'IsFilter': dict_specification['IsFilter'],
                                    'IsRequired': dict_specification['IsRequired'],
                                    'IsOnProductDetails': dict_specification['IsOnProductDetails'],
                                    'IsSideMenuLinkActive': dict_specification['IsSideMenuLinkActive'],
                                    'IsWizard': dict_specification['IsWizard'],
                                    'IsSideMenuLinkActive': dict_specification['IsSideMenuLinkActive'],
                                    'DefaultValue': dict_specification['DefaultValue'],
                                    'category_id': rec.id,
                                    'sku_values_ids': sku_item_values,
                        }
                        res_create_brand = self.sudo().create(vals_dict)

class VtexSkuMapSpecs(models.Model):
    _name = 'vtex.sku.map.specs'
    _description = 'Sku Map Values'
    _rec_name = 'FieldValueId'

    FieldValueId = fields.Char('FieldValueId')
    Value = fields.Char('Value')
    IsActive = fields.Char('IsActive')
    Position = fields.Char('Position')
    FieldId = fields.Char('FieldId')

    specs_id = fields.Many2one('vtex.product.category.specs', string='Specs')


class VtexSkuMapSpecs(models.Model):
    _name = 'vtex.config.trade.policy'
    _description = 'Lista de Trade policies'

    name = fields.Char('Nombre')    
    id_vtex = fields.Integer('Trade Policy')


class VtexConfigPaymentsOrders(models.Model):
    _name = 'vtex.config.payments.orders'
    _description = 'Config Order Payments'

    
    account_id = fields.Many2one('account.account', string='Cuenta')
    apply_type = fields.Selection([
        ('sale', 'Factura'),
        ('payment', 'Pago'),
        ('iva', 'Iva'),
        ('ica', 'Ica'),
        ('rtfte', 'Rtfte'),
        ('commision', 'Comisión'),
        ('shipping', 'Envio'),
        ('pricelist', 'Tarifa'),
    ], string='Aplica a')

    affects_pay = fields.Selection([
        ('debit', 'Debito'),
        ('credit', 'Credito'),
    ], string='Afecta a')

    config_vtex_id = fields.Many2one('config.vtex.access', string='Config VTEX')
