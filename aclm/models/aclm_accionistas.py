from odoo.exceptions import AccessError, UserError, ValidationError
import csv
from odoo.http import request
from odoo import models, fields, api, _
from reportlab.pdfgen import canvas
import tempfile
import base64
from io import StringIO
from datetime import datetime, timedelta
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

class AclmAccionistas(models.Model):

    _name = 'aclm.accionistas'
    _description = 'Generacion de Reportes Accionistas'


    @api.model
    def generar_accionistas_excel(self, *args, **kwargs):

        #listado accionistas
        data_full_accionitas = self.env['res.partner'].search([('x_studio_accionista', '=', 'Activo')], order='name')
       # Crea un archivo temporal y luego cierra, dejando una ruta válida para usar
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()

        workbook = xlsxwriter.Workbook(temp_file.name)
        worksheet = workbook.add_worksheet()

        # Encabezado
        worksheet.write('A1', 'N')
        worksheet.write('B1', 'R.U.T')
        worksheet.write('C1', 'Marco')
        worksheet.write('D1', 'ACCIONISTA')
        worksheet.write('E1', 'NOMBRE CONTACTO')
        worksheet.write('F1', 'TELEFONO')
        worksheet.write('G1', 'CORREO')
        worksheet.write('H1', 'ACCIONES')

        row = 1
        num = 1
        total_acciones = 0
        for data_excel in data_full_accionitas:
            valor_str = data_excel['x_studio_cantidad_1']
            valor_float = float(data_excel['x_studio_cantidad_1'].replace(',', '.')) if data_excel['x_studio_cantidad_1'] else 0.0
            total_acciones += valor_float

            worksheet.write(row, 0, str(num))
            worksheet.write(row, 1, str(data_excel['vat']))
            worksheet.write(row, 2, str(data_excel['x_studio_cod_de_marco']))
            worksheet.write(row, 3, str(data_excel['x_studio_holding']))
            worksheet.write(row, 4, str(data_excel['x_studio_nombre_contacto']) if data_excel['x_studio_nombre_contacto'] else '')
            worksheet.write(row, 5, str(data_excel['phone_sanitized']) if data_excel['phone_sanitized'] else '')
            worksheet.write(row, 6, str(data_excel['email_normalized']) if data_excel['email_normalized'] else '')
            
            worksheet.write(row, 7, float(data_excel['x_studio_cantidad_1'].replace(',', '.')) if data_excel['x_studio_cantidad_1'] else 0.0)
            row += 1
            num += 1
        
        row += 1
        worksheet.write(row, 6, 'TOTAL DE ACCIONES:')
        worksheet.write(row, 7, total_acciones)

        workbook.close()

        # Lectura del archivo creado y su codificación a base64 para el attachment
        with open(temp_file.name, 'rb') as f:
            byte_data = base64.b64encode(f.read())

        # Eliminamos el archivo temporal después de leerlo
        os.unlink(temp_file.name)

        attachment = self.env['ir.attachment'].create({
            'name': 'listado_oficial_asociacion_canal_las_mercedes.xlsx',
            'type': 'binary',
            'datas': byte_data,
            'res_model': self._name,
            'res_id': 100,
            })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{id}/{name}'.format(id=attachment.id, name=attachment.name),
            'target': 'new',
        }

    @api.model
    def generar_accionistas_pdf(self, *args, **kwargs):
        data_full_accionitas = self.env['res.partner'].search([('x_studio_accionista', '=', 'Activo')], order='name')
        #self.crear_pdf(data_full_accionitas)

        return true

    @api.model
    def crear_pdf(self, data_pdf):
        # Crea un archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()

        w, h = A4
        c = canvas.Canvas(temp_file.name, pagesize=A4)
        #print(data_pdf)  # Agrega esta línea para imprimir los datos y verificar su estructura

        for data in data_pdf:
            
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
            c.drawCentredString(w / 2, h - 80, "LISTADO OFICIAL DE LA ASOCIACION CANAL DE LAS MERCEDES")
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

            cuadro_x = 50
            cuadro_y = h - 160
            cuadro_width = w - 100
            cuadro_height = 30 
            c.rect(cuadro_x, cuadro_y, cuadro_width, cuadro_height, fill=False)
            
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
                

                for move in account_moves:
                    
                    
                    detalle_transaccion = move.name
                    via_transaccion = 'ACLM'#move.l10n_latam_document_type_id.name
                    monto_cargos = move.amount_total 
                                  
                    monto_depositos_cargos = move.payment_id.amount
                    paymen_id=move.payment_id
                     

                    saldo_adeudado += monto_cargos # Sumar el monto_cargos al saldo adeudado  
                    #saldo_adeudado -= monto_cargos
                    # Verificar si monto_cargos es negativo
                      # Asignar una cadena vacía
                    if monto_cargos < 0:
                        monto_cargos_formatted = ''  # Asignar una cadena vacía
                    else:
                        monto_cargos_formatted = "$ {:,.0f}".format(monto_cargos).replace(",", ".")
                                    
                  
                    monto_depositos_cargos_formatted = "$ {:,.0f}".format(monto_depositos_cargos).replace(",", ".")
                    saldo_adeudado_formatted = "$ {:,.0f}".format(saldo_adeudado).replace(",", ".")
                    
                    saldo_adeudado_suma = saldo_adeudado
                    saldo_adeudado_sum = "$ {:,.0f}".format(saldo_adeudado_suma).replace(",", ".")
                    ref=move.ref
                    tabla_y -= 20
                    
                        
                    #datos_tabla += sorted(datos_tabla[1:], key=lambda x: x[0])            
                    datos_tabla.append([
                        fecha_dia_form, detalle_transaccion, via_transaccion, monto_cargos_formatted, monto_depositos_cargos_formatted, saldo_adeudado_formatted
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
                
                tabla = Table(datos_tabla, colWidths=[60, 143, 75, 58, 90, 70])
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
                                    

           





        # Lectura del archivo creado y su codificación a base64 para el attachment
        with open(temp_file.name, 'rb') as f:
            byte_data = base64.b64encode(f.read())

        # Eliminamos el archivo temporal después de leerlo
        os.unlink(temp_file.name)

        attachment = self.env['ir.attachment'].create({
            'name': 'reporte.pdf',
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