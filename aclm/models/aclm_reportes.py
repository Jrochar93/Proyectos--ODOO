from odoo.exceptions import AccessError, UserError, ValidationError
import csv
from odoo.http import request
from odoo import models, fields, api, _
from reportlab.pdfgen import canvas
import tempfile
import base64
from io import StringIO
from datetime import datetime, timedelta,date
import re

import xlsxwriter
import os
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib import colors, styles
from reportlab.lib.styles import getSampleStyleSheet
from operator import itemgetter

import calendar

import sys

# Lib Config Logger
import logging
logging.basicConfig(filename="/var/log/odoo/odoo-server.log", format='%(asctime)s %(message)s', filemode='w')

class AclmReportes(models.Model):
    _name = 'aclm.reportes'
    _description = 'Generacion de Reportes'

    
    # Función que obtiene listado de Accionistas - Holding.
  

    

        

    # Campos del modelo
    #accionista_de = fields.Many2one('res.partner', string='Accionista de', domain=[('x_studio_accionista', '=', 'Activo')])
    accionista_de = fields.Many2one('res.partner', string='Accionista de', domain=[('x_studio_accionista', '=', 'Activo'),], order='name')
    accionista_a = fields.Many2one('res.partner', string='Accionista a', domain=[('x_studio_accionista', '=', 'Activo')], order='name')   
    fecha_inicio_de = fields.Date(string='Fecha Orden De', required=True)
    fecha_inicio_a = fields.Date(string='Fecha Orden A', required=True)   
    reporte_pdf = fields.Binary(string='Reporte PDF', readonly=True)
    nombre_reporte_pdf = fields.Char(string='Nombre Reporte PDF', readonly=True)

    @api.model
    def _get_users_between_params(self, accionista_de_id, accionista_a_id, tipo_req):
        if (not accionista_de_id and accionista_a_id) or (accionista_de_id and not accionista_a_id):
            raise ValidationError("Se deben especificar tanto el " + tipo_req + " desde como el " + tipo_req + " hasta.")

        accionista_de = self.env['res.partner'].browse(accionista_de_id) if accionista_de_id else None
        accionista_a = self.env['res.partner'].browse(accionista_a_id) if accionista_a_id else None
        

        if accionista_de and accionista_a and accionista_de_id and accionista_a_id:
            usuarios = self.env['res.partner'].search([
                ('name', '>=', accionista_de.name),
                ('name', '<=', accionista_a.name),
                ('x_studio_accionista', '=', 'Activo')
            ], order='name')
        else:
            usuarios = self.env['res.partner'].search([
                ('x_studio_accionista', '=', 'Activo')
            ], order='name')

        
        return usuarios
    
    @api.model
    def _get_users_by_rut(self, rut, tipo_req):
        if (not rut):
            raise ValidationError("Se deben especificar el rut " + tipo_req)

        filter_value = [ ('is_company', '=', True),('x_studio_accionista', '=', 'Activo'), ('vat','=',rut)]
        #accionistas = request.env['res.partner'].search_read(filter_value, ['id','vat','x_studio_holding','x_studio_cod_de_marco','x_studio_cantidad_1'], order='name')
        accionistas = request.env['res.partner'].search(filter_value, order='name')
        
        return accionistas
        
    
    @api.constrains('fecha_inicio_de')
    def check_fecha_inicio_de(self):
        if self.fecha_inicio_de > self.fecha_inicio_a:
            raise ValidationError("xxx La Fecha Orden De debe ser menor o igual a la Fecha Orden a.")

        
    @api.model
    def cambiar_formato_fecha(self, fecha_inicio_de, formato_salida='%d-%m-%Y'):
        #fecha_obj = datetime.strptime(fecha_inicio_a, '%Y-%m-%d').date()
        fecha_obj=fecha_inicio_de
        desde = fecha_obj.strftime(formato_salida)

        return desde
   
    
   
    @api.model
    def get_account_moves_and_lines(self, fecha_desde, fecha_hasta, partner_id):
        # Convierte las fechas a strings en el formato adecuado para Odoo
        fecha_desde_str = fecha_desde
        fecha_hasta_str = fecha_hasta

        # Crea el dominio para la búsqueda
        domain = [
            ('date', '>=', fecha_desde_str),
            ('date', '<=', fecha_hasta_str),
            ('partner_id', '=', partner_id)
        ]
        #order = 'invoice_date,invoice_date_due  ASC,  l10n_latam_document_type_id DESC'  # Orden ascendente por invoice_date_due
        order = 'date ASC, l10n_latam_document_type_id DESC'  # Orden descendente por invoice_date e invoice_date_due

        # Realiza la búsqueda en el modelo account.move
        account_moves = self.env['account.move'].search(domain, order=order)
        account_moves = sorted(account_moves, key=lambda move: (move.date, move.l10n_latam_document_type_id.sequence))
        return account_moves
    
    @api.model
    def get_account_moves_and_lines_old(self,  fecha_hasta, partner_id):
        # Convierte las fechas a strings en el formato adecuado para Odoo
        
        fecha_desde_str = fecha_hasta

        # Crea el dominio para la búsqueda
        domain = [            
            ('date', '<', fecha_desde_str),
            ('partner_id', '=', partner_id)
        ]
        #order = 'invoice_date,invoice_date_due  ASC,  l10n_latam_document_type_id DESC'  # Orden ascendente por invoice_date_due
        order = 'date ASC, l10n_latam_document_type_id DESC'  # Orden descendente por invoice_date e invoice_date_due

        # Realiza la búsqueda en el modelo account.move
        account_moves_old = self.env['account.move'].search(domain, order=order)
        account_moves_old = sorted(account_moves_old, key=lambda move: (move.date, move.l10n_latam_document_type_id.sequence))
        return account_moves_old

    @api.model
    def get_account_moves_and_lines_residual(self, fecha_desde, fecha_hasta, partner_id, limit = False ):

        # Crea el dominio para la búsqueda
        
        domain = [            
            ('date', '>=', fecha_desde),
            ('date', '<=', fecha_hasta),
            ('partner_id', '=', partner_id),
            '|',
            '&',  # Este es el operador AND, que agrupa las próximas dos condiciones
            ('amount_residual_signed', '>',0),
            ('move_type', '=', 'out_invoice'),
            '|',
            ('move_type', '=', 'out_refund'),
            ('move_type', '=', 'entry')
        ]

        order = 'date ASC, l10n_latam_document_type_id DESC'  # Orden descendente por invoice_date e invoice_date_due

        # Realiza la búsqueda en el modelo account.move
        
        if limit == True:
            account_moves_old = self.env['account.move'].search(domain, order=order)
        else: 
            account_moves_old = self.env['account.move'].search(domain, order=order, limit=1)
        account_moves_old = sorted(account_moves_old, key=lambda move: (move.date, move.l10n_latam_document_type_id.sequence))
        logging.info("get_account_moves_and_lines_residual hola: %s", account_moves_old)
        return account_moves_old
        
    @api.model
    def generate_data_from_period(self, datos_reportes, today = False):
        data_pdf = []  # Lista para almacenar los datos

        solicita=datos_reportes['solicita'];

        if(solicita=='base64'):
            usuarios = self._get_users_by_rut(datos_reportes['rut'],'accionista')
        else:        
            usuarios = self._get_users_between_params(datos_reportes['accionista_de'], datos_reportes['accionista_a'],'accionista')

        for usuario in usuarios:

            if today == True:
                hasta = datos_reportes['fecha_final']
                desde = datos_reportes['fecha_inicio']

                data = self.get_account_moves_and_lines_residual(desde, hasta, usuario.id )
                if data:
                    logging.info("Datos: %s",data)
                    date_string = data[0].date.strftime("%Y-%m-%d")

                    data_pdf.append({                    
                        'nombre_usuario': usuario.x_studio_holding,
                        'rut': usuario.vat,
                        'codigo_de': usuario.x_studio_cod_de_marco,                    
                        'fecha_inicio_de': date_string,
                        'fecha_inicio_a': hasta,
                        'cantidad_acciones': usuario.x_studio_cantidad_1, 
                        'partner_id':usuario.id,
                        'contacto': usuario.x_studio_nombre_contacto,
                        'telefono': usuario.phone,
                        'correo':usuario.email,               
                    })
            else:
                desde = datos_reportes['fecha_inicio']
                hasta = datos_reportes['fecha_final']
                #data = self.get_account_moves_and_lines(desde, hasta, usuario.id )
                data_pdf.append({                    
                        'nombre_usuario': usuario.x_studio_holding,
                        'rut': usuario.vat,
                        'codigo_de': usuario.x_studio_cod_de_marco,                    
                        'fecha_inicio_de': desde,
                        'fecha_inicio_a': hasta,                  
                        'cantidad_acciones': usuario.x_studio_cantidad_1, 
                        'partner_id':usuario.id,
                        'contacto': usuario.x_studio_nombre_contacto,
                        'telefono': usuario.phone,
                        'correo':usuario.email,               
                })
            
            #logging.info("Datos: %s",data_pdf)
        return data_pdf
        

    @api.model
    def crear_pdf(self, data_pdf):
        byte_data = self.crear_pdf_base64(data_pdf);

        attachment = self.env['ir.attachment'].create({
            'name': 'Estado_de_cuenta.pdf',
            'type': 'binary',
            'datas': byte_data,
            'res_model': self._name,
            'res_id': self.id,
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{id}/{name}'.format(id=attachment.id, name=attachment.name),
            'target': 'new',
        }


    @api.model
    def crear_pdf_base64(self, data_pdf):
    
        # Crea un archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()

        w, h = A4
        c = canvas.Canvas(temp_file.name, pagesize=A4)
       
        #print(data_pdf)  # Agrega esta línea para imprimir los datos y verificar su estructura

        for data in data_pdf:
            
            logo_path1 = "/usr/lib/python3.10/site-packages/odoo/addons_custom/aclm/models/LogoCanal.png"
            img1 = ImageReader(logo_path1)
            img1_w, img1_h = img1.getSize()
            x1 = 40
            y1 = h - img1_h + 35
            c.drawImage(img1, x1, y1, width=180, height=50)

            #logo_path2 = "/usr/lib/python3.10/site-packages/odoo/addons_custom/aclm/models/logo2.png"
            #img2 = ImageReader(logo_path2)
            #img2_w, img2_h = img2.getSize()
            #x2 = w - img2_w - 5
            #y2 = h - img2_h - 5
            #c.drawImage(img2, x2, y2, width=img2_w, height=img2_h)
            #c.drawImage(img2, x2, y2, width=50, height=25)

            c.setFillColorRGB(128, 128, 128)
            c.rect(50, h - 80, w - 100, 30, fill=True)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 16)
            c.drawCentredString(w / 2, h - 70, "ESTADO DE CUENTA")
            cuadro_x = 50
            cuadro_y = h - 100
            cuadro_width = w - 100
            cuadro_height = 20  # Adjusted height to accommodate the table
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)


            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 9)
           

            nombre_usuario = data.get('nombre_usuario', '')
            rut = data.get('rut', '')
            telefono = data.get('telefono', '')
            correo = data.get('correo', '')
            contacto = data.get('contacto', '')
            nombre_x = w / 10  # Posición predeterminada en la columna izquierda
            
            #if len(nombre_usuario) > 40:  # Si el nombre es demasiado largo
            #    nombre_x = w / 2.8  # Mover a la columna derecha
            if len(nombre_usuario) > 50:
                nombre_usuario = nombre_usuario[:50]

            c.drawString(nombre_x, h - 93, f"Nombre Accionista: {nombre_usuario}")
            c.drawString(nombre_x + 375, h - 93, f"RUT: {rut}")
            
            if contacto:
                c.drawString(nombre_x, h - 113, f"Nombre Contacto: {contacto}")
            else:
                c.drawString(nombre_x, h - 113, f"Nombre Contacto: -")
           

            cuadro_x = 50
            cuadro_y = h - 120
            cuadro_width = w - 100
            cuadro_height = 20  # Adjusted height to accommodate the table
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)

            if telefono:
                c.drawString(nombre_x + 375, h - 133, f"Tel: {telefono}")
            else:
                c.drawString(nombre_x + 375, h - 133, f"Tel: -")
                
            if correo:
                c.drawString(nombre_x, h - 133, f"Correo: {correo}")
            else:
                c.drawString(nombre_x, h - 133, f"Correo: -")
           
            cuadro_x = 50
            cuadro_y = h - 140
            cuadro_width = w - 100
            cuadro_height = 20  # Adjusted height to accommodate the table
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)

            codigo_marco = data.get('codigo_de', '')
            c.drawCentredString(w / 5.4, h - 153, f"Código marco: {codigo_marco}")
            cantidad_acciones = data.get('cantidad_acciones', '')
            c.drawCentredString(w / 1.26, h - 153, f"Acciones: {cantidad_acciones}")

            cuadro_x = 50
            cuadro_y = h - 160
            cuadro_width = w - 100
            cuadro_height = 20  # Adjusted height to accommodate the table
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)

            asistente = data.get('asistente', 'Johanna Hidalgo Conejeros.')
            c.drawCentredString(w / 4.3, h - 173, f"Asistente: {asistente}")
            
            telefono = data.get('', '+56 985660462')
            c.drawCentredString(w / 2, h - 173, f"Tel: {telefono}")
            email = data.get('email', 'contacto@canaldelasmercedes.cl')
            c.drawCentredString(w / 1.3, h - 173, f"Correo: {email}")
            
            cuadro_x = 50
            cuadro_y = h - 180
            cuadro_width = w - 100
            cuadro_height = 20  # Adjusted height to accommodate the table
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)

            fecha_inicio_de = data.get('fecha_inicio_de', '')
            fecha_inicio_de_str = datetime.strptime(fecha_inicio_de, "%Y-%m-%d").date()
            fecha_inicio_de_str_form = fecha_inicio_de_str.strftime("%d-%m-%Y")            
            c.drawCentredString(w / 6.0 , h - 193, f"Desde: {fecha_inicio_de_str_form}")

            fecha_inicio_a = data.get('fecha_inicio_a', '')
            fecha_inicio_a_str = datetime.strptime(fecha_inicio_a, "%Y-%m-%d").date()
            fecha_inicio_a_str_form = fecha_inicio_a_str.strftime("%d-%m-%Y")
            c.drawCentredString(w / 1.26, h - 193, f"Hasta: {fecha_inicio_a_str_form}")
            
            cuadro_x = 50
            cuadro_y = h - 200
            cuadro_width = w - 100
            cuadro_height = 20  # Adjusted height to accommodate the table
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)

            partner_id = data.get('partner_id', '')
            fecha_inicio_de_str = None

            if fecha_inicio_de:
                fecha_inicio_de_str = datetime.strptime(fecha_inicio_de, "%Y-%m-%d").date()

            fecha_inicio_a_str = None

            if fecha_inicio_a:
                fecha_inicio_a_str = datetime.strptime(fecha_inicio_a, "%Y-%m-%d").date()
            
            saldo_adeudado_old=0 
            monto_cargos_old=0
            monto_depositos_cargos_old=0           
            
            account_moves_old = self.get_account_moves_and_lines_old(fecha_inicio_de_str, partner_id)
            logging.info('CLI account_moves_old')
            logging.info(account_moves_old)
            for moves in account_moves_old:
                
                monto_cargos_old = moves.amount_total                   
                monto_depositos_cargos_old = moves.payment_id.amount
               
                logging.info("monto_depositos_cargos_old: %s", monto_depositos_cargos_old)
                paymen_id=moves.payment_id
                if paymen_id:                  
                    
                    monto_cargos_old =-monto_depositos_cargos_old
                        

                saldo_adeudado_old += monto_cargos_old # Sumar el monto_cargos al saldo adeudado
                #saldo_adeudado_old-=  monto_depositos_cargos_old 
                logging.info("saldo_adeudado_old: %s", monto_depositos_cargos_old)
                        
                  
            
                   
            account_moves = self.get_account_moves_and_lines(fecha_inicio_de_str, fecha_inicio_a_str, partner_id)
            if account_moves:
                estilo_celda = getSampleStyleSheet()['BodyText']
                estilo_celda.fontName = 'Helvetica'
                estilo_celda.fontSize = 8

                tabla_width = 500
                tabla_height = h - 140
                tabla_x = 50
                datos_tabla = [
                    ['Fecha día/mes', 'Detalle Transacción', 'Vencimiento', 'Vía', 'Monto Cargos', 'Pagado', 'Saldo']
                ]
                
                tabla_y = 730
                num_registros = len(account_moves)
                if num_registros >= 0 and num_registros <=5:
                        tabla_y = 635
                        
                if num_registros >= 5 and num_registros <=10:
                        tabla_y = 645                      
                    
                elif num_registros >10 and num_registros <=15 :
                    tabla_y = 680

                elif num_registros >15 and num_registros <=20 :
                    tabla_y = 720

                elif num_registros >20 and num_registros <=23 :
                    tabla_y = 760

                elif num_registros >23 and num_registros <=25 :
                    tabla_y = 770   
                
                
                
                

                elif num_registros>25:
                   raise ValidationError(f"En este rango de fechas existen {num_registros} registros para uno de los Accionistas, por favor acota tu búsqueda, el reporte solo se genera con maximo 25 registros")
                    
                saldo_adeudado=0
                saldo_adeudado= saldo_adeudado_old
                
                for move in account_moves:
                    
                    
                    # Obtener los datos correspondientes de cada movimiento y agregarlos a la tabla

                    #Fecha dia/mes  
                    fecha_dia = move.date
                    fecha_dia_form = fecha_dia.strftime("%d-%m-%Y")

                    

                    logging.info('move')
                    logging.info(move)
                 
                    #Detalle Transaccion
                    detalle_transaccion = move.name
                    detalle_transaccion = detalle_transaccion.replace(codigo_marco, "").strip()
                    fecha_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', detalle_transaccion)
                    if fecha_match:
                        # Extraer los componentes de la fecha
                        año, mes, día = fecha_match.groups()
                        detalle_transaccion = f"{detalle_transaccion.split()[0]} {día}-{mes}-{año}"
                    
                    #Vencimiento
                    fecha_vencimiento = move.invoice_date_due
                    fecha_vencimiento_form = fecha_vencimiento.strftime("%d-%m-%Y")

                    tipo_trans=move.l10n_latam_document_type_id.id
                    logging.info(f'tipo_trans{tipo_trans}')
                    #logging.info("tipo_trans: %s", tipo_trans)
                    if tipo_trans== 67:
                        detalle_transaccion = '10% '

                    #Via
                    via_transaccion = 'ACLM'#move.l10n_latam_document_type_id.name

                    #Monto Cargos

                    monto_cargos = move.amount_total 
                    monto_adeudado = move.amount_residual_signed
                    paymen_id=move.payment_id
                    if move.move_type == 'entry':
                        logging.info("move.id")
                        logging.info(move.id)
                        logging.info("move.line_ids")
                        logging.info(move.line_ids)
                        logging.info("paymen_id.payment_id")
                        logging.info(move.payment_id)
                    saldo_a_favor = 0
                    if paymen_id:
                        monto_depositos_cargos = move.payment_id.amount
                        monto_cargos =-monto_depositos_cargos
                        via_transaccion = move.payment_id.payment_method_line_id.name
                        if move.ref != False:
                            ref = str(move.ref).replace(codigo_marco, "").strip()
                            #detalle_transaccion = 'Pago ' + '\n '+ str(ref)
                            detalle_transaccion = 'Pago aplicado'
                        else:
                            detalle_transaccion = 'Pago aplicado'
                            
                            for line_id in move.line_ids:
                                saldo_a_favor = line_id.amount_residual
                            monto_adeudado=saldo_a_favor
                            logging.info('monto_cargos')
                            logging.info(monto_cargos)
                            logging.info('saldo_a_favor')
                            logging.info(saldo_a_favor)
                            if(saldo_a_favor==0):
                                detalle_transaccion='Pago aplicado'
                            elif (saldo_a_favor==monto_cargos):
                                detalle_transaccion = 'Pago no aplicado'
                            else:
                                detalle_transaccion = 'Pago aplicado parcialmente'
                        
                    else:
                    
                        if(monto_adeudado>=0):
                            monto_depositos_cargos = monto_cargos-monto_adeudado
                            
                        else:
                            monto_depositos_cargos = monto_cargos+monto_adeudado
                            #saldo_adeudado+=monto_cargos+monto_adeudado
                            #saldo_ok= monto_cargos+monto_adeudado
                        #saldo_adeudado += monto_depositos_cargos
                   # Sumar el monto_cargos al saldo adeudado  
                    #saldo_adeudado -= monto_cargos
                    # Verificar si monto_cargos es negativo
                    # Asignar una cadena vacía
                    #Monto Cargos con Formato
                    if monto_cargos < 0:
                        monto_cargos_formatted = ''  # Asignar una cadena vacía
                    else:
                        if(move['move_type']=='out_refund'):
                            monto_cargos_formatted = "$ {:,.0f}".format(- monto_cargos).replace(",", ".")
                            #saldo_adeudado-=monto_cargos-monto_depositos_cargos
                        else:
                            monto_cargos_formatted = "$ {:,.0f}".format(monto_cargos).replace(",", ".")
                            #saldo_adeudado+=monto_cargos
                        
                    #saldo_adeudado =saldo_adeudado
                    if(paymen_id):
                        monto_depositos_cargos_formatted = "- $ {:,.0f}".format(monto_depositos_cargos).replace(",", ".")
                        monto_cargos_formatted = monto_depositos_cargos_formatted
                    else:    
                        monto_depositos_cargos_formatted = "-"

                    if tipo_trans ==63:
                        logging.info(f'Aquii{tipo_trans}')
                        saldo_adeudado -= monto_cargos
                    
                    else:
                        saldo_adeudado += monto_cargos
                    #saldo_adeudado += monto_cargos

                    #saldo_adeudado+=abs(-monto_cargos)
                  
                    saldo_adeudado_formatted = "$ {:,.0f}".format(saldo_adeudado).replace(",", ".")
                    monto_adeudado_formatted =  "$ {:,.0f}".format(monto_adeudado).replace(",", ".")
                    if move.x_studio_porcentmulta:
                        detalle_transaccion = detalle_transaccion + '\n' + " ("+move.x_studio_porcentmulta+") "
                    #saldo_adeudado_list = [move.amount_residual_signed for move in account_moves]
                    #saldo_adeudado_suma = sum(saldo_adeudado_list)
                    
                    saldo_adeudado_suma = saldo_adeudado
                    
                    saldo_adeudado_sum = "$ {:,.0f}".format(saldo_adeudado_suma).replace(",", ".")
                    ref=move.ref
                    tabla_y -= 23
                    
                    logging.info('monto_depositos_cargos')
                    logging.info(monto_depositos_cargos)
                    #datos_tabla += sorted(datos_tabla[1:], key=lambda x: x[0])            
                    datos_tabla.append([
                        fecha_dia_form, detalle_transaccion,fecha_vencimiento_form, via_transaccion, monto_cargos_formatted, monto_depositos_cargos_formatted, saldo_adeudado_formatted
                        ])
                c.setFont("Helvetica-Bold", 12)
                saldo = data.get('', f"Saldo a pagar hasta {fecha_inicio_a_str_form}: ")
                c.drawCentredString(w / 1.40, tabla_y - 25, f" {saldo} {saldo_adeudado_sum}")
                c.setFont("Helvetica", 12)

                    # Dibujar las notas
                #c.setFont("Helvetica-Bold", 9)
                #Nota1 = data.get('', 'Nota: Estimado Accionista, de existir alguna observación con su estado de cuenta contactar al asistente indicado en el encabezado del presente')
                #c.drawCentredString(w / 1.0, tabla_y - 45, f" {Nota1}")
                """Nota2 = data.get('', 'contactar al asistente indicado en el encabezado del presente.')
                c.drawCentredString(w / 1.67,  tabla_y - 55, f" {Nota2}")
                c.setFont("Helvetica", 9)"""
                    
                # Ordenar la lista de datos_tabla por la columna 'Fecha día/mes' (fecha_dia_form)
                
                
                tabla = Table(datos_tabla, colWidths=[63, 158, 50, 50, 56, 58, 60])
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

                # ... Previous code ...

                # Starting height for both sections
                h_banco = h- 720
                line_height = 20  # Adjust this value as needed

                # Banco de Chile
                c.setFont("Helvetica", 10)
                c.drawString(50, h_banco + 30, "Para su pago, efectúe transferencia a cualquiera de estos dos bancos:")
                rect_color = (180/255, 210/255, 255/255)
                c.setFillColor(rect_color)
                c.rect(50, h_banco, 238, line_height, fill=True)
                rect_color = (0, 0, 0)
                c.setFillColor(rect_color)
                c.drawString(75, h_banco + 5, "BANCO DE CHILE")  # Adjust the vertical position slightly

                # CUADRO PAGO BANCO CHILE
                c.setFont("Helvetica", 8)                
                c.drawString(50, h_banco - 15, f" NOMBRE:")                
                c.drawString(105, h_banco - 15, f"ASOCIACIÓN DEL CANAL DE LAS MERCEDES")

                c.drawString(50, h_banco - 25, f" BANCO:")               
                c.drawString(105, h_banco - 25, f"BANCO CHILE - EDWARDS")

                # Additional Information for Banco de Chile
                c.drawString(50, h_banco - 35, f" T. CUENTA:")
                c.drawString(105, h_banco - 35, f"CUENTA CORRIENTE")

                c.drawString(50, h_banco - 45, f" N° CUENTA:")
                c.drawString(105, h_banco - 45, f"01047-02")

                c.drawString(50, h_banco - 55, f" RUT:")
                c.drawString(105, h_banco - 55, f"70.059.900-0")

                c.drawString(50, h_banco - 65, f" CORREO:")
                c.drawString(105, h_banco - 65, f"contacto@canaldelasmercedes.cl")

                c.drawString(50, h_banco - 75, f" MOTIVO:")
                c.drawString(105, h_banco - 75, f"INDICAR CÓDIGO DE MARCO Y CUOTA")

                # ... Repeat the same pattern for the following rectangles and text ...

                # Banco Estado
                c.setFont("Helvetica", 10)
                rect_color = (180/255, 210/255, 255/255)
                c.setFillColor(rect_color)
                c.rect(310, h_banco, 238, line_height, fill=True)
                rect_color = (0, 0, 0)
                c.setFillColor(rect_color)
                c.drawString(335, h_banco + 5, "BANCO ESTADO")  # Adjust the vertical position slightly

                # CUADRO PAGO BANCO ESTADO
                c.setFont("Helvetica", 8)              
                c.drawString(310, h_banco - 15, f" NOMBRE:")       
                c.drawString(365, h_banco - 15, f"ASOCIACIÓN DEL CANAL DE LAS MERCEDES")

                c.drawString(310, h_banco - 25, f" BANCO:")              
                c.drawString(365, h_banco - 25, f"BANCO ESTADO")

                # Additional Information for Banco Estado
                c.drawString(310, h_banco - 35, f" T. CUENTA:")
                c.drawString(365, h_banco - 35, f"CUENTA CORRIENTE")

                c.drawString(310, h_banco - 45, f" N° CUENTA:")
                c.drawString(365, h_banco - 45, f"31000004998")

                c.drawString(310, h_banco - 55, f" RUT:")
                c.drawString(365, h_banco - 55, f"70.059.900-0")

                c.drawString(310, h_banco - 65, f" CORREO:")
                c.drawString(365, h_banco - 65, f"contacto@canaldelasmercedes.cl")

                c.drawString(310, h_banco - 75, f" MOTIVO:")
                c.drawString(365, h_banco - 75, f"INDICAR CÓDIGO DE MARCO Y CUOTA")

               
                c.drawString(50, h_banco - 100, f"Nota: Estimado Accionista, de existir alguna observación con su estado de cuenta contactar al asistente indicado en el encabezado del presente")

            
                        

                
               
            else:
                Sin_Datos = data.get('', 'Sin Registros para el Reporte')
                c.drawCentredString(w / 2, h - 400, f" {Sin_Datos}")
            c.showPage()

        c.save()
                                    

        # Lectura del archivo creado y su codificación a base64 para el attachment
        with open(temp_file.name, 'rb') as f:
            byte_data = base64.b64encode(f.read())

        

        # Eliminamos el archivo temporal después de leerlo
        os.unlink(temp_file.name)
        return byte_data;
        

    @api.model
    def generar_borrador(self, *args, **kwargs):
        accionista_de   = self.env.context.get('accionista_de')
        accionista_a    = self.env.context.get('accionista_a')
        fecha_inicio    = self.env.context.get('fecha_inicio_de')
        fecha_final    = self.env.context.get('fecha_inicio_a')

        reportes = {
            'accionista_de': accionista_de,
            'accionista_a': accionista_a,
            'fecha_inicio': fecha_inicio,
            'fecha_final': fecha_final,
            'solicita': 'erp'
        }

        return self.generar_borrador_general(reportes)

    @api.model
    def generar_borrador_general(self,reportes):

        solicita=reportes['solicita'];
        data_borrador = self.generate_data_from_period(reportes)

        if(solicita=='base64'):
            base64 = self.crear_pdf_base64(data_borrador)
            return base64
        else:
            return self.crear_pdf(data_borrador)

    @api.model
    def generar_saldo_abierto_general(self, reportes):
        solicita=reportes['solicita'];
        
        data_borrador = self.generate_data_from_period(reportes, True)

        if(solicita=='base64'):
            base64 = self.crear_pdf_today_base64(data_borrador)
            return base64
        else:
            return self.crear_pdf_today(data_borrador)


    @api.model
    def generar_saldo_abierto(self, *args, **kwargs):

        accionista_de   = self.env.context.get('accionista_de')
        accionista_a    = self.env.context.get('accionista_a')
        fecha_inicio    = self.env.context.get('fecha_inicio_de')
        fecha_final    = self.env.context.get('fecha_inicio_a')
        
        # Obteniendo la fecha de hoy
        today = date.today()
        # Formateando la fecha en el formato "yyyy-mm-dd"
        #fecha_final = today.strftime("%Y-%m-%d")


        reportes = {
            'accionista_de': accionista_de,
            'accionista_a': accionista_a,
            'fecha_inicio': fecha_inicio,
            'fecha_final': fecha_final,
            'solicita': 'erp'
        }
        return self.generar_saldo_abierto_general(reportes)
        """"
        data_borrador = self.generate_data_from_period(reportes, True)
        return self.crear_pdf_today(data_borrador)
        """

    @api.model
    def valida_pagos_no_conciliados(self, partner_id, move_id):
        pagos_obj = self.env['account.payment']
        pagos_conciliados = pagos_obj.search([
            ('is_reconciled', '=', False),
            ('partner_id', '=', partner_id),
            ('move_id', '=', move_id)

        ], limit=1)
        
        if not pagos_conciliados:
            return False
        
        return pagos_conciliados




    @api.model
    def crear_pdf_today (self, data_pdf):
        byte_data = self.crear_pdf_today_base64(data_pdf);
        
        attachment = self.env['ir.attachment'].create({
            'name': 'Estado_de_cuenta.pdf',
            'type': 'binary',
            'datas': byte_data,
            'res_model': self._name,
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{id}/{name}'.format(id=attachment.id, name=attachment.name),
            'target': 'new',
        }


    @api.model
    def crear_pdf_today_base64 (self, data_pdf):
               # Crea un archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()

        w, h = A4
        c = canvas.Canvas(temp_file.name, pagesize=A4)
       
        #print(data_pdf)  # Agrega esta línea para imprimir los datos y verificar su estructura

        for data in data_pdf:
            
            logo_path1 = "/usr/lib/python3.10/site-packages/odoo/addons_custom/aclm/models/LogoCanal.png"
            img1 = ImageReader(logo_path1)
            img1_w, img1_h = img1.getSize()
            x1 = 40
            y1 = h - img1_h + 43
            c.drawImage(img1, x1, y1, width=180, height=50)

            #logo_path2 = "/usr/lib/python3.10/site-packages/odoo/addons_custom/aclm/models/logo2.png"
            #img2 = ImageReader(logo_path2)
            #img2_w, img2_h = img2.getSize()
            #x2 = w - img2_w - 5
            #y2 = h - img2_h - 5
            #c.drawImage(img2, x2, y2, width=img2_w, height=img2_h)
            #c.drawImage(img2, x2, y2, width=50, height=25)

            c.setFillColorRGB(128, 128, 128)
            c.rect(50, h - 70, w - 100, 30, fill=True)

            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 16)
            c.drawCentredString(w / 2, h - 60, "ESTADO DE CUENTA - SALDOS ABIERTOS")
            cuadro_x = 50
            cuadro_y = h - 90
            cuadro_width = w - 100
            cuadro_height = 20  # Adjusted height to accommodate the table
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)


            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 9)
           

            nombre_usuario = data.get('nombre_usuario', '')
            rut = data.get('rut', '')
            telefono = data.get('telefono', '')
            correo = data.get('correo', '')
            contacto = data.get('contacto', '')
            nombre_x = w / 10  # Posición predeterminada en la columna izquierda
            
            if len(nombre_usuario) > 40:  # Si el nombre es demasiado largo
                nombre_x = w / 2.8  # Mover a la columna derecha

            c.drawString(nombre_x, h - 83, f"Nombre Accionista: {nombre_usuario}")
            c.drawString(nombre_x + 365, h - 83, f"RUT: {rut}")
            
            if contacto:
                c.drawString(nombre_x, h - 103, f"Nombre Contacto: {contacto}")
            else:
                c.drawString(nombre_x, h - 103, f"Nombre Contacto: -")
           

            cuadro_x = 50
            cuadro_y = h - 110
            cuadro_width = w - 100
            cuadro_height = 20  # Adjusted height to accommodate the table
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)

            if telefono:
                c.drawString(nombre_x, h - 123, f"Tel: {telefono}")
            else:
                c.drawString(nombre_x, h - 123, f"Tel: -")
            if correo:
                c.drawString(nombre_x + 205, h - 123, f"Correo: {correo}")
            else:
                c.drawString(nombre_x + 205, h - 123, f"Correo: -")
            cuadro_x = 50
            cuadro_y = h - 130
            cuadro_width = w - 100
            cuadro_height = 20  # Adjusted height to accommodate the table
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)

            codigo_marco = data.get('codigo_de', '')
            c.drawCentredString(w / 5.4, h - 143, f"Codigo marco: {codigo_marco}")
            cantidad_acciones = data.get('cantidad_acciones', '')
            c.drawCentredString(w / 1.44, h - 143, f"Acciones: {cantidad_acciones}")

            cuadro_x = 50
            cuadro_y = h - 150
            cuadro_width = w - 100
            cuadro_height = 20  # Adjusted height to accommodate the table
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)

            asistente = data.get('asistente', 'Johanna Hidalgo Conejeros.')
            c.drawCentredString(w / 4.5, h - 163, f"Asistente: {asistente}")
            
            telefono = data.get('', '+56 985660462')
            c.drawCentredString(w / 2, h - 163, f"Tel: {telefono}")
            email = data.get('email', 'contacto@canaldelasmercedes.cl')
            c.drawCentredString(w / 1.3, h - 163, f"Correo: {email}")
            
            cuadro_x = 50
            cuadro_y = h - 170
            cuadro_width = w - 100
            cuadro_height = 20  # Adjusted height to accommodate the table
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)

            fecha_inicio_de = data.get('fecha_inicio_de', '')
            fecha_inicio_de_str = datetime.strptime(fecha_inicio_de, "%Y-%m-%d").date()
            fecha_inicio_de_str_form = fecha_inicio_de_str.strftime("%d-%m-%Y")            
            c.drawCentredString(w / 6.1, h - 183, f"Desde: {fecha_inicio_de_str_form}")

            fecha_inicio_a = data.get('fecha_inicio_a', '')
            fecha_inicio_a_str = datetime.strptime(fecha_inicio_a, "%Y-%m-%d").date()
            fecha_inicio_a_str_form = fecha_inicio_a_str.strftime("%d-%m-%Y")
            c.drawCentredString(w / 1.3, h - 183, f"Hasta: {fecha_inicio_a_str_form}")
            
            cuadro_x = 50
            cuadro_y = h - 190
            cuadro_width = w - 100
            cuadro_height = 20  # Adjusted height to accommodate the table
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)

            partner_id = data.get('partner_id', '')
            fecha_inicio_de_str = None

            if fecha_inicio_de:
                fecha_inicio_de_str = datetime.strptime(fecha_inicio_de, "%Y-%m-%d").date()

            fecha_inicio_a_str = None

            if fecha_inicio_a:
                fecha_inicio_a_str = datetime.strptime(fecha_inicio_a, "%Y-%m-%d").date()
            
            account_moves = self.get_account_moves_and_lines_residual(fecha_inicio_de_str, fecha_inicio_a_str, partner_id, True)
            saldo_adeudado_sum=0
            if account_moves:
                logging.info('dentro del if account_moves') 
                logging.info("Data: %s", account_moves)
                estilo_celda = getSampleStyleSheet()['BodyText']
                estilo_celda.fontName = 'Helvetica'
                estilo_celda.fontSize = 8

                tabla_width = 500
                tabla_height = h - 120
                tabla_x = 50
                datos_tabla = [
                    ['Fecha día/mes', 'Detalle Transacción', 'Vencimiento', 'Vía', 'Monto Cargos', 'Saldo Abierto', 'Saldo adeudado']
                ]
                
                tabla_y = 750
                num_registros = len(account_moves)
                if num_registros >= 0 and num_registros <=5:
                        tabla_y = 635
                        
                if num_registros >= 5 and num_registros <=10:
                        tabla_y = 650                      
                    
                elif num_registros >10 and num_registros <=20 :
                    tabla_y = 780

                elif num_registros >20 and num_registros <=25 :
                    tabla_y = 710   
                
                elif num_registros>25 and num_registros <=30:
                    tabla_y = 745

                elif num_registros>30 and num_registros <=35:
                    tabla_y = 740
                
                

                elif num_registros>35:
                   raise ValidationError(f"En este rango de fechas existen {num_registros} registros para uno de los Accionistas, por favor acota tu búsqueda, el reporte solo se genera con maximo 35 registros")
                    
                saldo_adeudado=0
                
                for move in account_moves:
                   
                    # Obtener los datos correspondientes de cada movimiento y agregarlos a la tabla
                      
                    #Fecha dia/Mes
                    fecha_dia = move.date
                    fecha_dia_form = fecha_dia.strftime("%d-%m-%Y")
                    
                    #Vencimiento
                    fecha_vencimiento = move.invoice_date_due
                    fecha_vencimiento_form = fecha_vencimiento.strftime("%d-%m-%Y")

                    
                    monto_cargos = move.amount_total 
                    monto_adeudado = move.amount_residual
                    monto_depositos_cargos = move.amount_residual_signed

                    #Via transaccion
                    via_transaccion = move.payment_id.payment_method_line_id.name
                    
                    if via_transaccion == False:
                        via_transaccion = 'ACLM'#move.l10n_latam_document_type_id.name

                    
                    #saldo_adeudado -= monto_cargos
                    usuario_pago_conciliado = self.valida_pagos_no_conciliados(partner_id, move.id)
                    
                    if move.move_type == 'entry':
                        if  usuario_pago_conciliado:
                            monto_depositos_cargos_formatted = "- $ {:,.0f}".format(usuario_pago_conciliado.amount).replace(",", ".")
                            monto_depositos_cargos = '-'+str(monto_depositos_cargos_formatted)
                            saldo_adeudado_formatted = "$ {:,.0f}".format(saldo_adeudado).replace(",", ".")

                            if move.ref != False:
                                #ref = str(move.ref).replace(codigo_marco, "").strip()
                                #detalle_transaccion = 'Pago ' + '\n '+ str(ref)
                                detalle_transaccion = 'Pago no aplicado '
                                saldo_conciliado = 0
                                for line_id in move.line_ids:
                                    saldo_conciliado = line_id.amount_residual
                                logging.info("saldo_conciliado: "+ str(saldo_conciliado))
                                # Considerar que si tiene referencia el monto puede ser menor al amount del pago (puede quedar excedente de un pago)
                                monto_depositos_cargos_formatted = "$ {:,.0f}".format(saldo_conciliado).replace(",", ".")
                                if saldo_conciliado < 0:
                                    saldo_adeudado = saldo_adeudado + saldo_conciliado
                                else:
                                    saldo_adeudado = saldo_adeudado - saldo_conciliado

                                saldo_adeudado_formatted = "$ {:,.0f}".format(saldo_adeudado).replace(",", ".")

                            else:
                                saldo_conciliado = 0
                                for line_id in move.line_ids:
                                    saldo_conciliado = line_id.amount_residual
                                logging.info("saldo_conciliado: "+ str(saldo_conciliado))
                                
                                if saldo_conciliado < 0:
                                    saldo_adeudado = saldo_adeudado + saldo_conciliado
                                else:
                                    saldo_adeudado = saldo_adeudado - saldo_conciliado
                                # Considerar que si tiene referencia el monto puede ser menor al amount del pago (puede quedar excedente de un pago)
                                monto_depositos_cargos_formatted = " $ {:,.0f}".format(saldo_conciliado).replace(",", ".")
                                saldo_adeudado_formatted = "$ {:,.0f}".format(saldo_adeudado).replace(",", ".")
                                detalle_transaccion = 'Pago no aplicado'
                            
                        else:
                            continue
                    else:
                        saldo_adeudado += monto_depositos_cargos # Sumar el monto_cargos al saldo adeudado  
                        monto_depositos_cargos_formatted = "$ {:,.0f}".format(monto_depositos_cargos).replace(",", ".")
                        saldo_adeudado_formatted = "$ {:,.0f}".format(saldo_adeudado).replace(",", ".")
                        
                        detalle_transaccion = move.name
                        detalle_transaccion = detalle_transaccion.replace(codigo_marco, "").strip()
                        fecha_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', detalle_transaccion)
                        if fecha_match:
                            # Extraer los componentes de la fecha
                            año, mes, día = fecha_match.groups()
                            detalle_transaccion = f"{detalle_transaccion.split()[0]} {día}-{mes}-{año}"

                    if monto_cargos < 0:
                        monto_cargos_formatted = ''  # Asignar una cadena vacía
                    else:
                        if(move['move_type']=='out_refund' or move['move_type']=='entry'):
                            monto_cargos_formatted = "$ {:,.0f}".format(- monto_cargos).replace(",", ".")
                        else:
                            monto_cargos_formatted = "$ {:,.0f}".format(monto_cargos).replace(",", ".")
                        #monto_cargos_formatted = "$ {:,.0f}".format(monto_cargos).replace(",", ".")
                  
                    
                     
                    if move.x_studio_porcentmulta:
                        detalle_transaccion = detalle_transaccion + '\n' + " ("+move.x_studio_porcentmulta+") "
                    #saldo_adeudado_list = [move.amount_residual_signed for move in account_moves]
                    #saldo_adeudado_suma = sum(saldo_adeudado_list)
                    
                    saldo_adeudado_suma = saldo_adeudado
                    saldo_adeudado_sum = "$ {:,.0f}".format(saldo_adeudado_suma).replace(",", ".")
                    ref=move.ref
                    tabla_y -= 23
                    
                        
                    #datos_tabla += sorted(datos_tabla[1:], key=lambda x: x[0])            
                    datos_tabla.append([
                        fecha_dia_form, detalle_transaccion,fecha_vencimiento_form, via_transaccion, monto_cargos_formatted, monto_depositos_cargos_formatted, saldo_adeudado_formatted
                        ])
                
                c.setFont("Helvetica-Bold", 9)
                saldo = data.get('', f"Saldo a pagar hasta {fecha_inicio_a_str_form}: ")
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
                
                tabla = Table(datos_tabla, colWidths=[60, 120, 70, 55, 60, 60, 70])
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
                logging.info('dentro del else') 
                logging.info("sin datos que mostrar")
                Sin_Datos = data.get('', 'Sin Registros para el Reporte')
                c.drawCentredString(w / 2, h - 400, f" {Sin_Datos}")
            c.showPage()

        c.save()
                                    
        logging.info("Lectura del archivo creado y su codificación a base64 para el attachment")
        # Lectura del archivo creado y su codificación a base64 para el attachment
        with open(temp_file.name, 'rb') as f:
            byte_data = base64.b64encode(f.read())

        # Eliminamos el archivo temporal después de leerlo
        os.unlink(temp_file.name)
        return byte_data;
        