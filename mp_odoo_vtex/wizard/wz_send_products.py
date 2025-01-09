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
  
    
class WzSendProductsVtex(models.TransientModel):
    _name = "wz.send.product.vtex"

    products_ids_mp = fields.Many2many('product.template', 'products_sku_wz', string='Products')
    products_sku_ids_mp = fields.Many2many('product.template','products_template_sku_wz', string='Productos SKU')
    

    @api.onchange('products_ids_mp')
    def onchange_syn_ref_to_vtex(self):
        list_products = []
        for record in self.env['product.template'].browse(self._context['active_ids']):
            if record.ref_id_vtex == False or record.ref_id_vtex == '':
                list_products.append(record.id)
            else:
                raise ValidationError("El producto [%s] %s ya tiene el número en vtex" % (record.default_code,record.name))


        self.products_ids_mp = [(6,self,list_products)]


    @api.onchange('products_sku_ids_mp')
    def onchange_sync_sku_to_vtex(self):
        list_products = []
        for record in self.env['product.template'].browse(self._context['active_ids']):
            if record.ref_id_vtex == False:
                raise ValidationError("El producto [%s] %s no se encuentra el número en vtex" % (record.default_code,record.name))

            if record.ref_id_vtex_sku == False or record.ref_id_vtex_sku == '':
                list_products.append(record.id)
            else:
                raise ValidationError("El producto [%s] %s no tiene el número en vtex" % (record.default_code,record.name))


        self.products_sku_ids_mp = [(6,self,list_products)]


    def send_vtex(self):
        session_company_id = self.env.user.company_id
        company = self.env.company
        vtex_validator_products = self.env['vtex.validator.products']
        prod_prod = self.env['product.product']
        prod_temp = self.env['product.template']


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
            payload = ''
            mode = 'create'
            for rec in self:
                search_validator = vtex_validator_products.search([
                                                                    '&',
                                                                    ('type_request','=',mode),
                                                                    ('state','=','validate')
                                                                    ])

                if search_validator:
                    for rec_freq in search_validator.field_products_ids:
                        req_1 = str(rec_freq.name)
                        sear_req = prod_temp.search_read([
                                                ('id','=',rec.products_ids_mp.id)
                                                ],[req_1])
                        if sear_req:
                            if sear_req[0][req_1] == False:
                                raise UserError("Segun la validacion para E-commerce este campo es requerido %s " % rec_freq.name)
                
                data_product = {
                        "Name": str(rec.products_ids_mp.name),
                        "DepartmentId": '1',
                        "CategoryId": str(rec.products_ids_mp.categ_vtex_id.category_id),
                        "BrandId": str(rec.products_ids_mp.brand_vtex_id.brand_id),
                        "LinkId": str(rec.products_ids_mp.name),
                        "RefId":  str(rec.products_ids_mp.default_code),
                        "IsVisible": 'false',
                        "Description": str(rec.products_ids_mp.description_e_commerce),
                        "DescriptionShort": str(rec.products_ids_mp.name),
                        "Title": str(rec.products_ids_mp.name),
                        "IsActive": 'false',
                        #"MetaTagDescription": "tag testing",
                        "SupplierId": '1',
                        "ShowWithoutStock": 'true',
                        "AdWordsRemarketingCode": 'null',
                        "LomadeeCampaignCode": 'null',
                        #"Score": 1
                    }
                        
                data_product_f = json.dumps(data_product)
                #conn.request("POST", "/api/catalog/pvt/product", data_product_f, headers)
                res_product = conn.getresponse()
                data_product = res_product.read()
                data_sku = {}
                if data_product:
                    dict_data = json.loads(data_product)
                    IdRefProduct = dict_data['Id']
                    data_sku = {
                            "Name": str(rec.products_ids_mp.name),
                            "ProductId": str(IdRefProduct),
                            "RefId":  str(rec.products_ids_mp.default_code),
                            "IsActive": 'false',
                            "ActivateIfPossible": 'true',
                            "Name": str(rec.products_ids_mp.name),
                            "Ean": str(rec.products_ids_mp.barcode),
                            "PackagedHeight": '10',
                            "PackagedLength": '10',
                            "PackagedWidth": '10',
                            "PackagedWeightKg": '10',
                            "Height": '0',
                            "Length": '0',
                            "Width": '0',
                            "WeightKg": '0',
                            "CubicWeight": '0.1667',
                            "IsKit": 'false',
                            "ManufacturerCode": "123",
                            "CommercialConditionId": '1',
                            "MeasurementUnit": "un",
                            "UnitMultiplier": '2.0000',
                        }
                    
                    format_data_sku = json.dumps(data_sku)
                    #conn.request("POST", "/api/catalog/pvt/stockkeepingunit", format_data_sku, headers)
                    res_sku = conn.getresponse()
                    data_sku = res_sku.read()

                    if data_sku:
                        dict_sku = json.loads(data_sku)
                        rec.products_ids_mp.write({
                            'response_data_sku':  (json.dumps(dict_sku, indent=4, separators=(". ", " = "))),
                            'ref_id_vtex_sku': dict_sku['Id'],
                            'ref_id_vtex': IdRefProduct,
                            'vtex': True,
                            'sync_vtex': True,
                            })


    def request_create_product(self):
        session_company_id = self.env.user.company_id
        company = self.env.company
        vtex_validator_products = self.env['vtex.validator.products']
        prod_prod = self.env['product.product']
        prod_temp = self.env['product.template']
        obj_op = self.env['vtex.sync.operations']

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
            payload = ''
            mode = 'create'
            for rec in self.products_ids_mp:
                search_validator = vtex_validator_products.search([
                                                                    '&',
                                                                    ('type_request','=',mode),
                                                                    ('state','=','validate')
                                                                    ])

                if search_validator:
                    for rec_freq in search_validator.field_products_ids:
                        req_1 = str(rec_freq.name)
                        sear_req = prod_temp.search_read([
                                                ('id','=',rec.id)
                                                ],[req_1])
                        if sear_req:
                            if sear_req[0][req_1] == False:
                                raise UserError("Segun la validacion para E-commerce este campo es requerido %s " % rec_freq.field_description)
                
                data_product = {
                        "Name": str(rec.name),
                        "DepartmentId": '1',
                        "CategoryId": str(rec.categ_vtex_id.category_id),
                        "BrandId": str(rec.brand_vtex_id.brand_id),
                        "LinkId": str(rec.name),
                        "RefId":  str(rec.default_code),
                        "IsVisible": 'false',
                        "Description": str(rec.description_e_commerce),
                        "DescriptionShort": str(rec.name),
                        "Title": str(rec.name),
                        "IsActive": 'false',
                        "SupplierId": '1',
                        "ShowWithoutStock": 'true',
                        "AdWordsRemarketingCode": 'null',
                        "LomadeeCampaignCode": 'null',
                        #"Score": 1
                    }
                        
                data_product_f = json.dumps(data_product)


                json_request = data_product_f
                data_sku = {}
                if data_product:
                    IdRefProduct = False
                    data_sku = {
                            "Name": str(rec.name),
                            "ProductId": str(IdRefProduct),
                            "RefId":  str(rec.default_code),
                            "IsActive": 'false',
                            "ActivateIfPossible": 'true',
                            "Name": str(rec.name),
                            "Ean": str(rec.barcode),
                            "PackagedHeight": '1',
                            "PackagedLength": '1',
                            "PackagedWidth": '1',
                            "PackagedWeightKg": '1',
                            "Height": '0',
                            "Length": '0',
                            "Width": '0',
                            "WeightKg": '0',
                            "CubicWeight": '1',
                            "IsKit": 'false',
                            "ManufacturerCode": "",
                            "CommercialConditionId": '1',
                            "MeasurementUnit": "un",
                            "UnitMultiplier": '2.0000',
                        }
                    
                    format_data_sku = json.dumps(data_sku)
                    dict_op = {
                                'name': 'Solicitud de creación ['+str(rec.default_code)+"]-"+str(rec.name),
                                'id_ref_model': rec.id,
                                'id_ref_sync': rec.ref_id_vtex or False,
                                'id_ref_sync_other': rec.ref_id_vtex_sku or False,
                                'ref': "["+str(rec.default_code)+"]-"+str(rec.name),
                                'type_interface': 'product',
                                'type_request': 'create',
                                'json_request': str(json_request)+str(format_data_sku),
                                }
                    res_c = obj_op.sudo().create(dict_op)


    def request_create_product_sku(self):
        session_company_id = self.env.user.company_id
        company = self.env.company
        vtex_validator_products = self.env['vtex.validator.products']
        prod_prod = self.env['product.product']
        prod_temp = self.env['product.template']
        obj_op = self.env['vtex.sync.operations']

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
            payload = ''
            mode = 'create'
            for rec in self.products_sku_ids_mp:
                search_validator = vtex_validator_products.search([
                                                                    '&',
                                                                    ('type_request','=',mode),
                                                                    ('state','=','validate')
                                                                    ])

                if search_validator:
                    for rec_freq in search_validator.field_products_ids:
                        req_1 = str(rec_freq.name)
                        sear_req = prod_temp.search_read([
                                                ('id','=',rec.id)
                                                ],[req_1])
                        if sear_req:
                            if sear_req[0][req_1] == False:
                                raise UserError("Segun la validacion para E-commerce este campo es requerido %s " % rec_freq.field_description)

                data_sku = {}
                if not rec.ref_id_vtex: 
                    raise ValueError("No existe el Ref Id relacionado en el producto [%s] %s" % (rec.default_code, rec.name))
                else:
                    IdRefProduct = rec.ref_id_vtex
                    data_sku = {
                            "Name": str(rec.name),
                            "ProductId": str(IdRefProduct),
                            "RefId":  str(rec.default_code),
                            "IsActive": 'false',
                            "ActivateIfPossible": 'true',
                            "Name": str(rec.name),
                            "Ean": str(rec.barcode),
                            "PackagedHeight": '1',
                            "PackagedLength": '1',
                            "PackagedWidth": '1',
                            "PackagedWeightKg": '1',
                            "Height": '0',
                            "Length": '0',
                            "Width": '0',
                            "WeightKg": '0',
                            "CubicWeight": '1',
                            "IsKit": 'false',
                            "ManufacturerCode": "",
                            "CommercialConditionId": '1',
                            "MeasurementUnit": "un",
                            "UnitMultiplier": '2.0000',
                        }
                    
                    format_data_sku = json.dumps(data_sku)
                    dict_op = {
                                'name': 'Solicitud de creación SKU ['+str(rec.default_code)+"]-"+str(rec.name),
                                'id_ref_model': rec.id,
                                'id_ref_sync': rec.ref_id_vtex or False,
                                'id_ref_sync_other': rec.ref_id_vtex_sku or False,
                                'ref': "["+str(rec.default_code)+"]-"+str(rec.name),
                                'type_interface': 'sku_product',
                                'type_request': 'create',
                                'json_request': str(format_data_sku),
                                }
                    res_c = obj_op.sudo().create(dict_op)