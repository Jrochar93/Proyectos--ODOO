# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied, MissingError,ValidationError
from datetime import datetime
from xml.etree import ElementTree as ET



import xml.etree.ElementTree as ET
import base64

#Lib Config Logger
import logging 
logging.basicConfig(filename="/var/log/odoo/odoo-server.log", 
					format='%(asctime)s %(message)s', 
					filemode='w') 



class BcnGetw1InsertFac(http.Controller):
    logger = logging.getLogger() 

    def _error_response(self, message, status):
            response_xml = f"""<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>
                                <documento_respuesta>
                                    <mensaje>{message}</mensaje>
                                    <estado>{status}</estado>
                                </documento_respuesta>"""
            return http.Response(response_xml, status=400, content_type='application/xml')

    def _success_response(self, message, status):
        response_xml = f"""<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>
                            <documento_respuesta>
                                <mensaje>{message}</mensaje>
                                <estado>{status}</estado>
                            </documento_respuesta>"""
        return http.Response(response_xml, status=200, content_type='application/xml')
 # Main, método valida username/password, Obtiene DB Relacionada por GET y Company_ID desde el auth del usuario
    @http.route('/bcn_getw1/insert_factura_bcn', type='http', auth='none', methods=['POST'], csrf=False)
    def post_insert_factura(self, **kw):
        # Obtener credenciales de HTTP Basic Auth
		#logging.info("Ejemplo Logger")
        company_id_pais = kw.get('company_id')
        
        
        
        auth = request.httprequest.headers.get('Authorization', None)
        if not auth:
            return http.Response('Credenciales no proporcionadas.', status=401)

        try:
            # Decode para obtener Username y Password
            auth = base64.b64decode(auth.split(' ')[1]).decode('utf-8')
            username, password = auth.split(':')
        except (TypeError, ValueError):
            return http.Response('Credenciales no válidas.', status=401)

        # Validar Parametro DB Name
        db_name = kw.get('dbname')
        if not db_name:
            return http.Response('Debe Ingresar el la DB.', status=401)
        else:
            request.session.db = db_name
            env = request.env
            # Autenticación contra Odoo validando accesos
            uid = request.session.authenticate(request.db, username, password)

        if not uid:
            return http.Response('Credenciales inválidas.', status=401)

       

        if not company_id_pais:
            return http.Response('La company_id es requerida.', status=401)
       
        body = request.httprequest.data

        if not body:
            return http.Response('Debe Ingresar el XML en el Body.', status=401)
        else:
            if int(company_id_pais) == 2:
                return self.insert_bcn_col(body,int(company_id_pais))
            elif int(company_id_pais) == 1:
                #return http.Response('En desarrollo aun', status=401)
                return self.insert_bcn_cl(body,int(company_id_pais))
            
            
    def insert_bcn_col(self, body, company_id_pais):
        
        root = ET.fromstring(body)

        doc_subtipoid_element = root.find('.//cabecera/doc_subtipo')
        doc_subtipo = doc_subtipoid_element.text if doc_subtipoid_element is not None else None
        
            
        tipo_doc=''
        
        tipo_documento = request.env['l10n_latam.document.type'].search([
                    ('code', '=', doc_subtipo),
                    ('country_id', '=', 49)
                ], limit=1)
        tipo_doc=tipo_documento.id
            
            
        logging.info(f'doc_subtipo: {doc_subtipo} tipo_doc {tipo_doc}')
        doc_emisor_fiscalid_element = root.find('.//cabecera/doc_emisor_fiscalid')
        doc_emisor_fiscalid = doc_emisor_fiscalid_element.text if doc_emisor_fiscalid_element is not None else None

        doc_emisor_id_element = root.find(".//tercero/id")
        doc_emisor_id = doc_emisor_id_element.text if doc_emisor_id_element is not None else None

        logging.info(f'doc_emisor_id {doc_emisor_id}')
        doc_fecha_emision_element = root.find('.//cabecera/doc_fecha_emision')
        doc_fecha_emision = doc_fecha_emision_element.text if doc_fecha_emision_element is not None else None

        doc_fecha_vencimiento_element = root.find('.//cabecera/doc_fecha_vencimiento')
        doc_fecha_vencimiento = doc_fecha_vencimiento_element.text if doc_fecha_vencimiento_element is not None else None

        doc_folio_element = root.find('.//cabecera/doc_folio')
        doc_folio = doc_folio_element.text if doc_folio_element is not None else None

        doc_monto_neto_element = root.find('.//cabecera/doc_monto_neto')
        doc_monto_neto = doc_monto_neto_element.text if doc_monto_neto_element is not None else None

        doc_monto_iva_element = root.find('.//cabecera/doc_monto_iva')
        doc_monto_iva = doc_monto_iva_element.text if doc_monto_iva_element is not None else None
        doc_monto_neto = float(doc_monto_neto) if doc_monto_neto else 0.0
        doc_monto_iva = float(doc_monto_iva) if doc_monto_iva else 0.0

        doc_formapago_element = root.find('.//cabecera/doc_formapago')
        doc_formapago = doc_formapago_element.text if doc_formapago_element is not None else None
        if doc_fecha_vencimiento is None:
            doc_formapago = '1' 
        logging.info(f'doc_formapago {doc_formapago}')

        diario_contable = request.env['res.company'].search([('id', '=', company_id_pais)], limit=1)
        diario_contable_id=diario_contable.diario_contable_id.id
        if diario_contable_id:
            # Imprimir el diario_contable_id si se encuentra la compañía            
            logging.info(f'Diario contable encontrado: {diario_contable_id}')
        else: 
            # Devolver un mensaje de error si el diario contable no está configurado en la compañía
            return self._error_response('Diario contable no configurado en ODOO', -1)
        
        
    
        if root.find('.//distribucion') is not None and doc_subtipo=='1':
            distribucion_element = root.find('.//distribucion')
            distribucion = []

            for distribucion_linea in distribucion_element.findall('.//linea'):
                CuentaContable_element = distribucion_linea.find('CuentaContable')
                CuentaContable = CuentaContable_element.text if CuentaContable_element is not None else None

                distribucion.append({
                    'CuentaContable': CuentaContable
                })

           

            details_data = []
            invoice_line_data = []

            for detalle in root.findall('.//cac:InvoiceLine', namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'}):
                detalle_dict = {
                    'PriceAmount': detalle.find('.//cbc:PriceAmount', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}).text if detalle.find('.//cbc:LineExtensionAmount', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}) is not None else None,
                    'InvoicedQuantity': detalle.find('.//cbc:InvoicedQuantity', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}).text if detalle.find('.//cbc:InvoicedQuantity', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}) is not None else None,
                    'Note': detalle.find('.//cbc:Note', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}).text if detalle.find('.//cbc:Note', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}) is not None else None,
                }

                details_data.append(detalle_dict)
                
                # Descuento
                allowance_charge = detalle.find('.//cac:AllowanceCharge', namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'})
                if allowance_charge is not None:
                    DiscountReason = allowance_charge.find('.//cbc:AllowanceChargeReason', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}).text
                    Amount = allowance_charge.find('.//cbc:Amount', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}).text
                    
                    # Solo calcular el descuento si hay información de descuento disponible
                    if detalle_dict['PriceAmount'] is not None and float(detalle_dict['PriceAmount']) != 0:
                        descuento = float(Amount) / float(detalle_dict['PriceAmount']) * 100
                        logging.info(f"Amount desc--->{Amount} descuento {descuento}")
                    else:
                        logging.info("No se puede calcular el descuento porque el precio de la línea es cero o no está disponible")
                else:
                    logging.info("No se encontró información de descuento para esta línea")
                    descuento=0

                
                # Obtener información de impuestos solo para las líneas que tienen
                tax_ids_for_line = []
                tax_scheme_list = detalle.findall('.//cac:TaxCategory/cac:TaxScheme', namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2', 'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})

                for tax_scheme in tax_scheme_list:
                    tax_id_element = tax_scheme.find('.//cbc:ID', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})

                    if tax_id_element is not None:
                        tax_id = tax_id_element.text
                        tax = request.env['account.tax'].sudo().search([
                            ('imp_codigo', '=', tax_id),
                            ('type_tax_use', '=', 'purchase'),
                            ('real_amount', '=', 19),
                            ('active', '=', True),
                            ('company_id', '=', company_id_pais)
                        ], limit=1)

                        if tax:
                            tax_ids_for_line.append(tax.id)
                            logging.info(f'tax {tax_ids_for_line}')
                        else:
                            logging.warning(f'Tax with ID {tax_id} not found.')
                
                # Accede a la información de detalle_dict usando las claves adecuadas
                account_id = request.env['account.account'].search([
                    ('id', '=', distribucion[0]['CuentaContable']),
                    ('company_id', '=', company_id_pais)
                ], limit=1)

                if not account_id:
                    return self._error_response('Cuenta contable no existe en ODOO', -1)
                logging.info(f'account_id {account_id.id}')
                logging.info(f'CuentaContable: {distribucion[0]["CuentaContable"]}')
                logging.info(f'doc_subtipo: {doc_subtipo}')
                namespace = {'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
                    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}

                party_tax_scheme = root.find('.//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme', namespace)

                if party_tax_scheme is not None:
                    tax_scheme_list = party_tax_scheme.findall('.//cac:TaxScheme', namespace)
                    tax_ids = []

                    for tax_scheme in tax_scheme_list:
                        tax_id_element = tax_scheme.find('.//cbc:ID', namespace)

                        if tax_id_element is not None:
                            tax_id = tax_id_element.text
                            tax_ids.append(tax_id)
                            logging.info(f'tax_arriba {tax_ids}')

                invoice_line_data.append({
                    'account_id': account_id.id,
                    'quantity': float(detalle_dict['InvoicedQuantity']),
                    'price_unit': float(detalle_dict['PriceAmount']),
                    'name': detalle_dict['Note'],
                    'tax_ids': [(6, 0, tax_ids_for_line)] if tax_ids_for_line else False,
                    'display_type': 'product',  # Esto puede variar según tu modelo
                    'date_maturity': doc_fecha_vencimiento,
                    'discount':descuento,
                })

        elif doc_subtipo == '3':
            if root.find('.//distribucion') is not None:
                distribucion_element = root.find('.//distribucion')
                distribucion = []

                for distribucion_linea in distribucion_element.findall('.//linea'):
                    CuentaContable_element = distribucion_linea.find('CuentaContable')
                    CuentaContable = CuentaContable_element.text if CuentaContable_element is not None else None

                    distribucion.append({
                        'CuentaContable': CuentaContable
                    })
            else:
                return self._error_response('Documento Sin Cuenta Contable', -1) 
                
            
            #invoice_reference = False  # Cambiado a False porque solo se crea una referencia por factura
            discrepancy_response = root.find('.//cac:DiscrepancyResponse', namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2', 'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})

            if discrepancy_response is not None:
                # Obtener los valores de los elementos dentro de 'DiscrepancyResponse'
                reference_id_element = discrepancy_response.find('.//cbc:ReferenceID', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
                response_code_element = discrepancy_response.find('.//cbc:ResponseCode', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
                description_element = discrepancy_response.find('.//cbc:Description', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})
                
                # Verificar si los elementos existen y no son nulos antes de acceder a sus propiedades 'text'
                if reference_id_element is not None and reference_id_element:
                    reference_id = reference_id_element.text
                else:
                    reference_id = "No se encontró ReferenceID"

                if response_code_element is not None:
                    response_code = response_code_element.text
                else:
                    response_code = "No se encontró ResponseCode"

                if description_element is not None:
                    description = description_element.text
                else:
                    description = "No se encontró Description"
                
                # Imprimir los valores obtenidos
                logging.info(f"Reference ID:", {reference_id})
                logging.info(f"Response Code:", {response_code})
                logging.info(f"Description:", {description})
            else:
                logging.info(f"No se encontró DiscrepancyResponse en el XML.")

            details_data = []
            invoice_line_data = []

            for detalle in root.findall('.//cac:CreditNoteLine', namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'}):
                detalle_dict = {
                    'PriceAmount': detalle.find('.//cbc:PriceAmount', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}).text if detalle.find('.//cbc:PriceAmount', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}) is not None else None,
                    'BaseQuantity': detalle.find('.//cbc:BaseQuantity', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}).text if detalle.find('.//cbc:BaseQuantity', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}) is not None else None,
                    'Note': detalle.find('.//cbc:Note', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}).text if detalle.find('.//cbc:Note', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}) is not None else None,
                }

                details_data.append(detalle_dict)
                
                # Descuento
                allowance_charge = detalle.find('.//cac:AllowanceCharge', namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'})
                if allowance_charge is not None:
                    DiscountReason = allowance_charge.find('.//cbc:AllowanceChargeReason', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}).text
                    Amount = allowance_charge.find('.//cbc:Amount', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}).text
                    
                    # Solo calcular el descuento si hay información de descuento disponible
                    if detalle_dict['PriceAmount'] is not None and float(detalle_dict['PriceAmount']) != 0:
                        descuento = float(Amount) / float(detalle_dict['PriceAmount']) * 100
                        logging.info(f"Amount desc--->{Amount} descuento {descuento}")
                    else:
                        logging.info("No se puede calcular el descuento porque el precio de la línea es cero o no está disponible")
                else:
                    logging.info("No se encontró información de descuento para esta línea")
                    descuento=0

                tax_ids_for_line = []
                tax_scheme_list = detalle.findall('.//cac:TaxCategory/cac:TaxScheme', namespaces={'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2', 'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})

                for tax_scheme in tax_scheme_list:
                    tax_id_element = tax_scheme.find('.//cbc:ID', namespaces={'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'})

                    if tax_id_element is not None:
                        tax_id = tax_id_element.text
                        tax = request.env['account.tax'].sudo().search([
                            ('imp_codigo', '=', tax_id),
                            ('type_tax_use', '=', 'purchase'),
                            ('real_amount', '=', 19),
                            ('active', '=', True),
                            ('company_id', '=', company_id_pais)
                        ], limit=1)

                        if tax:
                            tax_ids_for_line.append(tax.id)
                            logging.info(f'tax {tax_ids_for_line}')
                        else:
                            logging.warning(f'Tax with ID {tax_id} not found.')

                invoice_line_data.append({
                    'quantity': float(detalle_dict['BaseQuantity']),
                    'price_unit': float(detalle_dict['PriceAmount']),
                    'name': detalle_dict['Note'],
                    'tax_ids': [(6, 0, tax_ids_for_line)] if tax_ids_for_line else False,
                    'display_type': 'product',  # Esto puede variar según tu modelo
                    'date_maturity': doc_fecha_vencimiento,
                    'discount':descuento,
                })

        if not doc_fecha_emision:
            return self._error_response('Las fecha de emisión es es obligatorias.', -1)

        # Verificar si la factura ya existe en Odoo
        existing_invoice = request.env['account.move'].search([('ref', '=', doc_folio),
                                                            ('partner_id.id', '=', doc_emisor_id),
                                                            ('company_id', '=', company_id_pais)], limit=1)

        if existing_invoice:
            # Factura ya existe, devolver respuesta de error
            return self._error_response('La factura ya existe en Odoo.', -1)
        else:
            # Factura no existe, continuar con la creación
            journal_id = request.env['account.journal'].search([('id', '=', diario_contable_id),                                                                
                                                                ('company_id', '=', company_id_pais)], limit=1)
            if not journal_id:
                return self._error_response('Diario Facturas de proveedores_bcn no existe creelo en ODOO', -1)
            logging.info(f'journal_id {journal_id.id}')
            partner = request.env['res.partner'].search([('id', '=', doc_emisor_id),
                                                        ('company_id', '=', company_id_pais)], limit=1)
            logging.info(f'partner {partner.id}')
            if not partner:
                return self._error_response('El Partner no existe en BD ODOO. Regístrelo', -1)

            if journal_id:
                # Crear la factura en Odoo
                logging.info(f'doc_monto_iva {doc_monto_iva} tipo_doc {tipo_doc}')
                
                logging.info(f' tipo_doc ok {tipo_doc}')
                move_type=''
                if doc_subtipo=='1':
                    move_type='in_invoice'
                elif doc_subtipo=='3':
                    move_type='in_refund'
                invoice_data = {
                    'partner_id': partner.id,
                    'l10n_latam_document_type_id': tipo_doc,
                    'journal_id': journal_id.id,
                    'move_type': move_type,
                    'invoice_date': doc_fecha_emision,
                    'invoice_date_due': doc_fecha_vencimiento,
                    'amount_total': doc_monto_neto + doc_monto_iva,
                    'l10n_latam_document_number': doc_folio,                    
                    'invoice_line_ids': [(0, 0, line) for line in invoice_line_data],                    
                    'ref': doc_folio,                    
                    'pago_metodo': doc_formapago,
                    # Añade otros campos según tu modelo
                }

                try:
                    # Crear la factura en Odoo
                    invoice = request.env['account.move'].sudo().create(invoice_data)
                    logging.info(f'invoice created: {invoice} {invoice_data}')

                    # Inicializar invoice_reference como False fuera del bloque try
                    invoice_reference = False

                    # Añadir la referencia de la factura si existe y el tipo de documento es '3'
                    if doc_subtipo == '3' and discrepancy_response is not None:
                        invoice_reference = {
                            'origin_doc_number': reference_id,
                            'bcn_reference_doc_type_id': 1,
                            'date': doc_fecha_emision,
                            
                            # Aquí puedes añadir más campos si es necesario
                        }

                        logging.info(f'invoice_reference {invoice_reference}')

                    # Añadir la referencia de la factura si existe y el tipo de documento es '3'
                    if invoice_reference:
                        invoice_reference['move_id'] = invoice.id
                        request.env['bcn.account.invoice.reference'].sudo().create(invoice_reference)

                    # Devolver respuesta exitosa
                    return self._success_response('Inserción exitosa', 0)

                except Exception as e:
                    # Si ocurre algún error al crear la factura, devolver respuesta de error
                    return self._error_response(f'Error al crear la factura en Odoo. {e}', -1)




                    

    def insert_bcn_cl(self, body, company_id_pais):
        root = ET.fromstring(body)
        
        doc_subtipoid_element = root.find('.//cabecera/doc_subtipo')
        doc_subtipo = doc_subtipoid_element.text if doc_subtipoid_element is not None else None
        tipo_doc=''
        
        tipo_documento = request.env['l10n_latam.document.type'].search([
                    ('code', '=', doc_subtipo),
                    ('country_id', '=', 46)
                ], limit=1)
        tipo_doc=tipo_documento.id
       
            
        logging.info(f'doc_subtipo: {doc_subtipo} tipo_doc {tipo_doc}')
        
        # Buscar el valor del elemento 'doc_emisor_fiscalid'
        doc_emisor_fiscalid_element = root.find('.//cabecera/doc_emisor_fiscalid')
        doc_emisor_fiscalid = doc_emisor_fiscalid_element.text if doc_emisor_fiscalid_element is not None else None
        
        doc_emisor_id_element = root.find(".//tercero/id")
        doc_emisor_id = doc_emisor_id_element.text if doc_emisor_id_element is not None else None    
        
        doc_tasa_iva_element = root.find(".//Encabezado/Totales/TasaIVA")
        doc_tasa_iva = doc_tasa_iva_element.text if doc_tasa_iva_element is not None else None

        # Si doc_tasa_iva no está presente, asigna el valor 19
        doc_tasa_iva = float(doc_tasa_iva) if doc_tasa_iva is not None else 19.0

        doc_fecha_emision_element = root.find('.//cabecera/doc_fecha_emision')
        doc_fecha_emision = doc_fecha_emision_element.text if doc_fecha_emision_element is not None else None
        
        
        doc_folio_element = root.find('.//cabecera/doc_folio')
        doc_folio = doc_folio_element.text if doc_folio_element is not None else None
        
        doc_monto_neto_element = root.find('.//cabecera/doc_monto_neto')
        doc_monto_neto = doc_monto_neto_element.text if doc_monto_neto_element is not None else None
        
        doc_monto_iva_element = root.find('.//cabecera/doc_monto_iva')
        doc_monto_iva = doc_monto_iva_element.text if doc_monto_iva_element is not None else None
        doc_monto_neto = float(doc_monto_neto) if doc_monto_neto else 0.0
        doc_monto_iva = float(doc_monto_iva) if doc_monto_iva else 0.0
        doc_fecha_vencimiento_element = root.find('.//cabecera/doc_fecha_vencimiento')
        doc_fecha_vencimiento = doc_fecha_vencimiento_element.text if doc_fecha_vencimiento_element is not None else None
        doc_formapago_element = root.find('.//cabecera/doc_formapago')
        doc_formapago = doc_formapago_element.text if doc_formapago_element is not None and doc_formapago_element.text != '0' else None

        if doc_fecha_vencimiento is None:
            doc_formapago = '1' 
        
        diario_contable = request.env['res.company'].search([('id', '=', company_id_pais)], limit=1)
        diario_contable_id=diario_contable.diario_contable_id.id
        if diario_contable_id:
            # Imprimir el diario_contable_id si se encuentra la compañía            
            logging.info(f'Diario contable encontrado: {diario_contable_id}')
        else: 
            # Devolver un mensaje de error si el diario contable no está configurado en la compañía
            return self._error_response('Diario contable no configurado en ODOO', -1)
        
        
        
        logging.info(f'Data:{doc_subtipo}- {doc_emisor_fiscalid} -{doc_emisor_id} - {doc_fecha_emision} - {doc_fecha_vencimiento} - {doc_folio} - {doc_monto_neto} - {doc_monto_iva} - {doc_formapago}')    
        
        
        distribucion = []

        # ...

        if root.find('.//distribucion') is not None:
            distribucion_element = root.find('.//distribucion')
            distribucion = []

            for distribucion_linea in distribucion_element.findall('.//linea'):
                CuentaContable_element = distribucion_linea.find('CuentaContable')
                CuentaContable = CuentaContable_element.text if CuentaContable_element is not None else None

                distribucion.append({
                    'CuentaContable': CuentaContable                    
                })
        else:
            
            return self._error_response('Documento Sin Cuenta Contable', -1)       

        if not doc_fecha_emision:
            return self._error_response('La fecha de emisión  es obligatorias.', -1)
       

        # Verificar si la factura ya existe en Odoo
        existing_invoice = request.env['account.move'].search(
            [('ref', '=', doc_folio), ('partner_id.id', '=', doc_emisor_id), ('company_id', '=', company_id_pais)], limit=1)

        # Resto del código...

        if existing_invoice:
            # Factura ya existe, devolver respuesta de error
            return self._error_response('La factura ya existe en Odoo.', -1)
        else:
            # Factura no existe, continuar con la creación
            journal_id = request.env['account.journal'].search([('id', '=', diario_contable_id),                                                                
                                                                ('company_id', '=', company_id_pais)], limit=1)
            if journal_id is False:
                return self._error_response('Diario Facturas de proveedores_bcn no existe creelo en ODOO', -1)
            logging.info(f'journal_id {journal_id.id}')
            partner = request.env['res.partner'].search(
                [('id', '=', doc_emisor_id), ('company_id', '=', company_id_pais)], limit=1)
            logging.info(f'partner {partner.id}')

            if journal_id:
                # Crear la factura en Odoo
                logging.info(f'doc_monto_iva {doc_monto_iva}')
                
                account_id = request.env['account.account'].search([
                    ('id', '=', distribucion[0]['CuentaContable']),
                    ('company_id', '=', company_id_pais)
                ], limit=1)

                if not account_id:
                    return self._error_response('Cuenta contable no existe en ODOO', -1)

                invoice_line_data = []  # Mantén esta línea para inicializar la lista
                if int(doc_subtipo)==34:
                    namespace_sii = {'sii': 'http://www.sii.cl/SiiDte'}

                    # Resto del código...

                    # Dentro de la sección de detalles
                    details_data = []
                    for detalle in root.findall('.//sii:Detalle', namespace_sii):
                        detalle_dict = {
                            'NroLinDet': detalle.find('sii:NroLinDet', namespace_sii).text if detalle.find('sii:NroLinDet', namespace_sii) is not None else None,
                            'NmbItem': detalle.find('sii:NmbItem', namespace_sii).text if detalle.find('sii:NmbItem', namespace_sii) is not None else None,
                            'DscItem': detalle.find('sii:DscItem', namespace_sii).text if detalle.find('sii:DscItem', namespace_sii) is not None else None,
                            'QtyItem': detalle.find('sii:QtyItem', namespace_sii).text if detalle.find('sii:QtyItem', namespace_sii) is not None else None,
                            'PrcItem': detalle.find('sii:PrcItem', namespace_sii).text if detalle.find('sii:PrcItem', namespace_sii) is not None else None,
                            'MontoItem': detalle.find('sii:MontoItem', namespace_sii).text if detalle.find('sii:MontoItem', namespace_sii) is not None else None,
                            
                        }

            # Asegúrate de ajustar las claves y rutas según la estructura real de tu XML


                        details_data.append(detalle_dict)
                        logging.warning(f'Tax with ID {detalle_dict} not found.')
                        IndExe = detalle_dict.get('IndExe', '')  # Convertir a cadena el valor de IndExe del diccionario
                        logging.info(f'IndExe {IndExe}.')
                        
                        if doc_subtipo == '34':  # Comparar con '1' como cadena
                            tax_ids_for_line = [(5, 0, 0)]  # Lista de impuestos con el impuesto correspondiente
                            logging.info(f'Impuesto aplicado para esta línea: {tax_ids_for_line}')
                       
                        
                        monto_item_value = detalle_dict.get('MontoItem', '')
                        item = (detalle_dict.get('NmbItem', '') or '') + (detalle_dict.get('DscItem', '') or '')
 
                        invoice_line_data.append({
                            'account_id': account_id.id,
                            'quantity': float(detalle_dict.get('QtyItem', '1') or 1),
                            'price_unit': detalle_dict.get('PrcItem', '') or monto_item_value,
                            'name': item,
                            'tax_ids': tax_ids_for_line,  # Aplicar impuesto solo si doc_tasa no es cero
                            'display_type': 'product',
                            'date_maturity': doc_fecha_vencimiento,
                        })

                else:
                    details_data = []
                    document_element = root.find('.//Documento')  # Elimina el prefijo del espacio de nombres

                    if document_element:
                        for i, detalle in enumerate(document_element.findall('.//Detalle')):
                            detalle_dict = {
                                'NroLinDet': detalle.find('NroLinDet').text if detalle.find('NroLinDet') is not None else None,
                                'NmbItem': detalle.find('NmbItem').text if detalle.find('NmbItem') is not None else None,
                                'DscItem': detalle.find('DscItem').text if detalle.find('DscItem') is not None else None,
                                'QtyItem': detalle.find('QtyItem').text if detalle.find('QtyItem') is not None else None,
                                'PrcItem': detalle.find('PrcItem').text if detalle.find('PrcItem') is not None else None,
                                'MontoItem': detalle.find('MontoItem').text if detalle.find('MontoItem') is not None else None,
                                'IndExe': detalle.find('IndExe').text if detalle.find('IndExe') is not None else None,
                            }
                    
                            details_data.append(detalle_dict)
                            logging.info(f'Tax details_data ID {i + 1}: {detalle_dict} ')
                            
                            IndExe = detalle_dict.get('IndExe', '')  # Convertir a cadena el valor de IndExe del diccionario
                            logging.info(f'IndExe {IndExe}.')
                            
                            if IndExe == '1':  # Comparar con '1' como cadena
                                tax_ids_for_line = [(5, 0, 0)]  # Lista de impuestos con el impuesto correspondiente
                                logging.info(f'Impuesto aplicado para esta línea: {tax_ids_for_line}')
                            else:
                                tax_ids_for_line = [(6, 0, [2])]  # Lista vacía de impuestos
                                logging.info(f'No se aplicará impuesto para esta línea {tax_ids_for_line}')
                                
                                
                            monto_item_value = detalle_dict.get('MontoItem', '')
                            item = detalle_dict.get('DscItem', '') or detalle_dict.get('NmbItem', '')  # Utiliza NmbItem si está presente, de lo contrario, usa DscItem

                            invoice_line_data.append({
                                'account_id': account_id.id,
                                'quantity': float(detalle_dict.get('QtyItem', '1') or 1),
                                'price_unit': detalle_dict.get('PrcItem', '') or monto_item_value,
                                'name': item,
                                'tax_ids': tax_ids_for_line,  # Aplicar impuesto solo si doc_tasa no es cero
                                'display_type': 'product',
                                'date_maturity': doc_fecha_vencimiento,
                            })

                    else:
                        namespace_sii = {'sii': 'http://www.sii.cl/SiiDte'}

                        # Resto del código...

                        # Dentro de la sección de detalles
                        details_data = []
                        for detalle in root.findall('.//sii:Detalle', namespace_sii):
                            detalle_dict = {
                                'NroLinDet': detalle.find('sii:NroLinDet', namespace_sii).text if detalle.find('sii:NroLinDet', namespace_sii) is not None else None,
                                'NmbItem': detalle.find('sii:NmbItem', namespace_sii).text if detalle.find('sii:NmbItem', namespace_sii) is not None else None,
                                'DscItem': detalle.find('sii:DscItem', namespace_sii).text if detalle.find('sii:DscItem', namespace_sii) is not None else None,
                                'QtyItem': detalle.find('sii:QtyItem', namespace_sii).text if detalle.find('sii:QtyItem', namespace_sii) is not None else None,
                                'PrcItem': detalle.find('sii:PrcItem', namespace_sii).text if detalle.find('sii:PrcItem', namespace_sii) is not None else None,
                                'MontoItem': detalle.find('sii:MontoItem', namespace_sii).text if detalle.find('sii:MontoItem', namespace_sii) is not None else None,
                                
                            }

                # Asegúrate de ajustar las claves y rutas según la estructura real de tu XML


                            details_data.append(detalle_dict)
                            
                            tasa_iva_total = root.find('.//sii:Totales/sii:TasaIVA', namespace_sii)
                            # Buscar el elemento ValorDR dentro de DscRcgGlobal en la sección DTE
                            descuento_total = root.find('.//sii:DscRcgGlobal/sii:ValorDR', namespace_sii)
                            logging.warning(f'Tax with ID {detalle_dict} not found.')
                            logging.info(f'Descuento{descuento_total} iva {tasa_iva_total}  ')
                            if tasa_iva_total is not None:
                                logging.info(f'IVA encontrado: {tasa_iva_total.text}')
                            
                            if tasa_iva_total.text =='19':  # Comparar con '1' como cadena
                                tax_ids_for_line = [(6, 0, [2])] # Lista de impuestos con el impuesto correspondiente
                                logging.info(f'Impuesto aplicado para esta línea: {tax_ids_for_line}')
                            else:                              
                                tax_ids_for_line = [(5, 0, 0)] # Lista de impuestos con el impuesto correspondiente
                                logging.info(f'Impuesto no aplicado para esta línea: {tax_ids_for_line}')
                        
                            
                            monto_item_value = detalle_dict.get('MontoItem', '') 
                            item = (detalle_dict.get('NmbItem', '') or '') + (detalle_dict.get('DscItem', '') or '')
                            if descuento_total is not None:
                                descuento_total_value = descuento_total.text  # No necesitas convertirlo a cadena
                                if descuento_total_value and float(descuento_total_value) > 0:
                                    descuento= float(descuento_total_value) / float(detalle_dict['PrcItem'])*100  
                            else:
                                # Manejar el caso en que descuento_total sea None
                                # Por ejemplo, lanzar una advertencia o establecer descuento_total_value en cero
                                descuento_total_value = 0
                                logging.warning('No se encontró el elemento ValorDR dentro de DscRcgGlobal en la sección DTE.')

                            invoice_line_data.append({
                                'account_id': account_id.id,
                                'quantity': float(detalle_dict.get('QtyItem', '1') or 1),
                                'price_unit': detalle_dict.get('PrcItem', '') or monto_item_value,
                                'name': item,
                                'tax_ids': tax_ids_for_line,  # Aplicar impuesto solo si doc_tasa no es cero
                                'display_type': 'product',
                                'date_maturity': doc_fecha_vencimiento,
                                'discount':descuento, 
                            })
                                                
                        
                        #logging.info('Sin detalles')
                        #return self._error_response('Lineas de detalles no encontrados en el XML.', -1)

                                    
                if partner:
                    logging.info(f'invoice_line_data: {invoice_line_data}')
                    lines = [(0, 0, line) for line in invoice_line_data]
                    
                    move_type=''
                    if doc_subtipo=='33' or doc_subtipo=='34':
                        move_type='in_invoice'
                    elif doc_subtipo=='61':
                        move_type='in_refund'
                    invoice_data = {
                        'partner_id': partner.id,
                        'l10n_latam_document_type_id': tipo_doc,
                        'journal_id': journal_id.id,
                        'move_type': move_type,
                        'invoice_date': doc_fecha_emision,
                        'invoice_date_due': doc_fecha_vencimiento or doc_fecha_emision,
                        'amount_total': doc_monto_neto + doc_monto_iva,
                        'invoice_line_ids': lines,
                        'l10n_latam_document_number': doc_folio,
                        'ref': doc_folio,
                        'forma_pago': doc_formapago,
                        # Añade otros campos según tu modelo
                    }

                    try:
                        # Crear la factura en Odoo
                        invoice = request.env['account.move'].sudo().create(invoice_data)
                        logging.info(f'invoice created: {invoice} {invoice_data}')

                        invoice_reference_list = []  # Lista para almacenar múltiples referencias si es necesario

                        # Verificar si el tipo de documento es '61' y agregar referencias si es así
                        if doc_subtipo == '61':
                            for referencia in root.iter('Referencia'):
                                nro_lin_ref = referencia.find('NroLinRef').text
                                tpo_doc_ref = referencia.find('TpoDocRef').text
                                folio_ref = referencia.find('FolioRef').text
                                fch_ref = referencia.find('FchRef').text
                                cod_ref = referencia.find('CodRef').text
                                razon_ref = referencia.find('RazonRef').text
                                
                                tipo_documento = request.env['l10n_latam.document.type'].search([
                                            ('code', '=', tpo_doc_ref),
                                            ('country_id', '=', 46)
                                        ], limit=1)
                                tipo_doc=tipo_documento.id
                                
                                reference_data = {
                                    'origin_doc_number': folio_ref,
                                    'bcn_reference_doc_type_id_cl': tipo_doc,
                                    'date': fch_ref,
                                    'reference_doc_code': cod_ref,                                    
                                    'reason': razon_ref,  
                                                                           
                                }
                                invoice_reference_list.append(reference_data)

                        # Verificar si se encontraron referencias y agregarlas a la factura
                        if invoice_reference_list:
                            for reference_data in invoice_reference_list:
                                reference_data['move_id'] = invoice.id
                                request.env['bcn.account.invoice.reference'].sudo().create(reference_data)

                        # Devolver respuesta exitosa
                        return self._success_response('Inserción exitosa', 0)

                    except Exception as e:
                        # Si ocurre algún error al crear la factura, devolver respuesta de error
                        return self._error_response(f'Error al crear la factura en Odoo. {e}', -1)

                else:
                    return self._error_response('El Partner no existe en BD ODOO. Regístrelo', -1)