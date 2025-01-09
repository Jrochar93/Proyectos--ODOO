# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import http.client
import json
import logging

_logger = logging.getLogger(__name__)




class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vtex = fields.Boolean('VTEX',default=False, help="Indicar si producto se sincroniza con E-commerce VTEX")
    ref_id_vtex = fields.Char('Id Ref VTEX')
    ref_id_vtex_sku = fields.Char('Id SKU VTEX')
    sync_vtex = fields.Boolean('Sync VTEX',default=False)

    is_sku_mp = fields.Boolean('Es SKU',default=False)
    product_sku_id = fields.Many2one('product.template', string='Producto Padre')
    
    brand_vtex_id = fields.Many2one('vtex.brand', string='Marca VTEX')
    categ_vtex_id = fields.Many2one('vtex.category', string='Categoría VTEX')

    description_e_commerce = fields.Text('Descripción de producto E-commerce') 
    description_short = fields.Text('Descripción Corta E-commerce')  
    
    response_data = fields.Text('Response Data')
    response_data_sku = fields.Text('Response Data Sku')

    # Marca para para envio e-commerce

    trade_policies_ids = fields.Many2many('vtex.config.trade.policy', 'trade_policiy_product',string='Trade Policy E-commerce')
    

    @api.onchange('product_sku_id')
    def _onchange_product_sku_id(self):
        for rec in self:
            rec.ref_id_vtex = rec.product_sku_id.ref_id_vtex

    def send_vtex(self): 
        pass

    def update_vtex(self):
        pass

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
                        #"MetaTagDescription": "tag testing",
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
                    #conn.request("POST", "/api/catalog/pvt/stockkeepingunit", format_data_sku, headers)
                    #res_sku = conn.getresponse()
                    #data_sku = res_sku.read()

                    """if data_sku:
                        dict_sku = json.loads(data_sku)
                        rec.products_ids_mp.write({
                            'response_data_sku':  (json.dumps(dict_sku, indent=4, separators=(". ", " = "))),
                            'ref_id_vtex_sku': dict_sku['Id'],
                            'ref_id_vtex': IdRefProduct,
                            'vtex': True,
                            'sync_vtex': True,
                            })"""
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



    def search_id_vtex(self):
        session_company_id = self.env.user.company_id
        vtex_validator_products = self.env['vtex.validator.products']
        prod_prod = self.env['product.product']
        prod_temp = self.env['product.template']
        
        mode = 'search'
        conn = http.client.HTTPSConnection("moreproducts.myvtex.com")
        api_key = 'vtexappkey-moreproducts-UZIUXU'
        api_token = 'AWSDDYCEEWBFDDQYJQRZOWJSFBPADJUZQHAIHWULGTXOJNDCUTFVKVTWZPDJNAXBDRTZBSNNKJVNVXTUJWKCQDOMAXBZQFRNJNDOKWMBDOBQUNEKYDWFGHWTCDFWNATU'
        headers = {
            'Accept': "application/json",
            'Content-Type': "application/json",
            'X-VTEX-API-AppKey': str(api_key),
            'X-VTEX-API-AppToken': str(api_token),
            'vtexappkey-moreproducts-UZIUXU': 'vtexappkey-moreproducts-UZIUXU'
            }
        
        payload = ''
        conn.request("GET", "/api/catalog_system/pvt/products/productgetbyrefid/"+str(self.default_code), payload, headers)
        dict_upt = {}
        dict_sku = ''
        res = conn.getresponse()
        data = res.read()

        if res.status == 200:
            if data:
                dict_product = json.loads(data)
                dict_upt ={
                                    'ref_id_vtex': dict_product['Id'], 
                                    'sync_vtex':  True,
                                    'vtex': True,
                                    'response_data':  (json.dumps(dict_product, indent=4, separators=(". ", " = "))),
                                    'description_e_commerce': dict_product['Description'], 
                                    'description_short':  dict_product['DescriptionShort'], 

                                    }
                # search sku
                conn.request("GET", "/api/catalog/pvt/stockkeepingunit?refId="+str(dict_product['RefId']), payload, headers)

                res_sku = conn.getresponse()
                data_sku = res_sku.read()

                if data_sku:
                    dict_sku = json.loads(data_sku)
                    dict_upt['ref_id_vtex_sku'] = dict_sku['Id']
                    dict_upt['is_sku_mp'] = True
                    dict_upt['product_sku_id'] = self.id
                
                if 'BrandId' in dict_product:
                    id_brand = self.env['vtex.brand'].search([('brand_id','=',str(dict_product['BrandId']))])
                    dict_upt['brand_vtex_id'] = id_brand.id
                #cambio
                if 'CategoryId' in dict_product:
                    id_category = self.env['vtex.category'].search([('category_id','=',str(dict_product['CategoryId']))])
                    dict_upt['categ_vtex_id'] = id_category.id


        else:
            # search sku
            conn.request("GET", "/api/catalog/pvt/stockkeepingunit?refId="+str(self.default_code), payload, headers)
            res_sku = conn.getresponse()
            data_sku = res_sku.read()
            
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
        
        self.write(dict_upt)
        return self




    @api.model
    def write(self, vals):
        #vtex
        tag_olds = []
        field_olds = []
        for rec_old in self:
            if rec_old.vtex == True:
                for k, v in vals.items():
                    sh_old_d = self.search([('id','=',self.id)])

                search_old_d = self.search_read([('id','=',self.id)],tag_olds)
                if search_old_d:
                    field_olds.append((0,0,{
                        'field_old_id': str(k),
                        'field_old_value': str(v),
                    }))


        result = super(ProductTemplate, self).write(vals)

        for rec in self:
            if rec.vtex == True:
                # peticion a operaciones
                #https://{accountName}.{environment}.com.br/api/catalog/pvt/product/{productId}
                obj_op = self.env['vtex.sync.operations']

                field_new = []
                for k, v in vals.items():
                    str_fd = str(k)
                    field_new.append((0,0,{
                        'field_new_id': str(k),
                        'field_new_value': str(v),
                    }))

                dict_op = {
                        'name': 'Solicitud de Actualización ['+str(rec.default_code)+"]-"+str(rec.name),
                        'id_ref_model': rec.id,
                        'id_ref_sync': rec.ref_id_vtex or False,
                        'id_ref_sync_other': rec.ref_id_vtex_sku or False,
                        'ref': "["+str(rec.default_code)+"]-"+str(rec.name),
                        'type_interface': 'product',
                        'type_request': 'update',
                        'json_request': str(vals),
                        'op_fields_ids': field_olds,
                        }
                res_c = obj_op.sudo().create(dict_op)

        return result

