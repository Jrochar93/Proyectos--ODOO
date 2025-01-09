#-- coding: utf-8 --
from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError

#Lib Call Websrevice
import requests
import json

#STRING TO XML
import xml.etree.ElementTree as ET
import base64

#Lib Config Logger
import logging 
logging.basicConfig(filename="/var/log/odoo/odoo-server.log", 
					format='%(asctime)s %(message)s', 
					filemode='w') 


class InvoiceFudColombia(models.Model):
    _name = 'invoice.fud.co'
    invoice_id = fields.Many2one('account.move', string='Invoice')

    #Instancia Logger
    logger = logging.getLogger() 
    
    #Usar solo para ver query y registros de toda la herencia.
    #logger.setLevel(logging.DEBUG) 

    #-----------------------------------------------        
    #  Casteo de valores según tipo dato
    #-----------------------------------------------
    def valida_valor_tipo_dato(self, tipo_dato, valor, largo):

        if tipo_dato == "integer":
            mod_value = int(valor)
        elif tipo_dato == "float":
            mod_value = float(valor)
        elif tipo_dato == "string":
            mod_value = str(valor)[ 0 : largo]
        else:
            mod_value = valor

        return mod_value
        
    #-----------------------------------------------        
    #  Determina el Nodo Base para Secciones (Detalle, Referencias)
    #-----------------------------------------------
    def get_origin_node_by_seccion(self, seccion):
        if seccion == "DETALLE":
            return "invoice_line_ids"
        elif seccion == "REFERENCIA":
            return "bcn_reference_ids"
        else:
            return False

    #-----------------------------------------------        
    #  Obtiene Nombre Sección según FUD
    #-----------------------------------------------
    def get_seccion_by_id(self, seccion_id):
        #TODO ELIMINAR ID DE SECCION REEMPLAZAR POR TEXTO, ES MAS FACIL TRAZAR
        if seccion_id == 1:
            return "ENCABEZADO"
        elif seccion_id == 2:
            return "PAGO"
        elif seccion_id == 3:
            return "REFERENCIA"
        elif seccion_id == 4:
            return "IMPUESTO O RETENCION"
        elif seccion_id == 5:
            return "IMP O RET LINEAS"
        elif seccion_id == 6:
            return "DESCUENTO O RECARGO"
        elif seccion_id == 7:
            return "DETALLE"
        else:
            return False

    #-----------------------------------------------        
    #  Base gerenación de FUD 
    #-----------------------------------------------
    def genera_fud(self, invoice_fud):

        #Obtiene Listado Encabezado y Procesa
        list_diccionariofud_encabezado  = self.env['bcn.dictionaryfud'].search_read([('tipo_doc', 'in', [str(invoice_fud.l10n_latam_document_type_id.code),'0']),('pais','=',str(invoice_fud.company_id.country_id.code)),('seccion','=','1'),('relacion_db','!=','')])
        logging.info("ENCABEZADO: {}".format(' '.join(map(str, list_diccionariofud_encabezado))))
        
        fud_seccion_encabezado = self.valida_seccion_empty(1, invoice_fud, list_diccionariofud_encabezado)
        #Obtiene Listado Detalle y Procesa
        list_diccionariofud_detalle     = self.env['bcn.dictionaryfud'].search_read([('tipo_doc', 'in', [str(invoice_fud.l10n_latam_document_type_id.code),'0']),('pais','=',str(invoice_fud.company_id.country_id.code)),('seccion','=','2'),('relacion_db','!=','')])
		#logging.info('list_diccionariofud_detalle')
        logging.info(list_diccionariofud_detalle)										   
												 
        fud_seccion_detalle = self.valida_seccion_empty(2, invoice_fud, list_diccionariofud_detalle)
		
        #Obtiene Listado Referencia y Procesa
        list_diccionariofud_referencia  = self.env['bcn.dictionaryfud'].search_read([('tipo_doc', 'in', [str(invoice_fud.l10n_latam_document_type_id.code),'0']),('pais','=',str(invoice_fud.company_id.country_id.code)),('seccion','=','3'),('relacion_db','!=','')])
		#logging.info('list_diccionariofud_referencia')
        logging.info(list_diccionariofud_referencia)											  
													
        fud_seccion_referencia = self.valida_seccion_empty(3, invoice_fud, list_diccionariofud_referencia)
        #Obtiene Listado Descuentos y Procesa
        list_diccionariofud_descuentos  = self.env['bcn.dictionaryfud'].search_read([('tipo_doc', 'in', [str(invoice_fud.l10n_latam_document_type_id.code),'0']),('pais','=',str(invoice_fud.company_id.country_id.code)),('seccion','=','4'),('relacion_db','!=','')])
        fud_seccion_descuentos = self.valida_seccion_empty(4, invoice_fud, list_diccionariofud_descuentos)
        #Obtiene Listado Comision y Procesa
        list_diccionariofud_comision    = self.env['bcn.dictionaryfud'].search_read([('tipo_doc', 'in', [str(invoice_fud.l10n_latam_document_type_id.code),'0']),('pais','=',str(invoice_fud.company_id.country_id.code)),('seccion','=','5'),('relacion_db','!=','')])
        fud_seccion_comision = self.valida_seccion_empty(5,invoice_fud,  list_diccionariofud_comision)
        #Obtiene Listado Subtotal y Procesa
        list_diccionariofud_subtotal    = self.env['bcn.dictionaryfud'].search_read([('tipo_doc', 'in', [str(invoice_fud.l10n_latam_document_type_id.code),'0']),('pais','=',str(invoice_fud.company_id.country_id.code)),('seccion','=','6'),('relacion_db','!=','')])
        fud_seccion_subtotal = self.valida_seccion_empty(6, invoice_fud, list_diccionariofud_subtotal)
        
        list_diccionario_detalle    = self.env['bcn.dictionaryfud'].search_read([('tipo_doc', 'in', [str(invoice_fud.l10n_latam_document_type_id.code),'0']),('pais','=',str(invoice_fud.company_id.country_id.code)),('seccion','=','7'),('relacion_db','!=','')])
        fud_seccion_detalle = self.valida_seccion_empty(7, invoice_fud, list_diccionario_detalle)

        #Validación Minima para Generar FUD
        if not list_diccionariofud_encabezado or not list_diccionariofud_detalle:
            return False
        else:
            # Validación para concatenar texos según seccion para el FUD
            full_fud = fud_seccion_encabezado + fud_seccion_detalle
            if( fud_seccion_referencia):
                full_fud = full_fud + "\n" + fud_seccion_referencia
            if( fud_seccion_descuentos):
                full_fud = full_fud + "\n" + fud_seccion_descuentos
            if( fud_seccion_comision):
                full_fud = full_fud + "\n" + fud_seccion_comision
            if( fud_seccion_subtotal):
                full_fud = full_fud + "\n" + fud_seccion_subtotal 
            
            if( fud_seccion_detalle):
                full_fud = full_fud + "\n" + fud_seccion_detalle     

            return full_fud
            
    #-----------------------------------------------        
    #  Validación de consistencia de Secciones
    #  Genera Base Text FUD
    #-----------------------------------------------
    def valida_seccion_empty(self, id_seccion, invoice_fud,  lista_diccionario):
        seccion = self.get_seccion_by_id(id_seccion)
        if not lista_diccionario:
            return False
        elif not seccion:
            return False
        else:
            if seccion == "ENCABEZADO":
                return self.genera_seccion_diccionario_fud(invoice_fud, seccion, lista_diccionario)
            else: 
                node_base_lista = self.get_origin_node_by_seccion(seccion)
                return self.genera_seccion_diccionario_fud_lineas(invoice_fud, seccion, lista_diccionario, node_base_lista)

    #-----------------------------------------------        
    #  Aplicación de Lineas de Excención Generales
    #-----------------------------------------------
    def get_lineas_exencion_documento(self, invoice_fud):
        lineas_exencion = list()
        position = 1
        for record in invoice_fud.invoice_line_ids:
            if (str(record.tax_ids.amount) == "0.0"):
                lineas_exencion.append(position)
            position +=1
        return lineas_exencion


    #-----------------------------------------------        
    # Validación Aplicación de Linea Excención Documento Detalle
    #-----------------------------------------------
    def valida_exencion_linea_documento(self, nro_linea, lista_exencion_documento):
            
        #Validación Indicador Exencion para Doc que contiene la linea
        if nro_linea in lista_exencion_documento:
            linea_exencion =  "|1|"

        #Validación Indicador Exencion para Doc que NO contiene la linea
        elif lista_exencion_documento and (nro_linea not in lista_exencion_documento):
            linea_exencion =  "| |"
        #Caso normal
        else:
            linea_exencion = "|"

        return linea_exencion

    #-----------------------------------------------        
    # Validación Aplicación de Excención Documento
    #-----------------------------------------------
    def valida_exencion_encabezado_documento(self, invoice_fud, seccion):
        
        linea_encabezado = ""
        lista_exencion_documento = list()
        # Condición Seccion Detalle y Factura Electronica (33) si tiene alguna linea con monto tasa 0 aplica indicador Exencion Encabezado
        # Validación Indicador Exencion para Doc Nota Debito (56) y Nota Credito (61)
        if seccion == 'DETALLE' and (str(invoice_fud.l10n_latam_document_type_id.code) == "33" or (invoice_fud.l10n_latam_document_type_id.code == '56' or invoice_fud.l10n_latam_document_type_id.code == '61')):
            
            linea_encabezado = "| Indicador Exencion |"
            lista_exencion_documento = self.get_lineas_exencion_documento(invoice_fud)

        return linea_encabezado, lista_exencion_documento

    #-----------------------------------------------        
    # Obtiene Codigo Inicial de Lineas por tipo Seccion
    #-----------------------------------------------
    def get_linea_encabezado_seccion(self, seccion):

        if seccion == 'DETALLE':
            desc_linea = 'Nro.Linea'
        elif seccion == 'REFERENCIA':
            desc_linea = 'Nro Linea Referencia'
        else:
            desc_linea = 'Nro.Linea'
        
        return desc_linea

    
    #-----------------------------------------------        
    # Genera Text FUD para Lineas (Detalle, Referencia, ETC)
    #-----------------------------------------------
    def genera_seccion_diccionario_fud_lineas(self, invoice_fud, seccion, diccionario_fud, nodo_base):
		#
        logging.info(nodo_base)
							   
        linea_valores = ""
        nro_linea = 0
        count_campos_cabecera = 0
        total_cabecera_diccionario = len(diccionario_fud) 

        #Obtiene Codigo Inicial de Lineas por tipo Seccion
        desc_linea = self.get_linea_encabezado_seccion(seccion)

        #Validación Indicador Exencion para Doc Nota Debito (56) y Nota Credito (61)
        indicador_exencion = False
        lista_exencion_documento = list()



        #TODO REPLACE encabezado_exencion, lista_exencion_documento = self.valida_exencion_encabezado_documento(invoice_fud, seccion):

        if (invoice_fud.l10n_latam_document_type_id.code == '56' or invoice_fud.l10n_latam_document_type_id.code == '61')  and (seccion == 'DETALLE'):
            #indicador_exencion = True
            #logging.info("INDICADOR EXENCION "+self.l10n_latam_document_type_id.code+"\n")
            #linea_encabezado = "<"+seccion+">"+"\n"+"Nro.Linea | Indicador Exencion |"
            lista_exencion_documento = self.get_lineas_exencion_documento(invoice_fud)
            
        else:
            linea_encabezado = "<"+seccion+">"+"\n"+desc_linea+" |"
        
        # Condición Seccion Detalle y Factura Electronica (33) si tiene alguna linea con monto tasa 0 aplica indicador Exencion Encabezado
        if seccion == 'DETALLE' and str(invoice_fud.l10n_latam_document_type_id.code) == "33":
            lista_exencion_documento = self.get_lineas_exencion_documento(invoice_fud)
        
        # Si cumple condición de Excención genera encabezado
        if lista_exencion_documento : 
            linea_encabezado = "<"+seccion+">"+"\n"+"Nro.Linea | Indicador Exencion |"
        else:
            linea_encabezado = "<"+seccion+">"+"\n"+desc_linea+" |"

        #TODO REPLACE encabezado_exencion, lista_exencion_documento = self.valida_exencion_encabezado_documento(invoice_fud, seccion):




        for record in invoice_fud[nodo_base]:
            nro_linea += 1
            count_insert_value_diccionario = 1

            #Validación de multiples lineas
            if linea_valores != "":
                linea_valores = linea_valores + "\n"
            




            #TODO REPLACE flag_exencion_linea = valida_exencion_linea_documento(nro_linea)
            
            #Validación Indicador Exencion para Doc 56 y 61
            if indicador_exencion :
                linea_valores = linea_valores + str(nro_linea) + "|1|"
            #Validación Indicador Exencion para Doc 33 que SI contiene la linea
            elif nro_linea in lista_exencion_documento:
                linea_valores = linea_valores + str(nro_linea) + "|1|"
            #Validación Indicador Exencion para Doc 33 que NO contiene la linea
            elif lista_exencion_documento and (nro_linea not in lista_exencion_documento):
                linea_valores = linea_valores + str(nro_linea) + "| |"
            #Caso normal
            else:
                linea_valores = linea_valores + str(nro_linea) + "|"    
            
            #TODO REPLACE flag_exencion_linea = valida_exencion_linea_documento(nro_linea)





            #Loop Diccionario Fud Seccion
            for detalle_diccionario in diccionario_fud:

                #Generación Cabecera Texto
                count_campos_cabecera +=1
                if  count_campos_cabecera <= total_cabecera_diccionario:
                    if count_campos_cabecera < total_cabecera_diccionario:
                        linea_encabezado = linea_encabezado + "" + str(detalle_diccionario["name"]) + "|"
                    if count_campos_cabecera == total_cabecera_diccionario:
                        linea_encabezado = linea_encabezado + "" + str(detalle_diccionario["name"])
                    
                #Generación Valores por Linea
                value = ""
                parse_nodes_row = detalle_diccionario["relacion_db"].split(".")
                if len(parse_nodes_row) > 1:
                    #Navegación Nodo por Nivel
                    for node_object in parse_nodes_row:
                        if value == "":
                            value = record[node_object]
                        else: 
                            value = value[node_object]
                else:
                    value = record[detalle_diccionario["relacion_db"]]

                if value == "":
                    value  = detalle_diccionario["valor_default"]
                else:
                    value = self.valida_valor_tipo_dato(detalle_diccionario["tipo_dato"], value, detalle_diccionario["largo"])
                
                #Validación Ultimo Valor de Linea
                if count_insert_value_diccionario < total_cabecera_diccionario:
                    linea_valores = linea_valores + str(value) + "|"
                else:
                    linea_valores = linea_valores + str(value)

                count_insert_value_diccionario +=1
            
        return str(linea_encabezado)+"\n"+ linea_valores

    #-----------------------------------------------        
    # Genera Text FUD para Lineas (Detalle, Referencia, ETC)
    #-----------------------------------------------
    def genera_seccion_diccionario_fud(self, invoice_fud, nombre_seccion, diccionario_fud):
        
        encabezado_text = "<"+nombre_seccion+"> \n"


        for record in diccionario_fud:
            parse_nodes_row = record["relacion_db"].split(".")
            
            value = ""

            for node_object in parse_nodes_row:
                if value == "":
                    value = invoice_fud[node_object]
                else: 
                    value = value[node_object]

            if value == "":
                value  = record["valor_default"]

            value = self.valida_valor_tipo_dato(record["tipo_dato"], value, record["largo"])
            if (str(record["name"]) == 'IVA' or str(record["name"]) == 'Tasa IVA' ) and (str(value) == "0" or str(value) == "0.0") :
                logging.info("Valor Iva o Tasa Iva no se adjuntan en caso de tener valor 0. \n")
            else:

                # TODO ESTO SOLO ES CASO BCN, VER CON JZAMUDIO UNA LOGICA MEJOR O MAPEAR UN CAMPO QUE NO SEA EL MISMO. 
                # DEBO DISCRIMINAR NOTA DEBITO AFECTA DE EXCENTA Y LO MISMO PARA NOTA CREDITO
                if (invoice_fud.l10n_latam_document_type_id.code == '56' or invoice_fud.l10n_latam_document_type_id.code == '61' ):
                    if str(record["name"]) == "Monto Neto" and (str(invoice_fud['amount_tax']) == '0' or str(invoice_fud['amount_tax']) == '0.0'):
                        record["name"] = "Monto Exento"


                encabezado_text = encabezado_text + str(record["name"]) +"      | "+ str(value) + "\n"

        return encabezado_text

    #-----------------------------------------------        
    # Demo Prueba Datos y Referencias
    #-----------------------------------------------
    def demo_test_hardcode(self, invoice_fud):

        fudtxt="<ENCABEZADO>\n"
        fudtxt=fudtxt+"TipoDocumento                            |1\n"
        fudtxt=fudtxt+"NumeroDocumento                          |SETT7139\n"
        fudtxt=fudtxt+"FechaEmision                             |2023-11-01\n"
        fudtxt=fudtxt+"HoraEmision                              |00:00:00-05:00\n"
        fudtxt=fudtxt+"TipoFactura                              |01\n"
        fudtxt=fudtxt+"TipoOperacion                            |10\n"
        fudtxt=fudtxt+"PrefijoPOS                               |\n"
        fudtxt=fudtxt+"TipoMoneda                               |COP\n"
        fudtxt=fudtxt+"NumeroMatricula                          |\n"
        fudtxt=fudtxt+"TerceroTipoEmpresa                       |1\n"
        fudtxt=fudtxt+"TerceroNroDoc                            |901088196\n"
        fudtxt=fudtxt+"TerceroNroDocDV                          |1\n"
        fudtxt=fudtxt+"TerceroIdenDoc                           |31\n"
        fudtxt=fudtxt+"TerceroRegimen                           |2\n"
        fudtxt=fudtxt+"TerceroRazonSocial                       |VIRUTEX ILKO COLOMBIA S.A.S.\n"
        fudtxt=fudtxt+"TerceroResponsabilidades                 |R-99-PN\n"
        fudtxt=fudtxt+"xTerceroTelefono                         |\n"
        fudtxt=fudtxt+"TerceroDepartamento                      |CAUCA\n"
        fudtxt=fudtxt+"TerceroDepartamentoCodigo                |19\n"
        fudtxt=fudtxt+"TerceroMunicipioCodigo                   |19573\n"
        fudtxt=fudtxt+"TerceroCiudad                            |PUERTO TEJADA\n"
        fudtxt=fudtxt+"TerceroDireccion                         |ZONA FRANCA DEL CAUCA ETAPA 4 LOTE 12\n"
        fudtxt=fudtxt+"TerceroPaisCodigo                        |CO\n"
        fudtxt=fudtxt+"TerceroPais                              |Colombia\n"
        fudtxt=fudtxt+"TerceroContactoCorreo                    |kelly.gonzalez@virutexilko.com.co\n"
        fudtxt=fudtxt+"TerceroTributoID                         |01\n"
        fudtxt=fudtxt+"TerceroTributoNombre                     |IVA\n"
        fudtxt=fudtxt+"NetoLineas                               |1845788,00\n"
        fudtxt=fudtxt+"Total                                    |2196488,00\n"
        fudtxt=fudtxt+"TotalBaseImponible                       |1845788,00\n"
        fudtxt=fudtxt+"TotalImpuestoIncluidos                   |2196488,00\n"
        fudtxt=fudtxt+"ImpuestoTotal_01                         |350700,00\n"
        fudtxt=fudtxt+"<IMPUESTO O RETENCION>\n"
        fudtxt=fudtxt+"ImpRetTipo|ImpRetCodigo|ImpRetNombre|ImpRetTasa|ImpRetBase|ImpRetValor\n"
        fudtxt=fudtxt+"IMPUESTO|01|IVA|19,00|1845788,00|350700,00\n"
        fudtxt=fudtxt+"<PAGO>\n"
        fudtxt=fudtxt+"PagoMetodo|PagoMedioCodigo|PagoFecha|PagoID\n"
        fudtxt=fudtxt+"2|47|2023-12-01|1\n"
        fudtxt=fudtxt+"<DETALLE>\n"
        fudtxt=fudtxt+"ItemLinea|ItemCantidad|ItemValorVenta|ItemDescripcion|ItemPrecioVentaUnit|ItemUM\n"
        fudtxt=fudtxt+"1|1,00|1845788,00|Servicio ASP Soporte y MantenciÃ³n TPW (Tomador Pedido web) mensual Periodo  2023/11|1845788,00|EA\n"
        fudtxt=fudtxt+"<IMP O RET LINEAS>\n"
        fudtxt=fudtxt+"ImpRetDetLinea|ImpRetDetTipo|ImpRetDetCodigo|ImpRetDetNombre|ImpRetDetTasa|ImpRetDetBase|ImpRetDetValor\n"
        fudtxt=fudtxt+"1|IMPUESTO|01|IVA|19,00|1845788,00|350700,00"
        return fudtxt

        #logging.info("Detalle ENCABEZADO es: {}".format(' '.join(map(str, list_diccionariofud_encabezado))))
        #logging.info("Procesando ENCABEZADO "+str(type(list_diccionariofud_encabezado))+"\n")
        encabezado_tex = "COLOMBIA<ENCABEZADO>\n"
        encabezado_tex = encabezado_tex + "NumeroDocumento | "+str(invoice_fud.name)+"\n"
        encabezado_tex = encabezado_tex + "FechaEmision | "+str(invoice_fud.invoice_date)+"\n"
        encabezado_tex = encabezado_tex + "HoraEmision | "+str(invoice_fud.create_date )+"\n"
        encabezado_tex = encabezado_tex + "TipoDocumento | "+str(invoice_fud.l10n_latam_document_type_id.code)+"\n"
        encabezado_tex = encabezado_tex + "TipoFactura | "+str(invoice_fud.l10n_latam_document_type_id.code)+"\n"
        encabezado_tex = encabezado_tex + "TipoOperacion | "+str(invoice_fud.l10n_latam_document_type_id.code)+"\n"
        encabezado_tex = encabezado_tex + "TipoMoneda | "+str(invoice_fud.name)+"\n"
        encabezado_tex = encabezado_tex + "TerceroTipoEmpresa | "+str(invoice_fud.company_id)+"\n"
        encabezado_tex = encabezado_tex + "TerceroNroDoc | "+str(invoice_fud.partner_id.vat)+"\n"
        encabezado_tex = encabezado_tex + "TerceroNroDocDV | "+str(invoice_fud.partner_id.x_studio_dv_nit)+"\n"
        encabezado_tex = encabezado_tex + "TerceroIdenDoc | "+str(31)+"\n"
        encabezado_tex = encabezado_tex + "TerceroResponsabilidades | "+str(invoice_fud.partner_id.vat)+"\n"
        encabezado_tex = encabezado_tex + "TerceroRegimen | "+str(invoice_fud.partner_id.name)+"\n"
        encabezado_tex = encabezado_tex + "TerceroRazonSocial | "+str(invoice_fud.partner_id.street)+"\n"
        encabezado_tex = encabezado_tex + "TerceroMunicipioCodigo | "+str(invoice_fud.company_id.city)+"\n"
        encabezado_tex = encabezado_tex + "TerceroCiudad | "+str(invoice_fud.company_id.city)+"\n"
        encabezado_tex = encabezado_tex + "TerceroDepartamento | "+str(invoice_fud.company_id.city)+"\n"
        encabezado_tex = encabezado_tex + "TerceroDepartamentoCodigo | "+str(invoice_fud.invoice_date)+"\n"
        encabezado_tex = encabezado_tex + "TerceroDireccion | "+str(invoice_fud.partner_id.street)+"\n"
        encabezado_tex = encabezado_tex + "TerceroPaisCodigo | "+str(invoice_fud.company_id.country_id.code)+"\n"
        encabezado_tex = encabezado_tex + "TerceroPais | "+str(invoice_fud.company_id.country_id.name)+"\n"
        encabezado_tex = encabezado_tex + "TerceroPaisLenguaje | "+str(invoice_fud.invoice_date_due)+"\n"
        encabezado_tex = encabezado_tex + "TipoCambioMonedaDesde  | "+str(invoice_fud.company_id.country_id.code)+"\n"
        encabezado_tex = encabezado_tex + "TipoCambioFactor | "+str(invoice_fud.amount_untaxed)+"\n"
        encabezado_tex = encabezado_tex + "TipoCambioFecha | "+str(invoice_fud.invoice_date_due)+"\n"
        encabezado_tex = encabezado_tex + "NetoLineas | "+str(invoice_fud.amount_untaxed)+"\n"
        encabezado_tex = encabezado_tex + "TotalBaseImponible | "+str(invoice_fud.invoice_date_due)+"\n"
        encabezado_tex = encabezado_tex + "TotalImpuestoIncluidos | "+str(invoice_fud.invoice_date_due)+"\n"
        encabezado_tex = encabezado_tex + "Total  | "+str(invoice_fud.amount_total)+"\n"

        
        #encabezado_tex = encabezado_tex + "Forma de Pago | "+str(invoice_fud.x_studio_forma_pago)+"\n"
        encabezado_tex = encabezado_tex + "Monto Total | "+str(invoice_fud.amount_total)+"\n"
        encabezado_tex = encabezado_tex + "Monto Neto | "+str(invoice_fud.amount_untaxed)+"\n"
        encabezado_tex = encabezado_tex + "ImpuestoTotal_01 | "+str(invoice_fud.amount_tax)+"\n"
        
        detalle_text = "<DETALLE>\n"
        detalle_text = detalle_text + "Nro.Linea|Tipo codigo|Codigo del Item|Nombre del Item|Descripcion Adicion al Item|Cantidad|Unidad de Medida|Precio Unitario Item|Monto Item \n"
        count = 0
        for record in invoice_fud.invoice_line_ids:
            count += 1
            detalle_text = detalle_text + str(count) +"| | |"+ str(record.product_id.name)+"|"+ str(record.product_id.name)+"|"+ str(record.quantity)+"| |"+ str(record.price_unit)+"|"+ str(record.price_subtotal)+"\n"

        referencia_text = "<REFERENCIA>\n"
        count = 0
        referencia_text = referencia_text + "Nro Linea Referencia|Folio Referencia|Tipo Documento Referencia|Fecha Referencia|Codigo Referencia|Razon Referencia \n"
        '''for record in invoice_fud.bcn_reference_ids:
            count += 1
            referencia_text = referencia_text + str(count) +"| | |"+ str(record.origin_doc_number)+"|"+ str(record.reference_doc_code)+"|"+ str(record.date)+"| |"+ str(record.l10n_cl_reference_doc_type_id.code)+"|"+ str(record.reason)+"\n"
        '''
        fud_text = encabezado_tex + detalle_text + referencia_text
        return fud_text
        