# -*- coding: utf-8 -*-
from gc import enable
from odoo import http
from odoo.http import request, Response
import base64
import json
import io
from datetime import datetime
from io import StringIO
from odoo import models, fields, api, _
from reportlab.pdfgen import canvas
import tempfile
import base64
from io import StringIO
from datetime import datetime
import xlsxwriter
import os
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib import colors, styles
from reportlab.lib.styles import getSampleStyleSheet
from operator import itemgetter
import logging
from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError
from werkzeug.wrappers import Response


# Lib Config Logger
import logging 
logging.basicConfig(filename="/var/log/odoo/odoo-server.log", format='%(asctime)s %(message)s', filemode='w') 

class ACLM(http.Controller):
    logger = logging.getLogger()

    @http.route('/aclm/reporte', type='http', auth='none', methods=['GET','OPTIONS'], csrf=False, cors="*")
    def get_listado_reporte(self, **kw):
        tipo = kw.get('tipo')
        fecha_de = kw.get('fecha_de')
        fecha_a = kw.get('fecha_a')
        cod_de_marco = kw.get('cod_de_marco')
        accionistas = kw.get('accionistas')
        partner_id= kw.get('partner_id')
        
        auth = request.httprequest.headers.get('Authorization', None)
        if not auth:
            return http.Response('Credenciales no proporcionadas.', status=401)

        try:
            auth = base64.b64decode(auth.split(' ')[1]).decode('utf-8')
            username, password = auth.split(':')
        except (TypeError, ValueError):
            return http.Response('Credenciales no válidas.', status=401)

        db_name = 'ACLM-DEV01'
        if not db_name:
            return http.Response('Debe ingresar la DB.', status=401)
        else:
            request.session.db = db_name
            env = request.env
            uid = request.session.authenticate(request.db, username, password)

        if not uid:
            return http.Response('Credenciales inválidas.', status=401)

        company_id = request.env.user.company_id.id

        if not company_id:
            return http.Response('No es posible obtener la empresa del usuario.', status=401)

        if fecha_de and fecha_a:
            try:
                fecha_de_str = datetime.strptime(str(fecha_de), '%Y-%m-%d').date()
                fecha_a_str = datetime.strptime(str(fecha_a), '%Y-%m-%d').date()
            except ValueError:
                return http.Response('Las fechas proporcionadas no son válidas.', status=400)
            
            if fecha_de_str > fecha_a_str:
                return http.Response('La fecha hasta es mayor a la desde.', status=402)

        if tipo == 'reporte':
            if not cod_de_marco:
                return http.Response('Debe ingresar cod_de_marco.', status=401)

            report_pdf_base64 = self.generate_report_pdf(fecha_de, fecha_a, cod_de_marco)

            response_data = {
                'report_pdf_base64': report_pdf_base64
            }
            response_body = json.dumps(response_data).encode('utf-8')

            response = http.Response(
                response=response_body,
                status=200,
                headers={
                    'Content-Type': 'application/json',
                    'cors_enable': 'true',
                    'proxy_mode': 'true'
                }
            )
            return response
        elif tipo == 'usuarios':
            usuarios = self.generate_usuarios()
            if usuarios:
                return http.Response(usuarios, status=200, content_type='application/json')
            else:
                return http.Response(json.dumps([]), status=404, content_type='application/json')
            
        elif tipo == 'accionistas':
            if not cod_de_marco:
                return http.Response('Debe ingresar cod_de_marco.', status=401)
            accionistas = self.generate_accionistas(cod_de_marco)
            if accionistas:
                return http.Response(accionistas, status=200, content_type='application/json')
            else:
                return http.Response(json.dumps([]), status=404, content_type='application/json')
            
        elif tipo == 'pagos':
            if not partner_id:
                return http.Response('Debe ingresar partner_id.', status=401)
            
            pagos_pendientes = self.get_pagos_pendientes(partner_id)
            
            if pagos_pendientes:
                return http.Response(pagos_pendientes, status=200, content_type='application/json')
            else:
                return http.Response(json.dumps([]), status=404, content_type='application/json')
                    
        else:
            return http.Response('Tipo debe ser igual a reporte, usuarios, accionistas.', status=404)
         
    #def generate_usuario(self, cod_de_marco):
    #    filter_value = [('x_studio_cod_de_marco', '=', cod_de_marco), ('x_studio_accionista', '=', 'Activo')]
    #    accionistas = request.env['res.partner'].search_read(filter_value,['vat','display_name','commercial_partner_id'])
    #    accionista = accionistas[0]
    #    self.logger.info(accionista)
    #    response_data = {
    #            'usuario': accionista
    #    }
    #    response_body = json.dumps(response_data).encode('utf-8')
    #    return response_body
   

    # def generate_usuarios(self):
        # filter_value = [('is_company', '=', True), ('x_studio_accionista', '=', 'Activo')]
        # accionistas = request.env['res.partner'].search_read(filter_value, ['x_studio_cod_de_marco'])

        # codigos_marcos = [data['x_studio_cod_de_marco'] for data in accionistas if 'x_studio_cod_de_marco' in data]

        # response_data = {
            # 'usuarios': codigos_marcos
        # }
        # response_body = json.dumps(response_data).encode('utf-8')
        # return response_body
        
    #def generate_usuarios(self):
    #    filter_value = [('is_company', '=', True), ('x_studio_accionista', '=', 'Activo')]
    #    accionistas = request.env['res.partner'].search_read(filter_value, ['vat'])
    #
    #    rut = [data['vat'] for data in accionistas if 'vat' in data]
    #
    #    response_data = {
    #        'usuarios': rut
    #    }
    #    response_body = json.dumps(response_data).encode('utf-8')
    #    return response_body
    #
    #
    #def generate_accionistas(self, cod_de_marco):
    #    filter_value = [('x_studio_cod_de_marco', '=', cod_de_marco), ('x_studio_accionista', '=', 'Activo')]
    #    accionistas = request.env['res.partner'].search_read(filter_value, ['x_studio_holding'])
    #    
    #    if accionistas:
    #        x_studio_holding = accionistas[0]['x_studio_holding']  # Obtener el valor de vat del primer registro encontrado
    #        filter_value = [('x_studio_holding', '=', x_studio_holding), ('x_studio_accionista', '=', 'Activo')]
    #        accionistas = request.env['res.partner'].search_read(filter_value, ['id','x_studio_cod_de_marco','vat', 'x_studio_holding',  'x_studio_cantidad_1'])
    #
    #        response_data = {
    #            'accionistas': accionistas
    #        }
    #        response_body = json.dumps(response_data).encode('utf-8')
    #        return response_body

    def generate_usuarios(self):
        filter_value = [('is_company', '=', True), ('x_studio_accionista', '=', 'Activo')]
        accionistas = request.env['res.partner'].search_read(filter_value, ['vat'])

        rut = [data['vat'] for data in accionistas if 'vat' in data]

        response_data = {
            'usuarios': rut
        }
        response_body = json.dumps(response_data).encode('utf-8')
        return response_body
    

    def generate_accionistas(self, cod_de_marco):
        filter_value = [('vat', '=', cod_de_marco), ('x_studio_accionista', '=', 'Activo')]
        accionistas = request.env['res.partner'].search_read(filter_value, ['x_studio_holding'])
        
        if accionistas:
            x_studio_holding = accionistas[0]['x_studio_holding']  # Obtener el valor de vat del primer registro encontrado
            filter_value = [('x_studio_holding', '=', x_studio_holding), ('x_studio_accionista', '=', 'Activo')]
            accionistas = request.env['res.partner'].search_read(filter_value, ['id','x_studio_cod_de_marco','vat', 'x_studio_holding',  'x_studio_cantidad_1'])

        response_data = {
            'accionistas': accionistas
        }
        response_body = json.dumps(response_data).encode('utf-8')
        return response_body
        
    def get_pagos_pendientes(self, partner_id):
        logging.info("partner_id: %s", partner_id)
        partner_id_int = int(partner_id)  # Convertir a entero
        order = 'date ASC, l10n_latam_document_type_id DESC'  # Orden ascendente por fecha e ID de documento
        filter_value = [('partner_id', '=', partner_id_int), ('payment_state', '=', 'not_paid'), ('payment_id', '=', False)]


        pagos = request.env['account.move'].search_read(filter_value, ['id','name', 'amount_total', 'l10n_latam_document_type_id', 'invoice_date_due'],order = order)
        logging.info("pagos: %s", pagos)
        pagos_pend = [{'id': data['id'],'name': data['name'], 'amount_total': data['amount_total'], 'l10n_latam_document_type_id': data['l10n_latam_document_type_id'][1] if data['l10n_latam_document_type_id'] else '', 'invoice_date_due': data['invoice_date_due'].strftime('%Y-%m-%d') if data['invoice_date_due'] else ''} for data in pagos if 'name' in data]

        response_data = {
            'pagos_pendientes': pagos_pend
        }
        response_body = json.dumps(response_data).encode('utf-8')
        return response_body

    def generate_report_pdf(self, fecha_de, fecha_a,cod_de_marco):
        buffer = io.BytesIO()
      
        w, h = A4
        #c = canvas.Canvas(temp_file.name, pagesize=A4)
        c = canvas.Canvas(buffer)
        logo_path1 = "/usr/lib/python3.10/site-packages/odoo/addons_custom/aclm/models/logo2.png"
        img1 = ImageReader(logo_path1)
        img1_w, img1_h = img1.getSize()
        x1 = 10
        y1 = h - img1_h - 10
        c.drawImage(img1, x1, y1, width=img1_w, height=img1_h)

        logo_path2 = "/usr/lib/python3.10/site-packages/odoo/addons_custom/aclm/models/logo.png"
        img2 = ImageReader(logo_path2)
        img2_w, img2_h = img2.getSize()
        x2 = w - img2_w - 10
        y2 = h - img2_h - 10
        c.drawImage(img2, x2, y2, width=img2_w, height=img2_h)

        c.setFillColorRGB(128, 128, 128)
        c.rect(50, h - 90, w - 100, 30, fill=True)

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 16)
        c.drawCentredString(w / 2, h - 80, "ESTADO DE CUENTA")
        cuadro_x = 50
        cuadro_y = h - 180
        cuadro_width = w - 100
        cuadro_height = 120  # Adjusted height to accommodate the table
        c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)


        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 9)
            
        cuadro_x = 50
        cuadro_y = h - 140
        cuadro_width = w - 100
        cuadro_height = 30  # Adjusted height to accommodate the table
        c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)
        #cod_de_marco = int(cod_de_marco)
        filter_value = [ ('is_company', '=', True), ('x_studio_cod_de_marco','=',cod_de_marco)]
        accionista = request.env['res.partner'].search_read(filter_value, ['id','x_studio_holding','x_studio_cod_de_marco','x_studio_cantidad_1'])
        logging.info("Data: %s", accionista)
        for data in accionista:
           
            nombre_usuario = data.get('x_studio_holding', '')
            nombre_x = w / 10  # Posición predeterminada en la columna izquierda

            if len(nombre_usuario) > 40:  # Si el nombre es demasiado largo
                nombre_x = w / 2.8  # Mover a la columna derecha

            c.drawString(nombre_x, h - 103, f"Nombre Accionista: {nombre_usuario}")

            codigo_marco = data.get('x_studio_cod_de_marco', '')
            c.drawCentredString(w / 5.4, h - 123, f"Codigo marco: {codigo_marco}")

            cantidad_acciones = data.get('x_studio_cantidad_1', '')
            c.drawCentredString(w / 1.3, h - 123, f"Acciones: {cantidad_acciones}")

            cuadro_x = 50
            cuadro_y = h - 160
            cuadro_width = w - 100
            cuadro_height = 30 
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)

            asistente = data.get('asistente', 'Lorena Contreras Viedma.')
            c.drawCentredString(w / 4.5, h - 150, f"Asistente: {asistente}")
            
            telefono = data.get('', '+56 985660462')
            c.drawCentredString(w / 2, h - 150, f"Tel: {telefono}")
            email = data.get('email', 'contacto@canaldelasmercedes.cl')
            c.drawCentredString(w / 1.3, h - 150, f"Correo: {email}")

            
            fecha_inicio_de_str = datetime.strptime(fecha_de, "%Y-%m-%d").date()
            fecha_inicio_de_str_form = fecha_inicio_de_str.strftime("%d-%m-%Y")            
            c.drawCentredString(w / 6.1, h - 170, f"Desde: {fecha_inicio_de_str_form}")

            
            fecha_inicio_a_str = datetime.strptime(fecha_a, "%Y-%m-%d").date()
            fecha_inicio_a_str_form = fecha_inicio_a_str.strftime("%d-%m-%Y")
            c.drawCentredString(w / 1.3, h - 170, f"Hasta: {fecha_inicio_a_str_form}")

            partner_id = data.get('id', '')
           
        
        
        saldo_adeudado_old=0 
        monto_cargos_old=0
        monto_depositos_cargos_old=0   
        order = 'date ASC, l10n_latam_document_type_id DESC'  # Orden ascendente por fecha e ID de documento

        filter_value = [('date', '<', fecha_de),  ('partner_id', '=', partner_id)]

        account_moves_old = request.env['account.move'].search_read(filter_value, ['date','name','amount_total','payment_id','amount_total_in_currency_signed'], order=order)
        for moves in account_moves_old:
                
            monto_cargos_old = moves.get('amount_total', '') 
            
            id_old =moves.get('id', '')
            payment_id_old = moves.get('payment_id', '')
             
            if payment_id_old !='null' and id_old:
                pagos_old = request.env['account.payment'].search([('move_id', '=', id_old)])
                if pagos_old:
                    monto_depositos_cargos_old = pagos_old.amount
                    logging.info("monto_depositos_cargos_old---: %s", monto_depositos_cargos_old)
                    monto_cargos_old =-monto_depositos_cargos_old                  
            
            saldo_adeudado_old += monto_cargos_old # Sumar el monto_cargos al saldo adeudado
            

        order = 'date ASC, l10n_latam_document_type_id DESC'  # Orden ascendente por fecha e ID de documento

        filter_value = [('date', '>=', fecha_de), ('date', '<=', fecha_a), ('partner_id', '=', partner_id)]

        account_moves = request.env['account.move'].search_read(filter_value, ['date','name','amount_total','payment_id','amount_total_in_currency_signed'], order=order)
       
        logging.info("Data: %s", account_moves)
        if account_moves:
            estilo_celda = getSampleStyleSheet()['BodyText']
            estilo_celda.fontName = 'Helvetica'
            estilo_celda.fontSize = 8

            tabla_width = w - 100
            tabla_height = h - 140
            tabla_x = 50
            datos_tabla = [
                ['Fecha día/mes', 'Detalle Transacción', 'Vía de Transacción', 'Monto Cargos', 'Monto depositos cargos', 'Saldo adeudado']
            ]
                
            tabla_y = 750
            num_registros = len(account_moves)
            if num_registros >= 0 and num_registros <=5:
                tabla_y = 655
                        
            if num_registros >= 5 and num_registros <=10:
                tabla_y = 670                      
                    
            elif num_registros >10 and num_registros <=20 :
                tabla_y = 700

            elif num_registros >20 and num_registros <=25 :
                tabla_y = 730   
                
            elif num_registros>25 and num_registros <=30:
                tabla_y = 765

            elif num_registros>30 and num_registros <=35:
                tabla_y = 780
                
                

            elif num_registros>35:
                raise ValidationError(f"En este rango de fechas existen {num_registros} registros para uno de los Accionistas, por favor acota tu búsqueda, el reporte solo se genera con maximo 35 registros")
                
             
                
            saldo_adeudado=0
            saldo_adeudado= saldo_adeudado_old
            monto_depositos_cargos=0
            for move in account_moves:
                    
                    
                    
                # Obtener los datos correspondientes de cada movimiento y agregarlos a la tabla
                fecha_dia = move.get('date', '') 
                fecha_dia_form = fecha_dia.strftime("%d-%m-%Y")                    
                
                fecha_vencimiento = move.invoice_date_due
                fecha_vencimiento_form = fecha_vencimiento.strftime("%d-%m-%Y")
                
                detalle_transaccion = move.get('name', '') 
                detalle_transaccion = detalle_transaccion.replace(codigo_marco, "").strip()              
                via_transaccion = 'ACLM'                
                monto_cargos = move.get('amount_total', '')                 
                
                id = move.get('id', '')
                payment_id = move.get('payment_id', '')
                
                if payment_id !='null' and id:
                    
               
                    pagos = request.env['account.payment'].search([('move_id', '=', id)])
                    if pagos:
                        monto_depositos_cargos = pagos.amount
                        detalle_transaccion = 'Pago'
                        monto_cargos =-monto_depositos_cargos
                    else: 
                        monto_depositos_cargos=0
                                                
                        

                saldo_adeudado += monto_cargos # Sumar el monto_cargos al saldo adeudado  

                    # Verificar si monto_cargos es negativo
                      # Asignar una cadena vacía
                if monto_cargos < 0:
                    monto_cargos_formatted = ''  # Asignar una cadena vacía
                else:
                    monto_cargos_formatted = "$ {:,.0f}".format(monto_cargos).replace(",", ".")
                                    
                  
                monto_depositos_cargos_formatted = "$ {:,.0f}".format(monto_depositos_cargos).replace(",", ".")
                saldo_adeudado_formatted = "$ {:,.0f}".format(saldo_adeudado).replace(",", ".")

                   
                    
                     
                    
                    
                #saldo_adeudado_list = [move.get('amount_total_in_currency_signed') for move in account_moves]
                saldo_adeudado_suma = saldo_adeudado
                saldo_adeudado_sum = "$ {:,.0f}".format(saldo_adeudado_suma).replace(",", ".")
                #ref=move.ref
                tabla_y -= 20
                    
                        
                    #datos_tabla += sorted(datos_tabla[1:], key=lambda x: x[0])            
                datos_tabla.append([
                    fecha_dia_form, detalle_transaccion,fecha_vencimiento_form, via_transaccion, monto_cargos_formatted, monto_depositos_cargos_formatted, saldo_adeudado_formatted
                    ])

            c.setFont("Helvetica-Bold", 9)
            saldo = data.get('', f"Saldo a pagar hasta {fecha_inicio_a_str}: ")
            c.drawCentredString(w / 1.37, tabla_y - 25, f" {saldo} {saldo_adeudado_sum}")
            c.setFont("Helvetica", 9)

                    # Dibujar las notas
            c.setFont("Helvetica-Bold", 9)
            Nota1 = data.get('', 'Nota: Estimado Accionista, de existir alguna observación con su estado de cuenta')
            c.drawCentredString(w / 1.6, tabla_y - 45, f" {Nota1}")
            Nota2 = data.get('', 'contactar al asistente indicado en el encabezado del presente.')
            c.drawCentredString(w / 1.67,  tabla_y - 55, f" {Nota2}")
            c.setFont("Helvetica", 9)
                    
                # Ordenar la lista de datos_tabla por la columna 'Fecha día/mes' (fecha_dia_form)
                
            tabla = Table(datos_tabla, colWidths=[60, 80, 70, 75, 58, 70, 70])
            tabla.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(180/255, 210/255, 255/255 )),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONT', (0, 0), (-1, -1), estilo_celda.fontName, estilo_celda.fontSize)
                ]))

            tabla.wrapOn(c, tabla_width, tabla_height)
            tabla.drawOn(c, tabla_x, tabla_y)
                        

                
               
        else:
            Sin_Datos = data.get('', 'Sin Registros para el Reporte')
            c.drawCentredString(w / 2, h - 400, f" {Sin_Datos}")        

            
        c.showPage()
        c.save()
        pdf_bytes = buffer.getvalue()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        return pdf_base64
    
    """     
    Se pasa la logica a pagos.py
    @http.route('/aclm/pagos', type='http', auth='none', methods=['POST','OPTIONS'], csrf=False,cors="*")
    def post_registra_pagos(self, cod_de_marco=None, lista_pagos=None, **kw):

        if request.httprequest.data:
            json_data       = json.loads(request.httprequest.get_data(as_text=True))
            cod_de_marco    = json_data.get('cod_de_marco', cod_de_marco)
            lista_pagos     = json_data.get('lista_pagos', lista_pagos)
        

        auth = request.httprequest.headers.get('Authorization', None)
        if not auth:
            return http.Response('Credenciales no proporcionadas.', status=401)

        try:
            auth = base64.b64decode(auth.split(' ')[1]).decode('utf-8')
            username, password = auth.split(':')
        except (TypeError, ValueError):
            return http.Response('Credenciales no válidas.', status=401)
     
        if not cod_de_marco:
            response = {
                    'status_code': 409,
                    'message': "Debe ingresar Codigo de Marco.",
                }
            return Response(json.dumps(response), status=409, mimetype='application/json')
            #return http.Response('Debe ingresar Codigo de Marco.', status=401)
        
        if isinstance(lista_pagos, str):  # if lista_pagos is a string, convert it to a list of dictionaries
            lista_pagos = json.loads(lista_pagos)

        if not lista_pagos:
            response = {
                    'status_code': 409,
                    'message': "Debe ingresar el listado de pagos.",
                }
            return Response(json.dumps(response), status=409, mimetype='application/json')
            #return http.Response('Debe ingresar el listado de pagos.', status=401)

        db_name = 'ACLM-DEV01'
        if not db_name:
            return http.Response('Debe ingresar la DB.', status=401)
        else:
            request.session.db = db_name
            env = request.env
            uid = request.session.authenticate(request.db, username, password)

        if not uid:
            response = {
                    'status_code': 409,
                    'message': "Credenciales inválidas.",
                }
            return Response(json.dumps(response), status=409, mimetype='application/json')
            #return http.Response('Credenciales inválidas.', status=401)

        company_id = request.env.user.company_id.id
        
        if not company_id:
            response = {
                    'status_code': 409,
                    'message': "No es posible obtener la empresa del usuario.",
                }
            return Response(json.dumps(response), status=409, mimetype='application/json')
            #return http.Response('No es posible obtener la empresa del usuario.', status=401)
    
        # Valida existencia de account moves
        AccountMove = request.env['account.move']
        AccountPayment = request.env['account.payment']

        for pago in lista_pagos:
            move_id = pago.get('id')
            monto_pago = pago.get('monto_pago')
            if not AccountMove.browse(move_id).exists():
                response = {
                    'status_code': 409,
                    'message': "El ID de pago: "+ str(move_id)+" no existe.",
                }
                return Response(json.dumps(response), status=409, mimetype='application/json')
                #return http.Response('El ID de pago %s no existe.' % move_id, status=401)
            else:
                account_move = AccountMove.browse(move_id)
                if cod_de_marco == account_move.partner_id.x_studio_cod_de_marco:
                    # Valida si es Cuota/Multa y no Pago
                    if account_move.move_type == 'out_invoice':

                        # Valida si el pago ya existe
                        existing_payments = AccountPayment.search([
                            ('move_id', '=', account_move.id),
                            ('amount', '=', monto_pago),
                            ('payment_id', '=', account_move.partner_id.id),
                        ])
                        if existing_payments:
                            response = {
                                'status_code': 409,
                                'message': "El pago "+ str(account_move.name) +" ya se ha registrado anteriormente.",
                            }
                            return Response(json.dumps(response), status=409, mimetype='application/json')

                        #Se validan pagos a monto cerrado, no abonos ni pre-pagos.
                        if account_move.amount_residual_signed != monto_pago:
                            response = {
                                'status_code': 409,
                                'message': "El monto a pagar es: "+ str(account_move.amount_residual_signed)+", se esta pagando "+str(monto_pago)+". El monto debe ser exacto",
                            }
                            return Response(json.dumps(response), status=409, mimetype='application/json')
                            #return http.Response("El monto a pagar es: "+ str(account_move.amount_residual_signed)+", se esta pagando "+str(monto_pago)+". El monto debe ser exacto", status=401)

                        # Si es borrador se publica el documento
                        if account_move.state == 'draft':
                            account_move.action_post()
                        
                        # Se crea y Registra el Pago en Modulo de Pagos
                        action = account_move.action_register_payment()
                        PaymentRegister = request.env['account.payment.register']
                        payment_register = PaymentRegister.with_context(action['context']).create({})
                        payment_register.write({
                            'amount': monto_pago,
                            'payment_date': fields.Date.today(),
                            'payment_method_line_id': 6 #METODO 6 WEB, METODO 3 MANUAL ACLM
                        })
                        payment_register.action_create_payments()
                else:
                    response = {
                                'status_code': 409,
                                'message': "El documento "+ str(move_id) +" no pertenece al codigo marco: "+ str(cod_de_marco) +" ",
                            }
                    return Response(json.dumps(response), status=409, mimetype='application/json')
                    #return http.Response("El documento "+ str(move_id) +" no pertenece al codigo marco: "+ str(cod_de_marco) +" ", status=401)

        response = http.Response(
            message ='Pagos validados.',
            status=200,
            headers={
                'Content-Type': 'application/json',
                'cors_enable': 'true',
                'proxy_mode': 'true'
            }
        )
        return response
        #response = {
        #    'status_code': 200,
        #    'message': 'Pagos validados.',
        #    'cors_enable': 'true',
        #    'proxy_mode': 'true'
        #}
        #return Response(json.dumps(response), status=200, mimetype='application/json')
   
    @http.route('/aclm/cuponera', type='http', auth='none', methods=['GET','OPTIONS'], csrf=False,cors="*")
    def get_ws_cuponera(self, **kw):
        #valida parametros envio
        status_code = 200
        message = 'Generando Cuponera'
        
        #valida parametros envio
        rut_accionista = kw.get('rut_accionista')
        if rut_accionista == None:    
            message = 'Codigo de marco es requerido.'
            status_code = 401

        #Valida autenticacion basic
        auth = request.httprequest.headers.get('Authorization', None)
        if not auth:
            message = 'Credenciales no proporcionadas.'
            status_code = 401

        #Extrae datos de authentificacion
        try:
            auth = base64.b64decode(auth.split(' ')[1]).decode('utf-8')
            username, password = auth.split(':')
        except (TypeError, ValueError):
            return http.Response('Credenciales no válidas.', status=401)

        db_name = 'ACLM-DEV01'
        if not db_name:
            return http.Response('Debe ingresar la DB.', status=401)
        else:
            request.session.db = db_name
            env = request.env
            uid = request.session.authenticate(request.db, username, password)      
        
        #busca accionista            
        accionista = self.generate_accionistas(rut_accionista) 
        my_json = json.loads(accionista.decode('unicode_escape'))
        cuponera = request.env['aclm.cuponera']
        respuesta = cuponera.generar_cuponera_general(my_json['accionistas'][0]['id'],"base64")
        #logging.info("CIR-respuesta->"+str(respuesta))

        report_pdf_base64=respuesta.decode('utf-8')
        
        response_data = {
            'report_pdf_base64': report_pdf_base64
        }

        response_body = json.dumps(response_data) 

        response = http.Response(
            response=response_body,
            status=status_code,
            headers={
                'Content-Type': 'application/json',
                'cors_enable': 'true',
                'proxy_mode': 'true'
            }
        )
        return response
        """



        #response = {
        #    'status_code': status_code,
        #    'message': message,
        #}
        #return Response(json.dumps(response), status=status_code, mimetype='application/json')
