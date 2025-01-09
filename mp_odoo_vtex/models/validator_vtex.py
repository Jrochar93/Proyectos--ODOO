# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import http.client
import json

import logging
_logger = logging.getLogger(__name__)


class VtexValidatorProducts(models.Model):
    _name = 'vtex.validator.products'
    _description = 'Rules Validator Products VTEX'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')

    type_interface = fields.Selection([
        ('product', 'Products'),
        ('order', 'Orders'),
        ('inventory', 'Inventory'),
        ('pricelist', 'Priceslist'),
        ('brand', 'Brand'),
        ('category', 'Category'),
    ], string='Type interface')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validate'),
    ], string='State', tracking=True)

    type_request = fields.Selection([
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ], string='Type Request')

    model_id = fields.Many2one('ir.model', string='Model')
    name_model = fields.Char('Model', related='model_id.model')

    field_products_ids = fields.Many2many('ir.model.fields', string='Fields Required')

    field_mapped_ids = fields.One2many('vtex.validator.products.mapped', 'validator_products_id', string='Mapped Fields')


    def button_draft(self):
        for rec in self:
            rec.write({'state':'draft'})    

    def button_validate(self):
        for rec in self:
            rec.write({'state':'validate'})    

class VtexRulesValidatorRequest(models.Model):
    _name = 'vtex.rules.validator.request'
    _description = 'Rules Validate'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    validator_products_id = fields.Many2one('vtex.validator.products', string='Validator Products')


class VtexValidatorProductsMapped(models.Model):
    _name = 'vtex.validator.products.mapped'
    _description = 'Mappped products VTEX'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']


    field_id = fields.Many2one('ir.model.fields', string='Field Odoo', )
    name_technical = fields.Char('Name', related='field_id.name' )
    name_vtex = fields.Char('Name Vtex')


    validator_products_id = fields.Many2one('vtex.validator.products', string='Validator Products')




class VtexOperationsProducts(models.Model):
    _name = 'vtex.operations.request'
    _description = 'Request Products Operations'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')

    type_interface = fields.Selection([
        ('product', 'Products'),
        ('sku_product', 'Productos SKU'),
        ('order', 'Orders'),
        ('inventory', 'Inventory'),
        ('pricelist', 'Priceslist'),
        ('brand', 'Brand'),
        ('category', 'Category'),
    ], string='Type interface')

    type_request = fields.Selection([
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ], string='Type Request')

    fields_request = fields.Text('Fields Request')

    fields_request_send = fields.Text('Request Send')
    fields_request_response = fields.Text('Request Response')

    #validate_id = fields.Many2one('comodel_name', string='validate')
    

    
class VtexSyncOperations(models.Model):
    _name = 'vtex.sync.operations'
    _description = 'Sync Operations'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nombre')
    ref = fields.Char('Referencia')
    id_ref_model = fields.Char('Id Referencia Model')
    id_ref_sync = fields.Char('Id Referencia Sync')
    id_ref_sync_other = fields.Char('Id Referencia Sync 2')
    type_interface = fields.Selection([
        ('product', 'Products'),
        ('sku_product', 'Productos SKU'),
        ('order', 'Orders'),
        ('inventory', 'Inventory'),
        ('pricelist', 'Priceslist'),
        ('brand', 'Brand'),
        ('category', 'Category'),
    ], string='Type interface')

    type_request = fields.Selection([
        ('create', 'Al crear'),
        ('update', 'Al actualizar'),
        ('delete', 'Al eliminar'),
    ], string='Type Request')


    state = fields.Selection([
        ('draft', 'Borrador'),
        ('validate', 'Validado'),
        ('error', 'Error'),
        ('cancel', 'Cancelado'),
    ], string='State',default='draft')

    sync_ok = fields.Boolean('Sync ok',default=False)

    json_request = fields.Char('Json Request')
    json_response = fields.Char('Json Response')

    op_fields_ids = fields.One2many('vtex.operation.fields', 'sync_op_id', string='Op fields')


    def update_specs(self):
        pass

    def action_cancel(self):
        for rec in self:
            if rec.state == 'draft':
                rec.write({'state': 'cancel'})
    
    def sync_op(self):
        company = self.env.company
        session_company_id = self.env.user.company_id
        vtex_validator_products = self.env['vtex.validator.products']
        prod_prod = self.env['product.product']
        prod_temp = self.env['product.template']
        conn = http.client.HTTPSConnection("moreproducts.myvtex.com")
        get_config = self.env['config.vtex.access'].get_config_vtex()
        if get_config == {}:
            raise ValueError("No ha encontrado una configuración para la sincronización valida, contactar con administrador")
        else:
            conn = http.client.HTTPSConnection(get_config['url_access'])
            conn_product = http.client.HTTPSConnection(get_config['url_access'])
            conn_sku = http.client.HTTPSConnection(get_config['url_access'])
            conn_specs = http.client.HTTPSConnection(get_config['url_access'])
            conn_add_specs = http.client.HTTPSConnection(get_config['url_access'])
            conn_add_ean = http.client.HTTPSConnection(get_config['url_access'])
            conn_prd_trade_policy = http.client.HTTPSConnection(get_config['url_access'])
            
            headers = {
                    'Accept': "application/json",
                    'Content-Type': "application/json",
                    'X-VTEX-API-AppKey': str(get_config['api_key']),
                    'X-VTEX-API-AppToken': str(get_config['api_token']),
                    'vtexappkey-moreproducts-UZIUXU': str(get_config['account_name']),
            }
            payload = ''
        
            mode = 'create'
            dict_sku = []
            dict_response_sku = []
            Id_specs_put = False
            if mode == 'create':
                if self.type_interface == 'product':
                    IdRefProduct = ''
                    search_validator = vtex_validator_products.search([
                                                                        '&',
                                                                        ('type_request','=',mode),
                                                                        ('state','=','validate')
                                                                        ])
                    if search_validator:
                        for rec_freq in search_validator.field_products_ids:
                            req_1 = str(rec_freq.name)
                            sear_req = prod_temp.search_read([
                                                    ('id','=',self.id_ref_model)
                                                    ],[req_1])
                            if sear_req:
                                if sear_req[0][req_1] == False:
                                    raise UserError("Segun la validacion para E-commerce este campo es requerido %s " % rec_freq.name)
                    
                    # search data 
                    search_p = prod_temp.search([('id','=',self.id_ref_model)])
                    for record in search_p:
                        LinkId = str(record.name_web_mp)
                        LinkId_f = str(record.name_web_mp.lower())
                        data_product = {
                                "Name": str(record.name_web_mp),
                                "DepartmentId": str(record.categ_vtex_id.father_category_id),
                                "CategoryId": str(record.categ_vtex_id.category_id),
                                "BrandId": str(record.brand_vtex_id.brand_id),
                                "LinkId": LinkId_f,
                                "RefId":  str(record.default_code),
                                "IsVisible": 'false',
                                "Description": str(record.description_e_commerce),
                                "Title": str(record.name_web_mp),
                                "IsActive": 'true',
                                "IsVisible": 'true',
                                "ShowWithoutStock": 'false',
                            }
                                    
                        data_product_f = json.dumps(data_product)
                        conn_product.request("POST", "/api/catalog/pvt/product", data_product_f, headers)
                        res_product = conn_product.getresponse()
                        data_product = res_product.read()
                        data_sku = {}
                        if res_product.status == 200:
                            dict_data = json.loads(data_product)
                            IdRefProduct = dict_data['Id']
                            search_barcode = prod_prod.search([('default_code','=',record.default_code)],limit=1)
                
                            dict_data_sku = {
                                "Name": str(record.name_web_mp),
                                "ProductId": str(IdRefProduct),
                                "RefId":  str(record.default_code),
                                "IsActive": 'false',
                                "ActivateIfPossible": 'true',
                                "Ean": str(search_barcode.barcode),
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
                                "CommercialConditionId": '1',
                                "MeasurementUnit": "un",
                                "UnitMultiplier": '1.0000',
                            }
                            format_data_sku = json.dumps(dict_data_sku)
                            conn_sku.request("POST", "/api/catalog/pvt/stockkeepingunit", format_data_sku, headers)
                            res_sku = conn_sku.getresponse()
                            
                            if res_sku.status == 200 :
                                data_sku = res_sku.read()
                                dict_sku = json.loads(data_sku)
                                record.write({
                                    'response_data_sku':  (json.dumps(dict_sku, indent=4, separators=(". ", " = "))),
                                    'ref_id_vtex_sku': dict_sku['Id'],
                                    'ref_id_vtex': IdRefProduct,
                                    'vtex': True,
                                    'sync_vtex': True,
                                    })
                                sku_p = dict_sku['Id']
                                
                                # ean asociar
                                payload_ean = {}
                                conn_add_ean.request("POST", "/api/catalog/pvt/stockkeepingunit/"+str(sku_p)+"/ean/"+str(search_barcode.barcode), payload_ean, headers)
                                res_sku_ean = conn_add_ean.getresponse()
                                if res_sku_ean.status == 200:
                                        _logger.info('POST 200  Asociar Ean SKU Executado correctamente')
                                        data_sku_ean = res_sku_ean.read()
                                        _logger.info(data_sku_ean)
                                
                                # specificaciones solo color si esta el valor Id crear sin el id y sino actualizar 
                                color_p = record.color_id_mp.name

                                conn_specs.request("GET", "/api/catalog/pvt/stockkeepingunit/"+str(sku_p)+"/specification", payload,headers)
                                res_specs_add_sku = conn_specs.getresponse()

                                # crear specs 
                                if res_specs_add_sku.status == 200:
                                    get_id_color = self.env['vtex.sku.map.specs'].search([
                                                                                                ('Value','=',color_p)
                                                                                                ])
                                    
                                    payload_specs =  {
                                            "FieldId": 18,
                                            "SkuId": sku_p,
                                            "FieldValueId" : get_id_color.FieldValueId,
                                            }
                                
                                    payload_sku_specs_f = json.dumps(payload_specs)
                                    conn_add_specs.request("POST", "/api/catalog/pvt/stockkeepingunit/"+str(sku_p)+"/specification", payload_sku_specs_f, headers)
                                    res_sku_specs = conn_add_specs.getresponse()
                                    if res_sku_specs.status == 200:
                                        _logger.info('POST 200  Crear SKU Productos Executado correctamente')
                                        data_sku_specs = res_sku_specs.read()

                        if res_product.status == 200:
                            # asociar politicas recorrer y crear por id las politicas
                            TradePolicys = record.trade_policies_ids
                            payload_tradep = {}
                            for rec_tp in TradePolicys:
                                IdTradePolicy = rec_tp.id_vtex
                                payload_tradep = {}
                                conn_prd_trade_policy.request("POST", "/api/catalog/pvt/product/"+str(IdRefProduct)+"/salespolicy/"+str(IdTradePolicy), payload_tradep, headers)
                                res_prd_trade_p = conn_prd_trade_policy.getresponse()
                                if res_prd_trade_p.status == 200:
                                    _logger.info('POST 200  asociar politica')
                                    data_trade_p = res_prd_trade_p.read()

                # UPDATE selF
                self.write({'state': 'validate'})


                # SKU
                if self.type_interface == 'sku_product':
                    _logger.info('Incio funcion Crear SKU Productos')
                    IdRefProduct = False
                    search_validator = vtex_validator_products.search([
                                                                        '&',
                                                                        ('type_request','=',mode),
                                                                        ('state','=','validate')
                                                                        ])

                    if search_validator:
                        for rec_freq in search_validator.field_products_ids:
                            req_1 = str(rec_freq.name)
                            sear_req = prod_temp.search_read([
                                                    ('id','=',self.id_ref_model)
                                                    ],[req_1])
                            if sear_req:
                                if sear_req[0][req_1] == False:
                                    raise UserError("Segun la validacion para E-commerce este campo es requerido %s " % rec_freq.name)
                        
                        # Registro Producto 
                        search_p = prod_temp.search([('id','=',self.id_ref_model)])
                        for record in search_p:
                            if not record.ref_id_vtex:
                                raise UserError("No se ha encontrado la ref id para el SKU")
                                
                            IdRefProduct = record.ref_id_vtex
                            search_barcode = prod_prod.search([('default_code','=',record.default_code)],limit=1)
                
                            dict_data_sku = {
                                "Name": str(record.name_web_mp),
                                "ProductId": str(IdRefProduct),
                                "RefId":  str(record.default_code),
                                "IsActive": 'false',
                                "ActivateIfPossible": 'true',
                                "Ean": str(search_barcode.barcode),
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
                                "CommercialConditionId": '1',
                                "MeasurementUnit": "un",
                                "UnitMultiplier": '1.0000',
                            }

                            # formato
                            format_data_sku = json.dumps(dict_data_sku)
                            conn.request("POST", "/api/catalog/pvt/stockkeepingunit", format_data_sku, headers)
                            res_sku = conn.getresponse()
                            if res_sku.status == 200:
                                _logger.info('200  Crear SKU Productos Executado correctamente')
                                response_data_sku = res_sku.read()
                                dict_response_sku = json.loads(response_data_sku)

                                record.write({
                                    'response_data_sku':  (json.dumps(dict_response_sku, indent=4, separators=(". ", " = "))),
                                    'ref_id_vtex_sku': dict_response_sku['Id'],
                                    'vtex': True,
                                    'sync_vtex': True,
                                    })
                                sku_p = dict_response_sku['Id']
                                
                                # ean asociar
                                payload_ean = {}
                                conn_add_ean.request("POST", "/api/catalog/pvt/stockkeepingunit/"+str(sku_p)+"/ean/"+str(search_barcode.barcode), payload_ean, headers)
                                res_sku_ean = conn_add_ean.getresponse()
                                if res_sku_ean.status == 200:
                                        _logger.info('POST 200  Asociar Ean SKU Executado correctamente')
                                        data_sku_ean = res_sku_ean.read()
                                        _logger.info(data_sku_ean)
                                
                                # specificaciones solo color si esta el valor Id crear sin el id y sino actualizar 
                                color_p = record.color_id_mp.name


                                conn_specs.request("GET", "/api/catalog/pvt/stockkeepingunit/"+str(sku_p)+"/specification", payload,headers)
                                res_specs_add_sku = conn_specs.getresponse()

                                # crear specs 
                                if res_specs_add_sku.status == 200:
                                    get_id_color = self.env['vtex.sku.map.specs'].search([
                                                                                                ('Value','=',color_p)
                                                                                                ])
                                    
                                    payload_specs =  {
                                            "FieldId": 18,
                                            "SkuId": sku_p,
                                            "FieldValueId" : get_id_color.FieldValueId,
                                            }
                                
                                    payload_sku_specs_f = json.dumps(payload_specs)
                                    conn_add_specs.request("POST", "/api/catalog/pvt/stockkeepingunit/"+str(sku_p)+"/specification", payload_sku_specs_f, headers)
                                    res_sku_specs = conn_add_specs.getresponse()
                                    if res_sku_specs.status == 200:
                                        _logger.info('POST 200  Crear SKU Productos Executado correctamente')
                                        data_sku_specs = res_sku_specs.read()

                self.write({'state': 'validate'})


class VtexOperationFields(models.Model):
    _name = 'vtex.operation.fields'
    _description = 'Operations Fields Operations'

    name = fields.Char('Name')
    type_request = fields.Selection([
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ], string='Type Request')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Validate'),
        ('error', 'Error'),
        ('cancel', 'Cancel'),
    ], string='State',default='draft')
    
    field_old_id = fields.Char('Field Old Id')
    field_old_name = fields.Char('Field Old Name')
    field_old_tag = fields.Char('Field Old Tag')
    field_old_value = fields.Char('Field Old Value')

    field_new_id = fields.Char('Field New Id')
    field_new_name = fields.Char('Field New Name')
    field_new_tag = fields.Char('Field New Tag')
    field_new_value = fields.Char('Field New Value')

    sync_op_id = fields.Many2one('vtex.sync.operations', string='Sync Op')
