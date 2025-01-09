from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import models, fields, api, _
import tempfile
import sys

import base64
import os

from odoo.tools import config

# Librerias Reporte PDF
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib import colors, styles
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from operator import itemgetter
import json
import shutil
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo.http import request
import zipfile

# Lib Config Logger
import logging

logging.basicConfig(filename="/var/log/odoo/odoo-server.log", format='%(asctime)s %(message)s', filemode='w')


class AclmCuponera(models.Model):
    _name = 'aclm.cuponera'
    _description = 'Generacion de Cuponera'

    # Campos del modelo
    accionista_de = fields.Many2one('res.partner', string='Accionista de',
                                    domain=[('x_studio_accionista', '=', 'Activo')], order='name')
    tipo_cuponera = fields.Selection([
        ('codigo_marco', 'Cuponera por Código de Marco'),
        ('rut', 'Cuponera por Rut'),
        ('masiva', 'Cuponera masiva'),
    ], string='Tipo de Cuponera', required=True, default='codigo_marco')
    reporte_pdf = fields.Binary(string='Reporte PDF', readonly=True)
    nombre_reporte_pdf = fields.Char(string='Nombre Reporte PDF', readonly=True)

    @api.model
    def generar_cuponera(self, *args, **kwargs):
        tipo_cuponera = self.env.context.get('tipo_cuponera')
        logging.info("Tipo cuponera: {}".format(tipo_cuponera))
        accionista_de = self.env.context.get('accionista_de')

        if tipo_cuponera == 'codigo_marco':
            accionistas_ids = [accionista_de]
            return self.generar_cuponera_general(accionistas_ids)

        elif tipo_cuponera == 'rut':
            logging.info("RUT de accionistas_ids->" + str(accionista_de))
            accionista = self.env['res.partner'].browse(accionista_de) if accionista_de else None
            rut = accionista['vat']
            logging.info("RUT de accionista->" + str(rut))
            return self.generar_cuponera_rut(rut)

        elif tipo_cuponera == 'masiva':

            accionistas_id = self.env['res.partner'].search([('x_studio_accionista', '=', 'Activo')])

            cuponeras_folder = os.path.join(os.path.dirname(__file__), 'Cuponeras')

            # Eliminar la carpeta Cuponeras y su contenido
            if os.path.exists(cuponeras_folder):
                shutil.rmtree(cuponeras_folder)
                logging.info("Carpeta de Cuponeras Eliminada->" + str(cuponeras_folder))
            respuestas = []  # Lista para almacenar las respuestas de las cuponeras generadas
            ruts = set([])

            for accionista_m in accionistas_id:
                rut = accionista_m['vat']
                if not rut in ruts:
                    respuesta = self.generar_cuponera_masiva(rut)
                    ruts.add(rut)
                    respuestas.append(respuesta)
            cuponeras_folder = os.path.join(os.path.dirname(__file__), 'Cuponeras')
            if os.path.exists(cuponeras_folder):
                zip_result = self.generar_zip_cuponeras(cuponeras_folder)
                if zip_result:
                    return zip_result

                else:
                    # Manejar el caso si algo sale mal
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Error',
                            'message': 'No se pudo generar el archivo ZIP.',
                            'sticky': False,
                        }
                    }

            return respuestas

    def get_accionistas_rut(self, rut_accionista):
        filter_value = [('vat', '=', rut_accionista), ('x_studio_accionista', '=', 'Activo')]
        accionistas = self.env['res.partner'].search_read(filter_value, ['x_studio_holding'])

        if accionistas:
            x_studio_holding = accionistas[0][
                'x_studio_holding']  # Obtener el valor de vat del primer registro encontrado
            filter_value = [('x_studio_holding', '=', x_studio_holding), ('x_studio_accionista', '=', 'Activo')]
            accionistas = self.env['res.partner'].search_read(filter_value, ['id'])

        response_data = {
            'accionistas': accionistas
        }
        response_body = json.dumps(response_data).encode('utf-8')
        return response_body

    def get_accionistas_masivo(self, rut_accionista_m):
        filter_value = [('vat', '=', rut_accionista_m), ('x_studio_accionista', '=', 'Activo')]
        accionistas = self.env['res.partner'].search_read(filter_value, ['x_studio_holding'])

        if accionistas:
            x_studio_holding = accionistas[0][
                'x_studio_holding']  # Obtener el valor de vat del primer registro encontrado
            filter_value = [('x_studio_holding', '=', x_studio_holding), ('x_studio_accionista', '=', 'Activo')]
            accionistas = self.env['res.partner'].search_read(filter_value, ['id'])

        response_data = {
            'accionistas': accionistas
        }
        response_body = json.dumps(response_data).encode('utf-8')

        return response_body

    @api.model
    def generar_cuponera_rut(self, rut_accionista, salida=None):
        accionistas = self.get_accionistas_rut(rut_accionista)
        logging.info('accionistas')
        logging.info(accionistas)
        my_json = json.loads(accionistas.decode('unicode_escape'))
        accionistas_ids = [registro['id'] for registro in my_json['accionistas']]
        respuesta = self.generar_cuponera_general(accionistas_ids, salida)
        logging.info('accionistas_ids')
        logging.info(accionistas_ids)
        return respuesta

    @api.model
    def generar_cuponera_masiva(self, rut_accionista, salida='base64_pdf'):
        accionistas = self.get_accionistas_masivo(rut_accionista)

        logging.info(accionistas)
        my_json = json.loads(accionistas.decode('unicode_escape'))
        accionistas_id = [registro['id'] for registro in my_json['accionistas']]
        for accionistas_ids in accionistas_id:
            respuesta = self.generar_cuponera_general(accionistas_id, salida)

            logging.info('accionistas_ids')
            logging.info(accionistas_ids)

            return respuesta

    @api.model
    def generar_cuponera_general(self, accionistas_ids, salida=None):

        logging.info("CIR-accionistas_ids->" + str(accionistas_ids))
        logging.info("CIR-accionistas_ids->" + str(self))

        # Crea un archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()

        # Canvas Base
        canvas_cuponera = canvas.Canvas(temp_file.name, pagesize=A4)

        for accionista_id in accionistas_ids:
            canvas_cuponera = self._pdf_logo(canvas_cuponera)
            canvas_cuponera = self.crear_pdf_primera_pagina(canvas_cuponera, temp_file)
            canvas_cuponera = self.crear_pdf_contenido(canvas_cuponera, temp_file, accionista_id)

        if (salida == "base64"):
            return self.generar_pdf_cuponera_base64(temp_file, canvas_cuponera)
        elif (salida == "base64_pdf"):
            accionista = self.env['res.partner'].browse(accionista_id)
            rut_accionista = accionista.vat
            nombre_holding = accionista.x_studio_holding

            self.generar_pdf_cuponera_carpeta(temp_file, canvas_cuponera, rut_accionista, nombre_holding)


        else:
            return self.generar_pdf_cuponera(temp_file, canvas_cuponera)

    @api.model
    def _pdf_logo(self, canvas_cuponera):

        w, h = A4
        # Carga de Imagen
        logo_path1 = "/usr/lib/python3.10/site-packages/odoo/addons_custom/aclm/models/LogoCanal.png"
        img1 = ImageReader(logo_path1)
        img1_w, img1_h = img1.getSize()
        canvas_cuponera.drawImage(img1, 180, h - img1_h + 30, width=180, height=50)
        canvas_cuponera.setFillColorRGB(128, 128, 128)

        # Encabezado
        canvas_cuponera.setFillColorRGB(0, 0, 0)
        canvas_cuponera.setFont("Helvetica", 10)
        # Encabezado  bajada imagen
        canvas_cuponera.drawCentredString(w / 2, h - 75, "ASOCIACIÓN DEL CANAL DE LAS MERCEDES")
        # Encabezado  bajada imagen
        canvas_cuponera.drawCentredString(w / 2, h - 90, "UNION SAN JOSE PC 23, LOLENCO, COMUNA CURACAVI")
        return canvas_cuponera

    @api.model
    def get_nombre_mes(self, num_mes):
        meses = {
            '1': 'ENERO',
            '2': 'FEBRERO',
            '3': 'MARZO',
            '4': 'ABRIL',
            '5': 'MAYO',
            '6': 'JUNIO',
            '7': 'JULIO',
            '8': 'AGOSTO',
            '9': 'SEPTIEMBRE',
            '10': 'OCTUBRE',
            '11': 'NOVIEMBRE',
            '12': 'DICIEMBRE',
        }

        return meses[num_mes]

    @api.model
    def crear_pdf_contenido(self, c, temp_file, accionista_de):

        # Crea el dominio para la búsqueda
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('l10n_latam_document_type_id', 'in', [60, 62]),  # Busca que sea 60 o 62
            ('partner_id', '=', accionista_de)
        ]
        order = 'date ASC, l10n_latam_document_type_id ASC'

        # Realiza la búsqueda en el modelo account.move
        account_moves = self.env['account.move'].search(domain, order=order)
        # Obtiene el año actual
        current_year = datetime.now().year

        grouped_moves = {}
        for move in account_moves:

            logging.info("CUOTA: " + str(move.name))
            move_date = fields.Date.from_string(move.date)  # Convierte la fecha de string a objeto date
            # Crea la clave de "año-mes"
            year_month = f"{move_date.year}_{move_date.month:02d}"
            # Añade el objeto de movimiento de cuenta a la lista para este "año-mes"
            if year_month not in grouped_moves:
                grouped_moves[year_month] = []

            grouped_moves[year_month].append(move)

        count_cuotas = 1
        total_cuotas = len(grouped_moves)
        # Itera sobre los pares clave-valor en el diccionario
        for year_month, moves in grouped_moves.items():

            logging.info("Año y mes: " + year_month)
            # Datos de Usuario
            partner_name = str(moves[0].partner_id.name) if moves[0].partner_id.name else ''
            partner_vat = str(move[0].partner_id.vat) if moves[0].partner_id.vat else ''
            partner_email_normalized = str(moves[0].partner_id.email_normalized) if moves[
                0].partner_id.email_normalized else ''
            partner_x_studio_cod_de_marco = str(moves[0].partner_id.x_studio_cod_de_marco) if moves[
                0].partner_id.x_studio_cod_de_marco else ''
            partner_phone_sanitized = str(moves[0].partner_id.phone_sanitized) if moves[
                0].partner_id.phone_sanitized else ''
            partner_x_studio_cantidad_1 = str(moves[0].partner_id.x_studio_cantidad_1) if moves[
                0].partner_id.x_studio_cantidad_1 else ''

            # Datos de Tabla Cuotas
            move_date = moves[0].date if moves[0].date else ''

            # Añade un mes a la fecha actual
            next_month = move_date + relativedelta(months=1)
            two_next_month = move_date + relativedelta(months=2)

            # Diccionario MESES a texto
            # Mes Actual
            current_month = move_date.month
            mes_actual = self.get_nombre_mes(str(current_month))

            # Mes Siguiente
            last_day_of_next_month = next_month.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
            mes_siguiente = self.get_nombre_mes(str(last_day_of_next_month.month))

            # 2 Mes Siguiente
            last_day_of_next_month_after = two_next_month.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
            dos_mes_siguiente = self.get_nombre_mes(str(last_day_of_next_month_after.month))

            w, h = A4
            c.setFillColorRGB(0, 0, 0)
            c = self._pdf_logo(c)
            c = self.crear_pdf_encabezado(c, temp_file)

            c.setFont("Helvetica-Bold", 10)
            rect_color = (180 / 255, 210 / 255, 255 / 255)  # Color azul en formato RGB
            c.setFillColor(rect_color)
            c.rect(410, h - 125, 124, 14, fill=True)
            rect_color = (0, 0, 0)  # Color Negro en formato RGB
            c.setFillColor(rect_color)
            c.drawString(412, h - 120, f"CUPONERA N°{moves[0].partner_id.x_studio_cuponera_n}")

            rect_color = (180 / 255, 210 / 255, 255 / 255)  # Color azul en formato RGB
            c.setFillColor(rect_color)
            c.rect(410, h - 138, 124, 14, fill=True)
            rect_color = (0, 0, 0)  # Color Negro en formato RGB
            c.setFillColor(rect_color)
            c.drawString(432, h - 134, f"CUOTA {count_cuotas} de {total_cuotas}")

            # Imagen Base Contenido
            c.rect(70, h - 200, 450, 50, fill=False)
            # Carga de Imagen
            logo_path1 = "/usr/lib/python3.10/site-packages/odoo/addons_custom/aclm/models/LogoCanal.png"
            img1 = ImageReader(logo_path1)
            img1_w, img1_h = img1.getSize()
            c.drawImage(img1, 75, h - img1_h - 108, width=150, height=40)

            # Celda CUPONERA CUOTA
            c.setFont("Helvetica-Bold", 14)
            rect_color = (180 / 255, 210 / 255, 255 / 255)  # Color azul en formato RGB
            c.setFillColor(rect_color)
            c.rect(70, h - 230, 450, 30, fill=True)

            rect_color = (0, 0, 0)  # Color Negro en formato RGB
            c.setFillColor(rect_color)
            c.drawString(160, h - 222, f"CUPONERA CUOTA AÑO {current_year} - {current_year + 1}")
            c.setFont("Helvetica", 12)

            # DATOS ACCIONISTA
            c.setFont("Helvetica-Bold", 14)
            rect_color = (180 / 255, 210 / 255, 255 / 255)  # Color azul en formato RGB
            c.setFillColor(rect_color)
            c.rect(70, h - 260, 450, 20, fill=True)
            rect_color = (0, 0, 0)  # Color Negro en formato RGB
            c.setFillColor(rect_color)
            c.drawString(70, h - 255, f" DATOS ACCIONISTA")

            c.setFont("Helvetica", 8)
            c.rect(70, h - 280, 100, 20, fill=False)
            c.drawString(70, h - 275, f" NOMBRE")
            c.rect(170, h - 280, 350, 20, fill=False)
            c.drawString(175, h - 275, f"{partner_name}")

            c.rect(70, h - 300, 100, 20, fill=False)
            c.drawString(70, h - 295, f" TELÉFONO")
            c.rect(170, h - 300, 350, 20, fill=False)
            c.drawString(175, h - 295, f"{partner_phone_sanitized}")

            c.rect(70, h - 320, 100, 20, fill=False)
            c.drawString(70, h - 315, f" RUT")
            c.rect(170, h - 320, 350, 20, fill=False)
            c.drawString(175, h - 315, f"{partner_vat}")

            c.rect(70, h - 340, 100, 20, fill=False)
            c.drawString(70, h - 335, f" CORREO ELECTRONICO")
            c.rect(170, h - 340, 350, 20, fill=False)
            c.drawString(175, h - 335, f"{partner_email_normalized}")

            c.rect(70, h - 360, 100, 20, fill=False)
            c.drawString(70, h - 355, f" CODIGO MARCO")
            c.rect(170, h - 360, 350, 20, fill=False)
            c.drawString(175, h - 355, f"{partner_x_studio_cod_de_marco}")
            c.drawString(350, h - 355, f" ACCIONES")
            c.rect(350, h - 360, 170, 20, fill=False)
            c.drawString(470, h - 355, f"{partner_x_studio_cantidad_1}")

            # DATOS CONTACTO
            c.setFont("Helvetica-Bold", 14)
            rect_color = (180 / 255, 210 / 255, 255 / 255)  # Color azul en formato RGB
            c.setFillColor(rect_color)
            c.rect(70, h - 390, 450, 20, fill=True)

            rect_color = (0, 0, 0)  # Color Negro en formato RGB
            c.setFillColor(rect_color)
            c.drawString(75, h - 385, f"DATOS CONTACTO ACLM")
            c.setFont("Helvetica-Bold", 11)

            c.rect(70, h - 410, 100, 20, fill=False)
            c.drawString(70, h - 405, f" TELÉFONO")
            c.rect(170, h - 410, 350, 20, fill=False)
            c.drawString(175, h - 405, f"+56985660462")

            c.rect(70, h - 430, 100, 20, fill=False)
            c.drawString(70, h - 425, f" CORREO")
            c.rect(170, h - 430, 350, 20, fill=False)
            c.drawString(175, h - 425, f"contacto@canaldelasmercedes.cl")

            # Tabla Dinamica con Datos
            tabla_width = 500
            tabla_height = h - 440
            tabla_x = 70
            tabla_y = h - 480
            datos_tabla = [
                ['Fecha ', 'Detalle ', 'Vencimiento', 'Monto Cargos']
            ]
            move_amount_periodo = 0
            # Itera sobre los objetos move en la lista de moves
            for move in moves:
                move_name = str(move.name) if move.name else ''
                move_name = move_name.replace(partner_x_studio_cod_de_marco, "")
                move_due_date = move.invoice_date_due if move.invoice_date_due else ''
                move_amount = move.amount_total if move.amount_total else ''
                # Campo que lista todo los campos existentes en el objeto Account_move
                # logging.info("Campos: %s", move._fields)
                move_amount_periodo += move_amount

                estilo_celda = getSampleStyleSheet()['BodyText']
                # Formato D-M-Y
                # fecha_inicio_a_str_form = move_date.strftime("%d-%B-%Y")
                fecha_inicio_a_str_form = move_date.strftime("%d") + '-' + str(mes_actual) + '-' + str(current_year)
                # Formato D-M-Y
                # fecha_vencimiento_a_str_form = move_due_date.strftime("%d-%B-%Y")
                fecha_vencimiento_a_str_form = str(move_due_date.day) + '-' + str(mes_actual) + '-' + str(current_year)

                monto_depositos_formatted = "$ {:,.0f}".format(move_amount).replace(",", ".")

                datos_tabla.append([
                    fecha_inicio_a_str_form,
                    move_name,
                    fecha_vencimiento_a_str_form,
                    monto_depositos_formatted
                ])
                tabla_y -= 40
                logging.info("APPEND: : " + str(fecha_inicio_a_str_form) + " - " + str(move_name))

            tabla = Table(datos_tabla, colWidths=[110, 130, 110, 100])
            tabla.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(180 / 255, 210 / 255, 255 / 255)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONT', (0, 0), (-1, -1), estilo_celda.fontName, estilo_celda.fontSize)
            ]))

            tabla.wrapOn(c, tabla_width, tabla_height)
            tabla.drawOn(c, tabla_x, tabla_y)

            estilo_celda.fontName = 'Helvetica-Bold'
            tabla_y -= 20
            c.rect(70, tabla_y, 450, 20, fill=False)
            move_amount_formatted = "$ {:,.0f}".format(move_amount_periodo).replace(",", ".")
            c.setFont("Helvetica-Bold", 14)
            datos_tabla = [['TOTAL A PAGAR ANTES DEL ' + str(move_due_date.day) + ' DE ' + str(
                mes_actual) + ' DE ' + str(move_due_date.year), move_amount_formatted]]
            tabla = Table(datos_tabla, colWidths=[350, 100])
            tabla.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONT', (0, 0), (-1, -1), estilo_celda.fontName, estilo_celda.fontSize)
            ]))

            tabla.wrapOn(c, tabla_width, tabla_height)
            tabla.drawOn(c, tabla_x, tabla_y)

            tabla_y -= 20
            c.rect(70, tabla_y, 450, 20, fill=False)
            move_amount_multa = (move_amount_periodo * 0.05) + move_amount_periodo
            move_amount_multa_formatted = "$ {:,.0f}".format(move_amount_multa).replace(",", ".")
            datos_tabla = [['TOTAL A PAGAR ANTES DEL ' + str(last_day_of_next_month.day) + ' ' + str(
                mes_siguiente) + ' DE ' + str(last_day_of_next_month.year), move_amount_multa_formatted]]
            tabla = Table(datos_tabla, colWidths=[350, 100])
            tabla.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONT', (0, 0), (-1, -1), estilo_celda.fontName, estilo_celda.fontSize)
            ]))

            tabla.wrapOn(c, tabla_width, tabla_height)
            tabla.drawOn(c, tabla_x, tabla_y)

            tabla_y -= 20
            c.rect(70, tabla_y, 450, 20, fill=False)
            move_amount_multa = (move_amount_multa * 0.05) + move_amount_multa
            move_amount_multa_dos_formatted = "$ {:,.0f}".format(move_amount_multa).replace(",", ".")
            datos_tabla = [['TOTAL A PAGAR ANTES DEL ' + str(last_day_of_next_month_after.day) + ' DE ' + str(
                dos_mes_siguiente) + ' DE ' + str(last_day_of_next_month_after.year), move_amount_multa_dos_formatted]]
            tabla = Table(datos_tabla, colWidths=[350, 100])
            tabla.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONT', (0, 0), (-1, -1), estilo_celda.fontName, estilo_celda.fontSize)
            ]))

            tabla.wrapOn(c, tabla_width, tabla_height)
            tabla.drawOn(c, tabla_x, tabla_y)
            count_cuotas += 1
            c.showPage()

        return c

    @api.model
    def crear_pdf_encabezado(self, c, temp_file):

        w, h = A4

        # Encabezado
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 10)
        # Encabezado  bajada imagen
        c.drawCentredString(w / 2, h - 75, "ASOCIACIÓN DEL CANAL DE LAS MERCEDES")
        # Encabezado  bajada imagen
        c.drawCentredString(w / 2, h - 90, "UNIÓN SAN JOSE PC 23, LOLENCO, COMUNA CURACAVI")

        return c

    @api.model
    def crear_pdf_primera_pagina(self, c, temp_file):

        w, h = A4

        c = self.crear_pdf_encabezado(c, temp_file)

        # Titulo
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(w / 2, h - 130, "CUPONERA DE PAGO CUOTAS AÑO 2023 – 2024")

        styles = getSampleStyleSheet()
        style = styles['Normal']
        style.alignment = 4
        logging.info('altura')
        logging.info(h - 240)
        ancho_maximo = 465
        alto_maximo = 780
        posicion_en_fila = 70

        # Bajada Titulo
        c.setFont("Helvetica", 10)
        c.drawString(70, h - 160, "Estimado (a) Accionista:")

        """
        c.drawString(70, h - 180, "Desde este año 2023 el proceso de pago de cuotas de nuestra")
        c.drawString(70, h - 193, "Asociación tendrá una nueva modalidad, siendo estas las únicas formas de pago.")
        """
        texto_bajada = "&nbsp;&nbsp;&nbsp;Desde este año 2023 el proceso de pago de cuotas de nuestra Asociación tendrá una nueva modalidad, siendo estas las únicas formas de pago."
        bajada = Paragraph(texto_bajada, style)
        bajada.wrapOn(c, ancho_maximo, alto_maximo)
        # canvas, posición x en fila, posición y en documento.
        bajada.drawOn(c, posicion_en_fila, h - 190)

        ancho_maximo = 432
        posicion_en_fila = 102

        # Instrucciones de pago
        c.setFont("Helvetica-Bold", 14)
        c.drawString(70, h - 220, "INSTRUCCIONES Y FORMA DE PAGO:")
        c.setFont("Helvetica", 10)
        # Parrafo 1
        """
        c.drawString(90, h - 240, "1. Pago vía nuestro sitio Web,")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(230, h - 240, "www.canaldelasmercedes.cl")
        c.setFont("Helvetica", 10)
        c.drawString(370, h - 240, " siguiendo los pasos indicados  ")

        c.drawString(90, h - 252, "en la misma a través de la empresa Transbank, en esta plataforma podrá pagar con tarjetas  ")
        c.drawString(90, h - 265, "de débito y crédito (Seleccionando las cuotas que quiera pagar o bien realizar un")
        c.drawString(90, h - 277, "prepago de las cuotas que desee)")
        """
        c.drawString(90, h - 240, "1. ")

        ancho_maximo = 432
        alto_maximo = 780
        posicion_en_fila = 102
        texto_parrafo1 = "Pago vía nuestro sitio Web, <u><i><b>www.canaldelasmercedes.cl</b></i></u> siguiendo los pasos indicados en la misma a través de la empresa Transbank, en esta plataforma podrá pagar con tarjetas de débito o crédito (Seleccionando las cuotas que quiera pagar o bien realizar un prepago de las cuotas que desee)"
        p1 = Paragraph(texto_parrafo1, style)
        p1.wrapOn(c, ancho_maximo, alto_maximo)
        # canvas, posición x en fila, posición y en documento.
        p1.drawOn(c, posicion_en_fila, 564)
        # Parrafo 2
        c.drawString(90, h - 293, "2. ")
        texto_parrafo2 = "Pago a través de transferencia electrónica directa a nuestras cuentas corrientes de la Asociación. (Banco de Chile y/o Banco Estado)"
        p2 = Paragraph(texto_parrafo2, style)
        p2.wrapOn(c, ancho_maximo, alto_maximo)
        # canvas, posición x en fila, posición y en documento.
        p2.drawOn(c, posicion_en_fila, 535)

        """
        c.drawString(90, h - 297, "2. Pago a través de transferencia electrónica directa a nuestras cuentas ")
        c.drawString(90, h - 307, "corriente de la Asociación. (Banco de Chile y/o Banco Estado)")
        """
        # Parrafo 3
        c.drawString(90, h - 325, "3. ")
        texto_parrafo3 = "Descargar e imprimir su cuponera en nuestro sitio Web y acercarse al banco de su preferencia o cercanía <u><i><b>a depositar</b></i></u>, para esto último deberá llenar  los respectivos documentos bancarios que destina el Banco para este tipo de trámites."
        p3 = Paragraph(texto_parrafo3, style)
        p3.wrapOn(c, ancho_maximo, alto_maximo)
        # canvas, posición x en fila, posición y en documento.
        p3.drawOn(c, posicion_en_fila, 491)
        """
        c.drawString(90, h - 325, "3. Descargar e imprimir su cuponera en nuestro sitio Web y acercarse al ")
        c.drawString(90, h - 337, "banco de su preferencia o cercanía")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(250, h - 337, "a depositar")
        c.setFont("Helvetica", 10)
        c.drawString(305, h - 337, ", para esto último deberá llenar  ")
        c.drawString(90, h - 349, "los respectivos documentos bancarios que destina el Banco para este tipo de tramites.")
        """
        # Parrafo 4
        c.drawString(90, h - 365, "4. ")
        texto_parrafo4 = "Si por alguna razón usted no puede imprimir su cuponera, lo invitamos que se acerque a nuestra oficina y le podremos entregar su copia, en donde además contamos con un terminal de pago con tarjeta, para así agilizar este trámite. Además, si usted desea pagar con efectivo, a 100 mts. de nuestra oficina existe un local con CAJA VECINA del BancoEstado, en donde puede efectuar su depósito."
        p4 = Paragraph(texto_parrafo4, style)
        p4.wrapOn(c, ancho_maximo, alto_maximo)
        # canvas, posición x en fila, posición y en documento.
        p4.drawOn(c, posicion_en_fila, 427)
        """
        c.drawString(90, h - 365, "4. Si por alguna razón usted no puede imprimir su cuponera, lo invitamos que se acerque")
        c.drawString(90, h - 377, "a nuestra oficina y le podremos entregar su copia, en donde además contamos con un ")
        c.drawString(90, h - 388, "terminal de pago con tarjeta, para así agilizar este trámite.")
        c.drawString(90, h - 399, "Además, si usted desea pagar con efectivo, a 100 mts. de nuestra oficina existe un local")
        c.drawString(90, h - 412, "con CAJA VECINA del BancoEstado, en donde puede efectuar su depósito.")
        """
        c.setFont("Helvetica", 14)
        rect_color = (180 / 255, 210 / 255, 255 / 255)  # Color azul en formato RGB
        c.setFillColor(rect_color)
        c.rect(70, h - 445, 470, 20, fill=True)
        rect_color = (0, 0, 0)  # Color Negro en formato RGB
        c.setFillColor(rect_color)
        c.drawString(75, h - 440, "BANCO DE CHILE")

        # CUADRO PAGO BANCO CHILE
        c.setFont("Helvetica", 10)
        c.rect(70, h - 465, 90, 20, fill=False)
        c.drawString(70, h - 460, f" NOMBRE")
        c.rect(160, h - 465, 380, 20, fill=False)
        c.drawString(165, h - 460, f"ASOCIACIÓN DEL CANAL DE LAS MERCEDES")

        c.rect(70, h - 485, 90, 20, fill=False)
        c.drawString(70, h - 480, f" BANCO")
        c.rect(160, h - 485, 380, 20, fill=False)
        c.drawString(165, h - 480, f"BANCO CHILE - EDWARDS")

        c.rect(70, h - 505, 90, 20, fill=False)
        c.drawString(70, h - 500, f" TIPO CUENTA")
        c.rect(160, h - 505, 380, 20, fill=False)
        c.drawString(165, h - 500, f"CUENTA CORRIENTE")

        c.rect(70, h - 525, 90, 20, fill=False)
        c.drawString(70, h - 520, f" N° CUENTA")
        c.rect(160, h - 525, 380, 20, fill=False)
        c.drawString(165, h - 520, f"01047-02")

        c.rect(70, h - 545, 90, 20, fill=False)
        c.drawString(70, h - 540, f" RUT")
        c.rect(160, h - 545, 380, 20, fill=False)
        c.drawString(165, h - 540, f"70.059.900-0")

        c.rect(70, h - 565, 90, 20, fill=False)
        c.drawString(70, h - 560, f" CORREO")
        c.rect(160, h - 565, 380, 20, fill=False)
        c.drawString(165, h - 560, f"contacto@canaldelasmercedes.cl")

        c.rect(70, h - 585, 90, 20, fill=False)
        c.drawString(70, h - 580, f" MOTIVO PAGO")
        c.rect(160, h - 585, 380, 20, fill=False)
        c.drawString(165, h - 580, f"INDICAR CÓDIGO DE MARCO Y CUOTA")

        c.setFont("Helvetica", 14)
        rect_color = (180 / 255, 210 / 255, 255 / 255)  # Color azul en formato RGB
        c.setFillColor(rect_color)
        c.rect(70, h - 615, 470, 20, fill=True)
        rect_color = (0, 0, 0)  # Color Negro en formato RGB
        c.setFillColor(rect_color)
        c.drawString(75, h - 610, "BANCO ESTADO")

        # CUADRO PAGO BANCO ESTADO
        c.setFont("Helvetica", 10)
        c.rect(70, h - 635, 90, 20, fill=False)
        c.drawString(70, h - 630, f" NOMBRE")
        c.rect(160, h - 635, 380, 20, fill=False)
        c.drawString(165, h - 630, f"ASOCIACIÓN DEL CANAL DE LAS MERCEDES")

        c.rect(70, h - 655, 90, 20, fill=False)
        c.drawString(70, h - 650, f" BANCO")
        c.rect(160, h - 655, 380, 20, fill=False)
        c.drawString(165, h - 650, f"BANCO ESTADO")

        c.rect(70, h - 675, 90, 20, fill=False)
        c.drawString(70, h - 670, f" TIPO CUENTA")
        c.rect(160, h - 675, 380, 20, fill=False)
        c.drawString(165, h - 670, f"CUENTA CORRIENTE")

        c.rect(70, h - 695, 90, 20, fill=False)
        c.drawString(70, h - 690, f" N° CUENTA")
        c.rect(160, h - 695, 380, 20, fill=False)
        c.drawString(165, h - 690, f"31000004998")

        c.rect(70, h - 715, 90, 20, fill=False)
        c.drawString(70, h - 710, f" RUT")
        c.rect(160, h - 715, 380, 20, fill=False)
        c.drawString(165, h - 710, f"70.059.900-0")

        c.rect(70, h - 735, 90, 20, fill=False)
        c.drawString(70, h - 730, f" CORREO")
        c.rect(160, h - 735, 380, 20, fill=False)
        c.drawString(165, h - 730, f"contacto@canaldelasmercedes.cl")

        c.rect(70, h - 755, 90, 20, fill=False)
        c.drawString(70, h - 750, f" MOTIVO PAGO")
        c.rect(160, h - 755, 380, 20, fill=False)
        c.drawString(165, h - 750, f"INDICAR CÓDIGO DE MARCO Y CUOTA")

        # Se despliega la 1era Hoja PDF
        c.showPage()

        return c

    @api.model
    def generar_pdf_cuponera_base64(self, temp_file, canvas_cuponera):

        canvas_cuponera.save()
        # Lectura del archivo creado y su codificación a base64 para el attachment
        with open(temp_file.name, 'rb') as f:
            byte_data = base64.b64encode(f.read())

        # Eliminamos el archivo temporal después de leerlo
        os.unlink(temp_file.name)
        return byte_data

    @api.model
    def generar_pdf_cuponera(self, temp_file, canvas_cuponera):

        byte_data = self.generar_pdf_cuponera_base64(temp_file, canvas_cuponera)

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

    @api.model
    def generar_zip_cuponeras(self, cuponeras_folder):
        if os.path.exists(cuponeras_folder):
            zip_file_name = 'cuponeras.zip'
            cuponeras_zip_folder = os.path.join(os.path.dirname(__file__), 'zip')

            # Asegurarse de que la carpeta exista, si no, crearla
            if not os.path.exists(cuponeras_zip_folder):
                os.makedirs(cuponeras_zip_folder)

            zip_file_path = os.path.join(cuponeras_zip_folder, zip_file_name)
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for root, _, files in os.walk(cuponeras_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, cuponeras_folder))

            # Devolver el ID del archivo adjunto creado
            return self.descargar_archivo_adjunto(zip_file_path)

    @api.model
    def descargar_archivo_adjunto(self, zip_file_path):
        # Leer el archivo ZIP como datos binarios
        with open(zip_file_path, 'rb') as zip_file:
            zip_data = zip_file.read()

        # Crear un archivo adjunto para el ZIP
        attachment = self.env['ir.attachment'].create({
            'name': 'cuponeras.zip',
            'type': 'binary',
            'datas': base64.b64encode(zip_data),
            'res_model': self._name,
            'res_id': self.id,
        })

        # Devolver una respuesta para descargar el archivo ZIP
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{id}/{name}'.format(id=attachment.id, name=attachment.name),
            'target': 'new',
        }

    @api.model
    def generar_pdf_cuponera_carpeta(self, temp_file, canvas_cuponera, rut_accionista, nombre_holding):
        # Generar el nombre de archivo único basado en el RUT
        file_name = f'Cuponera_{nombre_holding}_{rut_accionista}.pdf'

        # Decodificar el contenido base64
        byte_data = self.generar_pdf_cuponera_base64(temp_file, canvas_cuponera)
        decoded_data = base64.b64decode(byte_data)

        # Definir la ruta de la carpeta dentro del proyecto
        output_folder = os.path.join(os.path.dirname(__file__),
                                     'Cuponeras')  # Cambia 'Cuponeras' por el nombre de tu carpeta

        # Asegurarse de que la carpeta exista, si no, crearla
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Ruta completa del archivo en la carpeta de salida
        output_path = os.path.join(output_folder, file_name)

        # Guardar el PDF en la carpeta (sobrescribir si ya existe)
        with open(output_path, 'wb') as f:
            f.write(decoded_data)







