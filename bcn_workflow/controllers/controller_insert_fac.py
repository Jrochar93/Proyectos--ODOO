# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied, MissingError

import xml.etree.ElementTree as ET
import base64

#Lib Config Logger
import logging 
logging.basicConfig(filename="/var/log/odoo/odoo-server.log", 
					format='%(asctime)s %(message)s', 
					filemode='w') 

#db = 'bcn-piloto'
#username = 'jzamudio@bcncons.com'
#PROD 
#password = 'B+y0kdg='
#PILOTO
#password = 'Gu0mrsE='


class BcnGetw1InsertFac(http.Controller):
    logger = logging.getLogger() 

   
 # Main, método valida username/password, Obtiene DB Relacionada por GET y Company_ID desde el auth del usuario
    @http.route('/bcn_getw1/insert_factura', type='http', auth='none', methods=['POST'], csrf=False)
    def post_insert_factura(self, **kw):
        # Obtener credenciales de HTTP Basic Auth
		#logging.info("Ejemplo Logger")
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

        #Todo Revisar Multi Empresas.
        company_id = request.env.user.company_id.id

        if not company_id:
            return http.Response('No es posible obtener la empresa del usuario.', status=401)

        body = request.httprequest.data

        if not body:
            return http.Response('Debe Ingresar el XML en el Body.', status=401)
        else:

            root = ET.fromstring(body)
            # Busca el elemento "respuesta" utilizando una expresión XPath
            respuesta_element = root.find('.//respuesta')
            respuesta = respuesta_element.text if respuesta_element is not None else None
            
            # Extrae el XML contenido dentro del elemento CDATA
            if respuesta:
                sub_root = ET.fromstring(respuesta)
                dte_emisor_element = sub_root.find('.//cabecera/doc_dte_emisor')

                dte_emisor = dte_emisor_element.text if dte_emisor_element is not None else None
                if not dte_emisor:
                    return http.Response('No se encontro el dte_emisor en el XML.', status=401)

                if sub_root.find('.//distribucion'):
                    # Caso 1 distribucion contable
                    distribucion_element = sub_root.find('.//distribucion')
                    distribucion = []
                    if distribucion_element:
                        
                        distribucion_factura = {
                            'folio': distribucion_element.find('folio_det').text if distribucion_element.find('folio_det') is not None else None,
                            'codigo': distribucion_element.find('codigo').text if distribucion_element.find('codigo') is not None else None,
                            'tipo': distribucion_element.find('tipo').text if distribucion_element.find('tipo') is not None else None,
                            'regla_codigo': distribucion_element.find('regla_codigo').text if distribucion_element.find('regla_codigo') is not None else None,
                            'regla_fecha': distribucion_element.find('regla_fecha').text if distribucion_element.find('regla_fecha') is not None else None,
                            'lineas': []
                        }

                        if distribucion_element.findall('linea'):
                            for distribucion_linea in distribucion_element.findall('linea'):
                                # Estos campos dependen de la definición del Cliente, por lo que pueden cambiar.
                                detalle_linea_distribucion = {
                                    'cuentaContable': distribucion_linea.find('CUENTACONTABLE').text if distribucion_linea.find('CUENTACONTABLE') is not None else None,
                                    'centroCosto': distribucion_linea.find('CENTRODECOSTO').text if distribucion_linea.find('CENTRODECOSTO') is not None else None,
                                    'factorLinea': distribucion_linea.find('factor').text if distribucion_linea.find('factor') is not None else None
                                }

                                # Agregar el listado de Lineas al array de Distribucion
                                distribucion_factura['lineas'].append(detalle_linea_distribucion)
                            distribucion.append(distribucion_factura) 
                        
                    logging.info("Distribucion es: {}".format(' '.join(map(str, distribucion))))

                    
                if sub_root.find('.//ordencompra'):
                    # Caso 2 Orden de Compra
                    ordenCompra_element = sub_root.find('.//ordencompra')
                    ordenCompra = []
                    if ordenCompra_element:
                        ordenCompra_factura = {
                            'ID': ordenCompra_element.find('ID').text if ordenCompra_element.find('ID') is not None else None,
                            'oc': ordenCompra_element.find('oc').text if ordenCompra_element.find('oc') is not None else None,
                            'idtributario_proveedor': ordenCompra_element.find('idtributario_proveedor').text if ordenCompra_element.find('idtributario_proveedor') is not None else None,
                            'nombrecli': ordenCompra_element.find('nombrecli').text if ordenCompra_element.find('nombrecli') is not None else None,
                            'fecha_oc': ordenCompra_element.find('fecha_oc').text if ordenCompra_element.find('fecha_oc') is not None else None,
                            'fecha_venc': ordenCompra_element.find('fecha_venc').text if ordenCompra_element.find('fecha_venc') is not None else None,
                            'monto': ordenCompra_element.find('monto').text if ordenCompra_element.find('monto') is not None else None,
                            'moneda': ordenCompra_element.find('moneda').text if ordenCompra_element.find('moneda') is not None else None,
                            'Dominio': ordenCompra_element.find('Dominio').text if ordenCompra_element.find('Dominio') is not None else None,
                            'Solicitante_id': ordenCompra_element.find('Solicitante_id').text if ordenCompra_element.find('Solicitante_id') is not None else None,
                            'Solicitante_desc': ordenCompra_element.find('Solicitante_desc').text if ordenCompra_element.find('Solicitante_desc') is not None else None,
                            'items': []
                        }

                        if ordenCompra_element.findall('items'):
                            for items_ordencompra in ordenCompra_element.findall('items'):
                                detalle_items_ordencompra = {
                                    'd_codigo': items_ordencompra.find('d_codigo').text if items_ordencompra.find('d_codigo') is not None else None,
                                    'item_linea': items_ordencompra.find('item_linea').text if items_ordencompra.find('item_linea') is not None else None,
                                    'item_codigo': items_ordencompra.find('item_codigo').text if items_ordencompra.find('item_codigo') is not None else None,
                                    'item_codigo_proveedor': items_ordencompra.find('item_codigo_proveedor').text if items_ordencompra.find('item_codigo_proveedor') is not None else None,
                                    'item_nombre': items_ordencompra.find('item_nombre').text if items_ordencompra.find('item_nombre') is not None else None,
                                    'item_descripcion': items_ordencompra.find('item_descripcion').text if items_ordencompra.find('item_descripcion') is not None else None,
                                    'cantidad': items_ordencompra.find('cantidad').text if items_ordencompra.find('cantidad') is not None else None,
                                    'unitario': items_ordencompra.find('unitario').text if items_ordencompra.find('unitario') is not None else None,
                                    'factor_conversion': items_ordencompra.find('factor_conversion').text if items_ordencompra.find('factor_conversion') is not None else None,
                                    'monto_linea': items_ordencompra.find('monto_linea').text if items_ordencompra.find('monto_linea') is not None else None,
                                }
                                # Agregar el listado de Items al array de OrdenCompra
                                ordenCompra_factura['items'].append(detalle_items_ordencompra)
                            ordenCompra.append(ordenCompra_factura)

                if sub_root.find('.//recepcion'):
                    # Caso 3 Recepcion
                    recepcion_element = sub_root.find('.//recepcion')
                    recepcion = []
                    if recepcion_element:
                        recepcion_factura = {
                            'id': recepcion_element.find('id').text if recepcion_element.find('id') is not None else None,
                            'codigo': recepcion_element.find('codigo').text if recepcion_element.find('codigo') is not None else None,
                            'proveedor_rut': recepcion_element.find('proveedor_rut').text if recepcion_element.find('proveedor_rut') is not None else None,
                            'proveedor_nombre': recepcion_element.find('proveedor_nombre').text if recepcion_element.find('proveedor_nombre') is not None else None,
                            'fecha_recepcion': recepcion_element.find('fecha_recepcion').text if recepcion_element.find('fecha_recepcion') is not None else None,
                            'orden_compra_codigo': recepcion_element.find('orden_compra_codigo').text if recepcion_element.find('orden_compra_codigo') is not None else None,
                        }

                        if recepcion_element.findall('items_recepcion'):
                            for items_recepcion in recepcion_element.findall('items_recepcion'):
                                detalle_items_recepcion = {
                                    'd_codigo': items_recepcion.find('d_codigo').text if items_recepcion.find('d_codigo') is not None else None,
                                    'item_linea': items_recepcion.find('item_linea').text if items_recepcion.find('item_linea') is not None else None,
                                    'item_codigo': items_recepcion.find('item_codigo').text if items_recepcion.find('item_codigo') is not None else None,
                                    'item_codigo_proveedor': items_recepcion.find('item_codigo_proveedor').text if items_recepcion.find('item_codigo_proveedor') is not None else None,
                                    'item_nombre': items_recepcion.find('item_nombre').text if items_recepcion.find('item_nombre') is not None else None,
                                    'item_descripcion': items_recepcion.find('item_descripcion').text if items_recepcion.find('item_descripcion') is not None else None,
                                    'cantidad': items_recepcion.find('cantidad').text if items_recepcion.find('cantidad') is not None else None,
                                    'unitario': items_recepcion.find('unitario').text if items_recepcion.find('unitario') is not None else None,
                                    'factor_conversion': items_recepcion.find('factor_conversion').text if items_recepcion.find('factor_conversion') is not None else None,
                                    'monto_linea': items_recepcion.find('monto_linea').text if items_recepcion.find('monto_linea') is not None else None,
                                }
                                # Agregar el listado de Items al array de recepcion
                                recepcion_factura['items_recepcion'].append(detalle_items_recepcion)
                            recepcion.append(recepcion_factura)

                if sub_root.findall('.//Detalle'):
                    # Crear el array para Listado Lineas de Detalle de la Factura
                    detalles_data = []
                    for detalle in sub_root.findall('.//Detalle'):
                        # Crear un diccionario con los campos del Detalle
                        detalle_dict = {
                            'TpoCodigo': detalle.find('.//TpoCodigo').text if detalle.find('.//TpoCodigo') is not None else None,
                            'VlrCodigo': detalle.find('.//VlrCodigo').text if detalle.find('.//VlrCodigo') is not None else None,
                            'NmbItem': detalle.find('NmbItem').text if detalle.find('NmbItem') is not None else None,
                            'DscItem': detalle.find('DscItem').text if detalle.find('DscItem') is not None else None,
                            'QtyItem': detalle.find('QtyItem').text if detalle.find('QtyItem') is not None else None,
                            'PrcItem': detalle.find('PrcItem').text if detalle.find('PrcItem') is not None else None,
                            'MontoItem': detalle.find('MontoItem').text if detalle.find('MontoItem') is not None else None,
                        }

                        # Agregar el diccionario al array
                        detalles_data.append(detalle_dict)

                    logging.info("Detalle Factura es: {}".format(' '.join(map(str, detalles_data))))

                # Inicializar la variable para el ID de la factura creada
                factura_id = False
                
                # Crear un punto de guardado en la base de datos
                cr = http.request.env.cr
                cr.execute('SAVEPOINT factura_savepoint')
                try:
                   # Crear el objeto `account.move` con los datos de la factura
                    factura_vals = {
                        'partner_id': '',
                        'date': '',
                        'invoice_date_due': '',
                        'journal_id': '',
                        'company_id': '',
                        'state': 'draft'
                    }
                    factura_obj = http.request.env['account.move']
                    #factura = factura_obj.create(factura_vals)
                    
                    # Guardar el ID de la factura creada
                    #factura_id = factura.id if factura else False

                    # Crear los objetos `account.move.line` con los datos de las líneas de detalle
                    detalles_obj = http.request.env['account.move.line']
                    for detalle_data in detalles_data:
                        detalle_vals = {
                            #'move_id': factura_id,
                            'product_id': '',
                            'quantity': '',
                            'price_unit': ''
                        }
                        #detalles_obj.create(detalle_vals)
                        
                    # Validar la factura y confirmarla
                    #factura.action_post()

                except UserError as e:
                    # Si ocurre un error, hacer rollback a la transacción anterior y devolver el mensaje de error
                    cr.execute('ROLLBACK TO SAVEPOINT factura_savepoint')
                    return http.Response(str(e), status=400)
                
                # Si todo sale bien, hacer commit de los cambios en la base de datos
                cr.execute('RELEASE SAVEPOINT factura_savepoint')
                
                # Devolver el ID de la factura creada
                return http.Response(str(factura_id), status=201)

            else:
                return http.Response('El Contenido del XML no tiene la Factura.', status=401)
            
