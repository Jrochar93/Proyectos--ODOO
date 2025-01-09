#-- coding: utf-8 --
from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError
from num2words import num2words
from datetime import datetime, timedelta
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


class BcnFudColombia(models.TransientModel):
    _name = 'bcn.fud.co'
    _inherit = 'bcn.fud'
    
    invoice_id = fields.Many2one('account.move', string='Invoice')

    #Instancia Logger
    logger = logging.getLogger() 
    
    #Usar solo para ver query y registros de toda la herencia.
    #logger.setLevel(logging.DEBUG) 

    #-----------------------------------------------        
    #  Constructor
    #-----------------------------------------------

   
    #-----------------------------------------------        
    #  Base gerenación de FUD  Encabezado
    #----------------------------------------------

    def genera_encabezado(self, invoice_fud):
        logging.info('genera_encabezado')
        tipo_doc = invoice_fud.l10n_latam_document_type_id.code
        name = invoice_fud.name
        name = name.replace(" ", "")
        self.agregarHeader('NumeroDocumento', name)
        
        # Obtener la fecha actual y la hora actual
        fecha_actual = datetime.now()
        hora_actual = fecha_actual.strftime('%H:%M:%S')    

        self.agregarHeader('FechaEmision', fecha_actual)
        self.agregarHeader('HoraEmision', hora_actual)
        TipoDocumento=invoice_fud.l10n_latam_document_type_id.code
        self.agregarHeader('TipoDocumento', TipoDocumento)
        if TipoDocumento=='1':
            TipoFactura=invoice_fud.tipo_factura
        else:
            TipoFactura=''
        self.agregarHeader('TipoFactura', TipoFactura)
        self.agregarHeader('TipoOperacion', invoice_fud.tipo_operacion)
        self.agregarHeader('TipoMoneda', 'COP')
        self.agregarHeader('TerceroTipoEmpresa', invoice_fud.partner_id.tercero_tipo_emp)
        TerceroNroDoc_con_dv = invoice_fud.partner_id.vat
        TerceroNroDoc = TerceroNroDoc_con_dv.split('-')[0]
        dvnit = TerceroNroDoc_con_dv.split('-')[1]
        self.agregarHeader('TerceroNroDoc', TerceroNroDoc)
        self.agregarHeader('TerceroNroDocDV', dvnit)
        self.agregarHeader('TerceroIdenDoc', invoice_fud.partner_id.l10n_latam_identification_type_id.l10n_co_document_code)
        self.agregarHeader('TerceroResponsabilidades', invoice_fud.partner_id.tercero_respon)
        self.agregarHeader('TerceroRegimen', invoice_fud.partner_id.tercero_regimen)
        self.agregarHeader('TerceroRazonSocial', invoice_fud.partner_id.name)
        TerceroMunicipioCodigo=invoice_fud.partner_id.zip
        self.agregarHeader('TerceroMunicipioCodigo', TerceroMunicipioCodigo)
        self.agregarHeader('TerceroCiudad', invoice_fud.partner_id.city)    
        # Convertir el número a una cadena
        TerceroMunicipioCod = str(TerceroMunicipioCodigo)
        # Obtener los dos primeros dígitos
        TerceroDepartamentoCodigo = TerceroMunicipioCod[:2]
        self.agregarHeader('TerceroDepartamento', invoice_fud.partner_id.city_id.state_id.name)
        self.agregarHeader('TerceroDepartamentoCodigo', TerceroDepartamentoCodigo)
        self.agregarHeader('TerceroDireccion', invoice_fud.partner_id.street)
        self.agregarHeader('TerceroPaisCodigo', invoice_fud.partner_id.country_id.code)
        self.agregarHeader('TerceroPais', invoice_fud.partner_id.country_id.name)
        idioma_completo = invoice_fud.partner_id.lang
        idioma_abreviado = idioma_completo.split('_')[0]
        self.agregarHeader('TerceroPaisLenguaje', idioma_abreviado)
        total_base_imponible = sum(
            invoice_line.price_subtotal
            for invoice_line in invoice_fud.invoice_line_ids
            if any(tax.imp_codigo == '01' for tax in invoice_line.tax_ids)
        )

        ImpuestoTotal_01 = sum(
            invoice_line.quantity * invoice_line.price_unit * tax.amount / 100
            for invoice_line in invoice_fud.invoice_line_ids
            for tax in invoice_line.tax_ids
            if tax.imp_codigo == '01'
        )
        xRetefuente= sum(
            invoice_line.quantity * invoice_line.price_unit * tax.amount / 100
            for invoice_line in invoice_fud.invoice_line_ids
            for tax in invoice_line.tax_ids
            if tax.imp_codigo == '05'
        )

        NetoLineas = sum(
            invoice_line.price_subtotal
            for invoice_line in invoice_fud.invoice_line_ids
        )

        self.agregarHeader('ImpuestoTotal_01', ImpuestoTotal_01)
        self.agregarHeader('TotalBaseImponible', total_base_imponible)
        self.agregarHeader('NetoLineas', NetoLineas)
        TotalImpuestoIncluidos = int(NetoLineas + ImpuestoTotal_01)
        self.agregarHeader('TotalImpuestoIncluidos', TotalImpuestoIncluidos)
        self.agregarHeader('Total', TotalImpuestoIncluidos)

        # Convertir el monto total a palabras
        monto_total_en_letras = num2words(TotalImpuestoIncluidos, lang='es').title()
        self.agregarHeader('MontoLetras', monto_total_en_letras)
        #self.agregarHeader('xRetefuente', xRetefuente)

        self.agregar_detalles_pagos(invoice_fud)
        self.agregar_detalles_impuestos_retenciones(invoice_fud)
        self.agregar_impuestos_retenciones(invoice_fud)

        # -----------------------------------------------
        # Base generación de FUD Detalles
        # ----------------------------------------------

        return  # Ajustado el return

    # -----------------------------------------------
    # Base generación de FUD Pagos
    # ----------------------------------------------


    def agregar_detalles_pagos(self, invoice_fud):
        pagos = []
        for pago in invoice_fud:
            PagoMedioCodigo = 42
            pago_data = {
                'PagoMetodo': pago.pago_metodo,
                'PagoMedioCodigo': PagoMedioCodigo,
                'PagoFecha': pago.invoice_date_due.strftime('%Y-%m-%d'),
                'PagoID': 1
            }
            pagos.append(pago_data)

        super().agregarDetail('PAGOS', pagos)


    # -----------------------------------------------
    # Base generación de FUD IMP O RET LINEAS
    # ----------------------------------------------
    # Crear una lista para almacenar todas las líneas desglosadas


    def agregar_detalles_impuestos_retenciones(self, invoice_fud):
        all_lines = []

        for count, linea in enumerate(invoice_fud.invoice_line_ids, start=1):
            imp_ret_linea = []

            # Obtener la tasa de impuesto para la línea actual
            ImpRetTasa = next(
                (tax.amount for tax in linea.tax_ids if tax.imp_codigo == '01'),
                0
            )

            if ImpRetTasa != 0:
                ImpRetTipo = 'IMPUESTO'
                ImpRetCodigo = '01'
                ImpRetNombre = 'IVA'

                # Calcular la base para la retención
                ImpRetBase = linea.price_subtotal

                # Crear el diccionario de datos para la línea desglosada
                imp_linea_data = {
                    'ImpRetDetLinea': count,
                    'ImpRetDetTipo': ImpRetTipo,
                    'ImpRetDetCodigo': ImpRetCodigo,
                    'ImpRetDetNombre': ImpRetNombre,
                    'ImpRetDetTasa': ImpRetTasa,
                    'ImpRetDetBase': ImpRetBase,
                    'ImpRetDetValor': ImpRetBase * ImpRetTasa / 100  # Calcular el valor de la retención
                }

                # Agregar la línea desglosada a la lista
                imp_ret_linea.append(imp_linea_data)

            # Agregar todas las líneas desglosadas al total
            all_lines.extend(imp_ret_linea)

        # Agregar la lista completa de líneas desglosadas a la estructura principal
        super().agregarDetail('IMP O RET LINEAS', all_lines)
        # -----------------------------------------------
        # Base generación de FUD IMPUESTO O RETENCION
        # ----------------------------------------------


    def agregar_impuestos_retenciones(self, invoice_fud):
        imp_retencion = []

        # Crear un diccionario para almacenar las líneas desglosadas por tasa
        imp_dict = {}

        for invoice_line in invoice_fud.invoice_line_ids:
            for tax in invoice_line.tax_ids:
                if tax.imp_codigo == '01':
                    ImpRetTasa = tax.amount

                    # Verificar si ya existe una línea con la misma tasa en el diccionario
                    if ImpRetTasa not in imp_dict:
                        imp_dict[ImpRetTasa] = {
                            'ImpRetTipo': 'IMPUESTO',
                            'ImpRetCodigo': '01',
                            'ImpRetNombre': 'IVA',
                            'ImpRetTasa': ImpRetTasa,
                            'ImpRetBase': 0.0,
                            'ImpRetValor': 0.0
                        }

                    # Actualizar la línea en el diccionario con los nuevos valores
                    imp_dict[ImpRetTasa]['ImpRetBase'] += invoice_line.price_subtotal
                    imp_dict[ImpRetTasa]['ImpRetValor'] += (
                        invoice_line.quantity * invoice_line.price_unit * ImpRetTasa / 100
                    )

        # Convertir el diccionario a una lista para el formato final
        imp_retencion = list(imp_dict.values())

        super().agregarDetail('IMPUESTO O RETENCION', imp_retencion)



    # -----------------------------------------------
    # Base generación de FUD Detalles
    # ----------------------------------------------


    def genera_detalles(self, invoice_fud):
        logging.info('genera_detalles')

        detalles = []

        for count, linea in enumerate(invoice_fud.invoice_line_ids, start=1):
            detalle = {}
            detalle['ItemLinea'] = count
            detalle['ItemCantidad'] = linea.quantity
            detalle['ItemUM'] = 94
            detalle['ItemPrecioVentaUnit'] = linea.price_unit
            detalle['ItemDescripcion'] = linea.name
            detalle['ItemVendedorCodigo'] = linea.account_id.id
            detalle['ItemValorVenta'] = linea.price_subtotal
            ItemDescRecIndicador = 'false'
            ItemDescRecIndicador = linea.discount
            if ItemDescRecIndicador != 0:
                ItemDescRecIndicador = 'true'
            detalle['ItemDescRecMonto'] = (
                linea.quantity * linea.price_unit - linea.price_subtotal
            )
            detalle['ItemDescRecBase'] = linea.quantity * linea.price_unit

            detalles.append(detalle)

        super().agregarDetail('DETALLES', detalles)

        # -----------------------------------------------
        # Base generación de FUD Referencia
        # ----------------------------------------------
        referencias = []
        referencia = {}
        count = 0
        for linea in invoice_fud.bcn_reference_ids:
            count += 1

            referencia['ReferenciaNroDoc'] = linea.origin_doc_number
            referencia['ReferenciaFechaDoc'] = linea.date
            ReferenciaTipo=linea.referencia_tipo
            referencia['ReferenciaTipo'] = ReferenciaTipo
            if ReferenciaTipo=='':
                
                ReferenciaTipoDoc=linea.bcn_reference_doc_type_id.code
                referencia['ReferenciaTipoDoc'] = ReferenciaTipoDoc
            elif ReferenciaTipo=='Afectacion':
            
                ReferenciaAfectacionConcepto=6
                referencia['ReferenciaAfectacionConcepto'] = ReferenciaAfectacionConcepto
           
                    
            
            referencias.append(referencia)

        super().agregarDetail('REFERENCIA', referencias)

        return


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
            return "DETALLE"
        elif seccion_id == 3:
            return "REFERENCIA"
        elif seccion_id == 4:
            return "DESCUENTOS O RECARGOS"
        elif seccion_id == 5:
            return "COMISIONES Y OTROS CARGOS"
        elif seccion_id == 6:
            return "SUBTOTALES INFORMATIVOS"
        else:
            return False

    #-----------------------------------------------        
    #  Base gerenación de FUD 
    #-----------------------------------------------
    def genera_fud(self, invoice_fud):

        #Obtiene Listado Encabezado y Procesa
        list_diccionariofud_encabezado  = self.env['bcn.dictionaryfud'].search_read([('tipo_doc', 'in', [str(invoice_fud.l10n_latam_document_type_id.code),'0']),('pais','=',str(invoice_fud.company_id.country_id.code)),('seccion','=','1'),('relacion_db','!=','')])
        #logging.info("ENCABEZADO: {}".format(' '.join(map(str, list_diccionariofud_encabezado))))
        
        fud_seccion_encabezado = self.valida_seccion_empty(1, invoice_fud, list_diccionariofud_encabezado)
        #Obtiene Listado Detalle y Procesa
        list_diccionariofud_detalle     = self.env['bcn.dictionaryfud'].search_read([('tipo_doc', 'in', [str(invoice_fud.l10n_latam_document_type_id.code),'0']),('pais','=',str(invoice_fud.company_id.country_id.code)),('seccion','=','2'),('relacion_db','!=','')])
        logging.info('list_diccionariofud_detalle')
        logging.info(list_diccionariofud_detalle)
        fud_seccion_detalle = self.valida_seccion_empty(2, invoice_fud, list_diccionariofud_detalle)
        
        #Obtiene Listado Referencia y Procesa
        list_diccionariofud_referencia  =self.env['bcn.dictionaryfud'].search_read([('tipo_doc', 'in', [str(invoice_fud.l10n_latam_document_type_id.code),'0']),('pais','=',str(invoice_fud.company_id.country_id.code)),('seccion','=','3'),('relacion_db','!=','')])
        logging.info('list_diccionariofud_referencia')
        logging.info(list_diccionariofud_referencia)
        fud_seccion_referencia = self.valida_seccion_empty(3, invoice_fud, list_diccionariofud_referencia)
        #Obtiene Listado Descuentos y Procesa
        list_diccionariofud_descuentos  = self.env['bcn.dictionaryfud'].search_read([('tipo_doc', 'in', [str(invoice_fud.l10n_latam_document_type_id.code),'0']),('pais','=',str(invoice_fud.company_id.country_id.code)),('seccion','=','4'),('relacion_db','!=','')])
        fud_seccion_descuentos = self.valida_seccion_empty(4, invoice_fud, list_diccionariofud_descuentos)
        #Obtiene Listado Comision y Procesa
        list_diccionariofud_comision    = self.env['bcn.dictionaryfud'].search_read([('tipo_doc', 'in', [str(invoice_fud.l10n_latam_document_type_id.code),'0']),('pais','=',str(invoice_fud.company_id.country_id.code)),('seccion','=','5'),('relacion_db','!=','')])
        fud_seccion_comision = self.valida_seccion_empty(5,invoice_fud,  list_diccionariofud_comision)
        #Obtiene Listado Subtotal y Procesa
        list_diccionariofud_subtotal    = self.env['bcn.dictionaryfud'].search_read([('tipo_doc', 'in', [str(invoice_fud.l10n_latam_document_type_id.code),'0']),('pais','=',str(invoice_fud.company_id.country_id.code)),('seccion','=','5'),('relacion_db','!=','')])
        fud_seccion_subtotal = self.valida_seccion_empty(6, invoice_fud, list_diccionariofud_subtotal)

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
        logging.info('nodo_base')
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
        '''
        for attr in dir(invoice_fud):
            if not attr.startswith("__"):
                value = getattr(invoice_fud, attr)
                logging.info(f"{attr}: {value}")  
        '''
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
    # Metodo Principal
    #-----------------------------------------------
    '''
    def main(self, invoice_fud):
        #Llamado Main proceso FUD
        formulario_documento = self.genera_fud(invoice_fud)
        #self.demo_test_hardcode(invoice_fud)
#        logging.info(str(formulario_documento))
        if formulario_documento:
            #Conexión con GETONE
            logging.info("DESCOMENTAR CUANDO ZAMUDIO LO INDIQUE\n")
            return self.call_getone(formulario_documento,invoice_fud)
    '''
        
    #-----------------------------------------------        
    # Demo Prueba Datos y Referencias
    #-----------------------------------------------
    def demo_test_hardcode(self, invoice_fud):


        fudtxt= "<ENCABEZADO>\n"
        fudtxt=fudtxt+"Monto Neto      | 11.0\n"
        fudtxt=fudtxt+"Folio      | 1311\n"
        fudtxt=fudtxt+"Fecha de Emision      | 2023-10-31\n"
        fudtxt=fudtxt+"Fecha Vencimiento      | 2023-10-24\n"
        fudtxt=fudtxt+"Direccion Origen      | Cerro el Plomo 5420\n"
        fudtxt=fudtxt+"Comuna Origen      | Las Condes\n"
        fudtxt=fudtxt+"Ciudad Origen      | Santiago\n"
        fudtxt=fudtxt+"Rut Receptor      | 79844530-8\n"
        fudtxt=fudtxt+"Razon Social Receptor      | PRONTOMATIC S.A.\n"
        fudtxt=fudtxt+"Giro Receptor      | Giro\n"
        fudtxt=fudtxt+"Direccion Receptor      | AV. FRANCISCO BILBAO 3028\n"
        fudtxt=fudtxt+"Comuna Receptor      | LAS CONDES\n"
        fudtxt=fudtxt+"Ciudad Receptor      | Metropolitana\n"
        fudtxt=fudtxt+"Forma de Pago      | 1\n"
        fudtxt=fudtxt+"Tasa IVA      | 19.0\n"
        fudtxt=fudtxt+"IVA      | 2\n"
        fudtxt=fudtxt+"Tipo DTE      | 33\n"
        fudtxt=fudtxt+"Monto Total      | 13\n"
        fudtxt=fudtxt+"<DETALLE>\n"
        fudtxt=fudtxt+"Nro.Linea |Descripcion Adicion al Item|Nombre del Item|Cantidad|Precio Unitario Item|Monto Item\n"
        fudtxt=fudtxt+"1|[Caja Proyecto] CCLA-Proyecto|CCLA-Proyecto|11.0|1|11.0"
        return fudtxt
        #logging.info("Detalle ENCABEZADO es: {}".format(' '.join(map(str, list_diccionariofud_encabezado))))
        #logging.info("Procesando ENCABEZADO "+str(type(list_diccionariofud_encabezado))+"\n")
        encabezado_tex = "CHILE<ENCABEZADO>\n"
        encabezado_tex = encabezado_tex + "Codigo PAIS | "+str(invoice_fud.company_id.country_id.code)+"\n"
        encabezado_tex = encabezado_tex + "Tipo DTE | "+str(invoice_fud.l10n_latam_document_type_id.code)+"\n"
        encabezado_tex = encabezado_tex + "PREFIJO + FOLIO | "+str(invoice_fud.name)+"\n"
        encabezado_tex = encabezado_tex + "Folio | "+str(invoice_fud.sequence_number)+"\n"
        encabezado_tex = encabezado_tex + "Direccion Origen | "+str(invoice_fud.company_id.street)+"\n"
        encabezado_tex = encabezado_tex + "Comuna Origen | "+str(invoice_fud.company_id.city)+"\n"
        encabezado_tex = encabezado_tex + "Ciudad Origen | "+str(invoice_fud.company_id.street2)+"\n"
        encabezado_tex = encabezado_tex + "Rut Receptor | "+str(invoice_fud.partner_id.vat)+"\n"
        encabezado_tex = encabezado_tex + "Razon social Receptor | "+str(invoice_fud.partner_id.name)+"\n"
        encabezado_tex = encabezado_tex + "Direccion Receptor | "+str(invoice_fud.partner_id.street)+"\n"
        encabezado_tex = encabezado_tex + "Comuna Receptor | "+str(invoice_fud.partner_id.city)+"\n"
        encabezado_tex = encabezado_tex + "Ciudad Receptor | "+str(invoice_fud.partner_id.state_id.name)+"\n"
        #encabezado_tex = encabezado_tex + "Giro Receptor | "+str(invoice_fud.partner_id.l10n_cl_activity_description)+"\n"
        encabezado_tex = encabezado_tex + "Giro Receptor | eJEMPLO GIRO\n"
        encabezado_tex = encabezado_tex + "Fecha de Emision | "+str(invoice_fud.invoice_date)+"\n"
        encabezado_tex = encabezado_tex + "Fecha Vencimiento | "+str(invoice_fud.invoice_date_due)+"\n"
        
        #encabezado_tex = encabezado_tex + "Forma de Pago | "+str(invoice_fud.x_studio_forma_pago)+"\n"
        encabezado_tex = encabezado_tex + "Monto Total | "+str(invoice_fud.amount_total)+"\n"
        encabezado_tex = encabezado_tex + "Monto Neto | "+str(invoice_fud.amount_untaxed)+"\n"
        encabezado_tex = encabezado_tex + "IVA | "+str(invoice_fud.amount_tax)+"\n"
        
        detalle_text = "<DETALLE>\n"
        detalle_text = detalle_text + "Nro.Linea|Tipo codigo|Codigo del Item|Nombre del Item|Descripcion Adicion al Item|Cantidad|Unidad de Medida|Precio Unitario Item|Monto Item \n"
        count = 0
        for record in invoice_fud.invoice_line_ids:
            count += 1
            detalle_text = detalle_text + str(count) +"| | |"+ str(record.product_id.name)+"|"+ str(record.product_id.name)+"|"+ str(record.quantity)+"| |"+ str(record.price_unit)+"|"+ str(record.price_subtotal)+"\n"

        referencia_text = "<REFERENCIA>\n"
        count = 0
        referencia_text = referencia_text + "Nro Linea Referencia|Folio Referencia|Tipo Documento Referencia|Fecha Referencia|Codigo Referencia|Razon Referencia \n"
        '''
        for record in invoice_fud.bcn_reference_ids:
            count += 1
            referencia_text = referencia_text + str(count) +"| | |"+ str(record.origin_doc_number)+"|"+ str(record.reference_doc_code)+"|"+ str(record.date)+"| |"+ str(record.l10n_cl_reference_doc_type_id.code)+"|"+ str(record.reason)+"\n"
        '''
        fud_text = encabezado_tex + detalle_text + referencia_text
        return fud_text
        