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


class BcnGetw1InsertOc(http.Controller):
    logger = logging.getLogger() 

   
 # Main, método valida username/password, Obtiene DB Relacionada por GET y Company_ID desde el auth del usuario
    @http.route('/bcn_getw1/insert_oc', type='http', auth='none', methods=['POST'], csrf=False)
    def post_insert_oc(self, **kw):
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
                orden_compra_id_element = sub_root.find('.//id')
                orden_compra_id =orden_compra_id_element.text if orden_compra_id_element is not None else None
                
                    
                codigo_element = sub_root.find('.//codigo')
                codigo = codigo_element.text if codigo_element is not None else None                
                    
                dte_emisor_element = sub_root.find('.//emisor_rut')
                dte_emisor = dte_emisor_element.text if dte_emisor_element is not None else None                
                        
                emisor_rz_element = sub_root.find('.//emisor_rz')
                emisor_rz = emisor_rz_element.text if emisor_rz_element is not None else None
                
                proveedor_id_element = sub_root.find('.//proveedor_id')
                proveedor_id = proveedor_id_element.text if proveedor_id_element is not None else None
                
                proveedor_rut_element = sub_root.find('.//proveedor_rut')
                proveedor_rut = proveedor_rut_element.text if proveedor_rut_element is not None else None
                
                proveedor_nombre_element = sub_root.find('.//proveedor_nombre')
                proveedor_nombre = proveedor_nombre_element.text if proveedor_nombre_element is not None else None
                
                fecha_emision_element = sub_root.find('.//fecha_emision')
                fecha_emision = fecha_emision_element.text if fecha_emision_element is not None else None
                
                monto_total_element = sub_root.find('.//monto_total')
                monto_total = monto_total_element.text if monto_total_element is not None else None
                
                monto_neto_element = sub_root.find('.//monto_neto')
                monto_neto = monto_neto_element.text if monto_total_element is not None else None
                
                monto_impuestos_element = sub_root.find('.//monto_impuestos')
                monto_impuestos = monto_impuestos_element.text if monto_impuestos_element is not None else None
                
                monto_descuento_element = sub_root.find('.//monto_descuento')
                monto_descuento = monto_descuento_element.text if monto_descuento_element is not None else None
                
                monto_afecto_element = sub_root.find('.//monto_afecto')
                monto_afecto = monto_afecto_element.text if monto_afecto_element is not None else None
                
                monto_exento_element = sub_root.find('.//monto_exento')
                monto_exento = monto_exento_element.text if monto_exento_element is not None else None
                
                monto_retencion_element = sub_root.find('.//monto_retencion')
                monto_retencion = monto_retencion_element.text if monto_retencion_element is not None else None
                
                monto_impuesto_adicional_element = sub_root.find('.//monto_impuesto_adicional')
                monto_impuesto_adicional = monto_impuesto_adicional_element.text if monto_impuesto_adicional_element is not None else None
                
                fecha_creacion_element = sub_root.find('.//fecha_creacion')
                fecha_creacion = fecha_creacion_element.text if fecha_creacion_element is not None else None
                
                comprador_element = sub_root.find('.//comprador')
                comprador = comprador_element.text if comprador_element is not None else None
                
                comprador_area_element = sub_root.find('.//comprador_area')
                comprador_area = comprador_area_element.text if comprador_area_element is not None else None
                
                lugar_entrega_element = sub_root.find('.//lugar_entrega')
                lugar_entrega = lugar_entrega_element.text if lugar_entrega_element is not None else None
                
                fecha_entrega_element = sub_root.find('.//fecha_entrega')
                fecha_entrega = fecha_entrega_element.text if fecha_entrega_element is not None else None
                
                forma_pago_element = sub_root.find('.//forma_pago')
                forma_pago = forma_pago_element.text if forma_pago_element is not None else None
                
                solicitante_element = sub_root.find('.//solicitante')
                solicitante = solicitante_element.text if solicitante_element is not None else None
                
                rubro_id_element = sub_root.find('.//rubro_id')
                rubro_id = rubro_id_element.text if rubro_id_element is not None else None
                
                rubro_descripcion_element = sub_root.find('.//rubro_descripcion')
                rubro_descripcion = rubro_descripcion_element.text if rubro_descripcion_element is not None else None
                
                proyecto_element = sub_root.find('.//proyecto')
                proyecto = proyecto_element.text if proyecto_element is not None else None
                
                moneda_element = sub_root.find('.//moneda')
                moneda = moneda_element.text if moneda_element is not None else None
                
                observaciones_element = sub_root.find('.//observaciones')
                observaciones = observaciones_element.text if observaciones_element is not None else None
                
                #Fin Encabezado
                
                #Inicio Items
                
                d_codigo_element = sub_root.find('./items/d_codigo')
                d_codigo = d_codigo_element.text if d_codigo_element is not None else None
                
                item_linea_element = sub_root.find('./items/item_linea')
                item_linea = item_linea_element.text if item_linea_element is not None else None
                
                item_codigo_element = sub_root.find('./items/item_codigo')
                item_codigo = item_codigo_element.text if item_codigo_element is not None else None
                
                item_codigo_proveedor_element = sub_root.find('./items/item_codigo_proveedor')
                item_codigo_proveedor = item_codigo_proveedor_element.text if item_codigo_proveedor_element is not None else None
                
                item_nombre_element = sub_root.find('./items/item_nombre')
                item_nombre = item_nombre_element.text if item_nombre_element is not None else None
                
                item_descripcion_element = sub_root.find('./items/item_descripcion')
                item_descripcion = item_descripcion_element.text if item_descripcion_element is not None else None
                
                cantidad_element = sub_root.find('./items/cantidad')
                cantidad = cantidad_element.text if cantidad_element is not None else None   
                             
                unitario_element = sub_root.find('./items/unitario')
                unitario = unitario_element.text if unitario_element is not None else None
                
                factor_conversion_element = sub_root.find('./items/factor_conversion')
                factor_conversion = factor_conversion_element.text if factor_conversion_element is not None else None
                
                monto_linea_element = sub_root.find('./items/monto_linea')
                monto_linea = monto_linea_element.text if monto_linea_element is not None else None
                
                centro_costo_element = sub_root.find('./items/centro_costo')
                centro_costo = centro_costo_element.text if centro_costo_element is not None else None
                
                proyecto_element = sub_root.find('./items/proyecto')
                proyecto_item = proyecto_element.text if proyecto_element is not None else None
                
                gravable_element = sub_root.find('./items/gravable')
                gravable = gravable_element.text if gravable_element is not None else None
                
                observaciones_element = sub_root.find('./items/observaciones')
                observaciones = observaciones_element.text if observaciones_element is not None else None
                
                impuesto_element = sub_root.find('./items/impuesto')
                impuesto = impuesto_element.text if impuesto_element is not None else None
                
                descuento_element = sub_root.find('./items/descuento')
                descuento = descuento_element.text if descuento_element is not None else None
                #Fin Items
                
                #Inicio Abrobaciones   
                             
                estado_element = sub_root.find('./aprobaciones/estado')
                estado = estado_element.text if estado_element is not None else None
                
                ruta_codigo_element = sub_root.find('./aprobaciones/ruta_codigo')
                ruta_codigo = ruta_codigo_element.text if ruta_codigo_element is not None else None
                
                ruta_tipo_element = sub_root.find('./aprobaciones/ruta_tipo')
                ruta_tipo = ruta_tipo_element.text if ruta_tipo_element is not None else None
                
                ruta_fecha_element = sub_root.find('./aprobaciones/ruta_fecha')
                ruta_fecha= ruta_fecha_element.text if ruta_fecha_element is not None else None
                
                regla_codigo_element = sub_root.find('./aprobaciones/regla_codigo')
                regla_codigo = regla_codigo_element.text if regla_codigo_element is not None else None
                
                regla_fecha_element = sub_root.find('./aprobaciones/regla_fecha')
                regla_fecha = regla_fecha_element.text if regla_fecha_element is not None else None
                #Fin Aprobaciones
                
                #Inicio Abrobaciones_Secuencias   
                             
                secuencia_element = sub_root.find('./aprobaciones_secuencias/secuencia')
                secuencia = secuencia_element.text if secuencia_element is not None else None
                
                usuario_codigo_element = sub_root.find('./aprobaciones_secuencias/usuario_codigo')
                usuario_codigo = usuario_codigo_element.text if usuario_codigo_element is not None else None
                
                usuario_nombre_element = sub_root.find('./aprobaciones_secuencias/usuario_nombre')
                usuario_nombre = usuario_nombre_element.text if usuario_nombre_element is not None else None
                
                usuario_cargo_element = sub_root.find('./aprobaciones_secuencias/usuario_cargo')
                usuario_cargo= usuario_cargo_element.text if usuario_cargo_element is not None else None
                
                observacion_element = sub_root.find('./aprobaciones_secuencias/observacion')
                observacion = observacion_element.text if observacion_element is not None else None
                
                fecha_respuesta_element = sub_root.find('./aprobaciones_secuencias/fecha_respuesta')
                fecha_respuesta = fecha_respuesta_element.text if fecha_respuesta_element is not None else None
                #Fin Aprobaciones_Secuencias
                
                
                 
                #Inicio Observaciones
                observaciones = sub_root.findall('./observaciones/observacion')
                usuarios = []
                fechas = []
                textos = []
                for observacion in observaciones:
                    usuario_element = observacion.find('usuario')
                    usuario = usuario_element.text if usuario_element is not None else None
                    if usuario:
                        usuarios.append(usuario)
                    
                    fecha_element = observacion.find('fecha')
                    fecha = fecha_element.text if fecha_element is not None else None
                    if fecha:
                        fechas.append(fecha)
                        
                    texto_element = observacion.find('texto')
                    texto = texto_element.text if texto_element is not None else None
                    if texto:
                        textos.append(texto)
                    
                
                    
                
                if  orden_compra_id and codigo and dte_emisor and emisor_rz and proveedor_id and proveedor_rut and proveedor_nombre and fecha_emision and monto_total and monto_neto and monto_impuestos and monto_descuento and monto_afecto and monto_exento and monto_retencion and monto_impuesto_adicional and fecha_creacion and comprador and comprador_area and lugar_entrega and fecha_entrega and forma_pago and solicitante and rubro_id and rubro_descripcion and moneda and observaciones and d_codigo and item_linea and item_codigo and item_nombre and cantidad and unitario and factor_conversion and monto_linea and centro_costo and gravable and  observaciones and impuesto and descuento and estado and ruta_codigo and secuencia and usuario_codigo and usuario_nombre and usuario_cargo  and fecha_respuesta and usuario:
                
                  #return http.Response(str(usuarios), status=201)
                
                  return http.Response(str(orden_compra_id) + " Orden con codigo: " + str(codigo) + ", dte_emisor: " + str(dte_emisor)+ ", emisor_rz: " + str(emisor_rz)+ ", proveedor_id: " + str(proveedor_id) + ", proveedor_rut: " + str(proveedor_rut) + ", proveedor_nombre: " + str(proveedor_nombre)+ ", fecha_emision: " + str(fecha_emision)+ ", monto_total: " + str(monto_total)+ ", monto_neto: " + str(monto_neto)+ ", monto_impuestos: " + str(monto_impuestos) + ", monto_descuento: " + str(monto_descuento)+ ", monto_afecto: " + str(monto_afecto)+ ", monto_exento: " + str(monto_exento)+ ", monto_retencion: " + str(monto_retencion)+ ", monto_impuesto_adicional: " + str(monto_impuesto_adicional)+ ", fecha_creacion: " + str(fecha_creacion)+ ", comprador: " + str(comprador)+ ", comprador_area: " + str(comprador_area)+ ", lugar_entrega: " + str(lugar_entrega)+ ", fecha_entrega: " + str(fecha_entrega)+ ", forma_pago: " + str(forma_pago)+ ", solicitante: " + str(solicitante)+ ", rubro_id: " + str(rubro_id)+ ", rubro_descripcion: " + str(rubro_descripcion)+ ", proyecto: " + str(proyecto)+ ", moneda: " + str(moneda)+ ", d_codigo: " + str(d_codigo)+ ", item_linea: " + str(item_linea)+ ", item_codigo: " + str(item_codigo)+ ", item_codigo_proveedor: " + str(item_codigo_proveedor)+ ", item_nombre: " + str(item_nombre)+ ", item_descripcion: " + str(item_descripcion)+ ", cantidad: " + str(cantidad)+ ", unitario: " + str(unitario)+ ", descuento: " + str(descuento)+ ", monto_linea: " + str(monto_linea)+ ", centro_costo: " + str(centro_costo)+ ", gravable: " + str(gravable)+  ", proyecto_item: " + str(proyecto_item)+", impuesto: " + str(impuesto)+ ", estado: " + str(estado)+ ", ruta_codigo: " + str(ruta_codigo)+ ", ruta_tipo: " + str(ruta_tipo)+ ", ruta_fecha: " + str(ruta_fecha)+ ", regla_codigo: " + str(regla_codigo)+ ", regla_fecha: " + str(regla_fecha)+ ", secuencia: " + str(secuencia)+ ", usuario_codigo: " + str(usuario_codigo)+ ", usuario_nombre: " + str(usuario_nombre)+ ", usuario_cargo: " + str(usuario_cargo)+  ", fecha_respuesta: " + str(fecha_respuesta)+ ", usuarios: " + str(usuarios)+ ", fechas: " + str(fechas)+ ", textos: " + str(textos),  status=201)
                      
                      
                else: 
                    return http.Response('La Orden de compra no trae los campos completos .', status=401)                        
                    
               
                     
            
