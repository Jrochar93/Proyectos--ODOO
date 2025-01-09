from odoo.exceptions import UserError
import base64
import csv
import logging
import os
import tempfile
import xlsxwriter
from datetime import date
from odoo import models, fields, api, _
from datetime import datetime


class Aclmicontador(models.Model):
    _name = 'aclm.icontador'
    _description = 'Generación de Reporte para Icontador '

    #accionista_de = fields.Many2one('res.partner', string='Accionistas', domain=[('x_studio_accionista', '=', 'Activo')], order='name')
    accionista = fields.Selection([
        ('Todos', 'Todos'),
    ], string='Accionistas', required=True, default='Todos')
    tipo_reporte = fields.Selection([
        ('Multas', 'Ingreso Multas'),
        ('Cuotas', 'Ingreso Cuotas'),
        ('Cobros', 'Ingreso Cobros'),
    ], string='Tipo de Reporte', required=True, default='Multas')
    fecha_inicio_de = fields.Date(string='Fecha de', required=True)
    fecha_inicio_a = fields.Date(string='Fecha  A', required=True)

    reporte_excel_multas = fields.Binary(string='Reporte Excel Multas', readonly=True)
    nombre_reporte_excel_multas = fields.Char(string='Nombre Reporte Excel Multas', readonly=True)

    @api.constrains('fecha_inicio_de', 'fecha_inicio_a')
    def _check_fecha(self):
        for record in self:
            if record.fecha_inicio_de > record.fecha_inicio_a:
                raise UserError(_("La fecha de inicio no puede ser mayor que la fecha final."))

    @api.onchange('tipo_reporte')
    def Generar_Reporte(self):
        if self.tipo_reporte == 'Multas':
            report_action = self.generar_reporte_excel_multas()
            if report_action:
                return report_action
        elif self.tipo_reporte == 'Cuotas':
            report_action = self.generar_reporte_excel_cuotas()
            if report_action:
                return report_action
        elif self.tipo_reporte == 'Cobros':
            report_action = self.generar_reporte_excel_cobros()
            if report_action:
                return report_action

    def generar_reporte_excel_multas(self):

        # Crear un archivo temporal para almacenar el archivo Excel
        temp_file_path = tempfile.mktemp(suffix='.xlsx')

        # Crear un libro y una hoja de cálculo en el archivo Excel
        workbook = xlsxwriter.Workbook(temp_file_path)
        worksheet = workbook.add_worksheet()

        # Encabezados de columna para las facturas
        invoice_headers = [
            'Fecha Docto', 'Tipo Docto', 'Nro Docto', 'Rut', 'Nombre', 'CTA Neto', 'CA Neto', 'CC Neto',
            'Monto Neto', 'CTA Exento', 'CA Exento', 'CC Exento', 'Monto Exento', 'COD SII Otro', 'CTA Otro',
            'CA Otro', 'CC Otro', 'Monto Otro', '% IVA', 'IVA', 'TOTAL', 'Glosa'
        ]

        # Escribir encabezados de columna para las facturas
        for col, header in enumerate(invoice_headers):
            worksheet.write(0, col, header)

        # Buscar todos los pagos conciliados que cumplen con el criterio
        payments_pagos = self.env['account.payment'].search([
            ('create_date', '>=', self.fecha_inicio_de),
            ('create_date', '<=', self.fecha_inicio_a),
            # ('partner_id', '=', 8269),
        ])

        row = 1  # Comenzar desde la fila 1 para escribir los datos de las facturas
        for payment in payments_pagos:
            logging.info(f'Pagos {payment.move_id.id}')
            invoice_pagada = self.env['account.move'].search([('id', '=', payment.move_id.id)])

            for invoice in invoice_pagada:
                logging.info(f'Invoice {invoice.id}')

                invoices_conciliadas = self.env['account.move.line'].search([
                    ('partner_id', '=', invoice.partner_id.id),
                    ('move_id', '=', invoice.id),
                    ('reconciled', '=', True),
                    ('account_id.id', '=', 5),
                ], order='date')

                for conciliadas in invoices_conciliadas:

                    glosa = "Ingreso por "
                    glosa += f" {invoice.ref}"
                    document_types = (66)
                    invoices_encontradas = self.env['account.move.line'].search([
                        ('partner_id', '=', conciliadas.partner_id.id),
                        ('matching_number', '=', conciliadas.matching_number),
                        ('account_id.id', '=', 5),
                        #('reconciled', '=', True),
                        ('l10n_latam_document_type_id', '=', document_types),
                    ], order='date')

                    for invoice_line in invoices_encontradas:
                        logging.info(f'invoices_pagadas {invoice_line.id}')

                        # Calcular el monto exento como la diferencia entre el monto total y el monto residual de la factura
                        monto_exento = invoice_line.move_id.amount_total - invoice_line.move_id.amount_residual


                        # Escribir los datos de la factura en la hoja de cálculo
                        worksheet.write(row, 0, invoice_line.write_date.strftime('%d-%m-%Y'))  # Formatear la fecha como una cadena
                        worksheet.write(row, 1, '40')  # Asumiendo que 'Tipo Docto' es constante '40'
                        worksheet.write(row, 2, invoice_line.name) # O el número de factura si está disponible
                        worksheet.write(row, 3, invoice.partner_id.x_studio_marco_para_icontador)
                        worksheet.write(row, 4, invoice.partner_id.name)
                        worksheet.write(row, 5, '')  # Campo vacío para 'Cliente' (¿Quizás se refiere a otro campo?)
                        worksheet.write(row, 6, '')  # Campo vacío para 'CTA Neto'
                        worksheet.write(row, 7, '')  # Campo vacío para 'CA Neto'
                        worksheet.write(row, 8, '')  # Campo vacío para 'Monto Neto'
                        worksheet.write(row, 9, '502010')  # Asumiendo que 'CTA Exento' es constante '502010'
                        worksheet.write(row, 10, '')  # Campo vacío para 'CA Exento'
                        worksheet.write(row, 11, '')  # Campo vacío para 'CC Exento'
                        worksheet.write(row, 12, monto_exento)  # 'Monto Exento'
                        worksheet.write(row, 13, '')  # Campo vacío para 'COD SII Otro'
                        worksheet.write(row, 14, '')  # Campo vacío para 'CTA Otro'
                        worksheet.write(row, 15, '')  # Campo vacío para 'CA Otro'
                        worksheet.write(row, 16, '')  # Campo vacío para 'CC Otro'
                        worksheet.write(row, 17, '')  # Campo vacío para 'Monto Otro'
                        worksheet.write(row, 18, '')  # Campo vacío para '% IVA'
                        worksheet.write(row, 19, '')  # Campo vacío para 'IVA'
                        worksheet.write(row, 20, monto_exento)  # Campo vacío para 'TOTAL'
                        worksheet.write(row, 21, glosa)  # Escribir la glosa en la hoja de cálculo

                        # Incrementar el contador de fila para la siguiente factura
                        row += 1

        # Cerrar el libro y guardar el archivo Excel
        workbook.close()

        # Leer el contenido del archivo Excel generado
        with open(temp_file_path, 'rb') as excel_file:
            excel_content = excel_file.read()

        # Codificar el contenido del archivo Excel en base64
        encoded_content = base64.b64encode(excel_content)

        # Actualizar el campo de archivo binario en el modelo
        self.write({'reporte_excel_multas': encoded_content,
                    'nombre_reporte_excel_multas': 'Reporte_Multas.xlsx'})

        # Eliminar el archivo temporal
        os.unlink(temp_file_path)

        # Devolver la acción para descargar el archivo Excel
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=%s&id=%s&field=reporte_excel_multas&filename_field=nombre_reporte_excel_multas&download=true' % (
                self._name, self.id),
            'target': 'self'
        }



    def generar_reporte_excel_cuotas(self):

        # Crear un archivo temporal para almacenar el archivo Excel
        temp_file_path = tempfile.mktemp(suffix='.xlsx')

        # Crear un libro y una hoja de cálculo en el archivo Excel
        workbook = xlsxwriter.Workbook(temp_file_path)
        worksheet = workbook.add_worksheet()

        # Encabezados de columna para las facturas
        invoice_headers = [
            'Fecha Docto', 'Tipo Docto', 'Nro Docto', 'Rut', 'Nombre', 'CTA Neto', 'CA Neto', 'CC Neto',
            'Monto Neto', 'CTA Exento', 'CA Exento', 'CC Exento', 'Monto Exento', 'COD SII Otro', 'CTA Otro',
            'CA Otro', 'CC Otro', 'Monto Otro', '% IVA', 'IVA', 'TOTAL', 'Glosa'
        ]

        # Escribir encabezados de columna para las facturas
        for col, header in enumerate(invoice_headers):
            worksheet.write(0, col, header)

        # Buscar todos los pagos conciliados que cumplen con el criterio
        payments_pagos = self.env['account.payment'].search([
            ('create_date', '>=', self.fecha_inicio_de),
            ('create_date', '<=', self.fecha_inicio_a),
            #('partner_id', '=', 7392),
        ])

        row = 1  # Comenzar desde la fila 1 para escribir los datos de las facturas
        for payment in payments_pagos:
            logging.info(f'Pagos {payment.move_id.id}')
            invoice_pagada = self.env['account.move'].search([('id', '=', payment.move_id.id)])

            for invoice in invoice_pagada:
                logging.info(f'Invoice {invoice.id}')


                invoices_conciliadas = self.env['account.move.line'].search([
                    ('partner_id', '=', invoice.partner_id.id),
                    ('move_id', '=', invoice.id),
                    ('reconciled', '=', True),
                    ('account_id.id', '=', 5),
                ], order='date')

                for conciliadas in invoices_conciliadas:

                    glosa = "Ingreso por "
                    glosa += f" {invoice.ref}"
                    document_types = (62, 60, 68)
                    invoices_encontradas = self.env['account.move.line'].search([
                        ('partner_id', '=', conciliadas.partner_id.id),
                        ('matching_number', '=', conciliadas.matching_number),
                        ('account_id.id', '=', 5),
                        #('reconciled', '=', True),
                        ('l10n_latam_document_type_id', 'in', document_types),
                    ], order='date')

                    for invoice_line in invoices_encontradas:
                        logging.info(f'invoices_pagadas {invoice_line.id} matching_number {invoice_line.matching_number}')
                        CTA = invoice_line.l10n_latam_document_type_id.id
                        CTA_Exento = ''
                        if CTA == 60:
                            CTA_Exento = '501005'
                        elif CTA == 62:
                            CTA_Exento = '501004'
                        # Calcular el monto exento como la diferencia entre el monto total y el monto residual de la factura
                        monto_exento = invoice_line.move_id.amount_total - invoice_line.move_id.amount_residual

                        # Escribir los datos de la factura en la hoja de cálculo
                        worksheet.write(row, 0, invoice_line.write_date.strftime('%d-%m-%Y'))  # Formatear la fecha como una cadena
                        worksheet.write(row, 1, '38')  # Asumiendo que 'Tipo Docto' es constante '40'
                        worksheet.write(row, 2, invoice_line.name)  # O el número de factura si está disponible
                        worksheet.write(row, 3, invoice.partner_id.x_studio_marco_para_icontador)
                        worksheet.write(row, 4, invoice.partner_id.name)
                        worksheet.write(row, 5, '')  # Campo vacío para 'Cliente' (¿Quizás se refiere a otro campo?)
                        worksheet.write(row, 6, '')  # Campo vacío para 'CTA Neto'
                        worksheet.write(row, 7, '')  # Campo vacío para 'CA Neto'
                        worksheet.write(row, 8, '')  # Campo vacío para 'Monto Neto'
                        worksheet.write(row, 9, CTA_Exento)  # Asumiendo que 'CTA Exento' es constante '502010'
                        worksheet.write(row, 10, '')  # Campo vacío para 'CA Exento'
                        worksheet.write(row, 11, '')  # Campo vacío para 'CC Exento'
                        worksheet.write(row, 12, monto_exento)  # 'Monto Exento'
                        worksheet.write(row, 13, '')  # Campo vacío para 'COD SII Otro'
                        worksheet.write(row, 14, '')  # Campo vacío para 'CTA Otro'
                        worksheet.write(row, 15, '')  # Campo vacío para 'CA Otro'
                        worksheet.write(row, 16, '')  # Campo vacío para 'CC Otro'
                        worksheet.write(row, 17, '')  # Campo vacío para 'Monto Otro'
                        worksheet.write(row, 18, '')  # Campo vacío para '% IVA'
                        worksheet.write(row, 19, '')  # Campo vacío para 'IVA'
                        worksheet.write(row, 20, monto_exento)  # Campo vacío para 'TOTAL'
                        worksheet.write(row, 21, glosa)  # Escribir la glosa en la hoja de cálculo

                        # Incrementar el contador de fila para la siguiente factura
                        row += 1

        # Cerrar el libro y guardar el archivo Excel
        workbook.close()

        # Leer el contenido del archivo Excel generado
        with open(temp_file_path, 'rb') as excel_file:
            excel_content = excel_file.read()

        # Codificar el contenido del archivo Excel en base64
        encoded_content = base64.b64encode(excel_content)

        # Actualizar el campo de archivo binario en el modelo
        self.write({'reporte_excel_multas': encoded_content,
                    'nombre_reporte_excel_multas': 'Reporte_Cuotas.xlsx'})

        # Eliminar el archivo temporal
        os.unlink(temp_file_path)

        # Devolver la acción para descargar el archivo Excel
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=%s&id=%s&field=reporte_excel_multas&filename_field=nombre_reporte_excel_multas&download=true' % (
                self._name, self.id),
            'target': 'self'
        }

    def generar_reporte_excel_cobros(self):


        # Crear un archivo temporal para almacenar el archivo Excel
        temp_file_path = tempfile.mktemp(suffix='.xlsx')

        # Crear un libro y una hoja de cálculo en el archivo Excel
        workbook = xlsxwriter.Workbook(temp_file_path)
        worksheet = workbook.add_worksheet()

        # Encabezados de columna para las facturas
        invoice_headers = [
            'Fecha Docto', 'Tipo Docto', 'Nro Docto', 'Rut', 'Nombre', 'CTA Neto', 'CA Neto', 'CC Neto',
            'Monto Neto', 'CTA Exento', 'CA Exento', 'CC Exento', 'Monto Exento', 'COD SII Otro', 'CTA Otro',
            'CA Otro', 'CC Otro', 'Monto Otro', '% IVA', 'IVA', 'TOTAL', 'Glosa'
        ]

        # Escribir encabezados de columna para las facturas
        for col, header in enumerate(invoice_headers):
            worksheet.write(0, col, header)

        # Buscar todas las facturas que cumplen con el criterio
        payments_pagos = self.env['account.payment'].search([
            ('create_date', '>=', self.fecha_inicio_de),  # Filtrar por fecha de inicio
            ('create_date', '<=', self.fecha_inicio_a)  # Filtrar por fecha de fin
        ])


        row = 1  # Comenzar desde la fila 1 para escribir los datos de las facturas
        for payments in payments_pagos:
            logging.info(f'Pagos {payments.move_id.id}')
            CTA_Exento = ''
            if str(payments.outstanding_account_id.id) == '201':
                CTA_Exento = '101002'
            else:
                CTA_Exento = '101003'

            invoice_pagada = self.env['account.move'].search([('id', '=', payments.move_id.id)])

            for invoice in invoice_pagada:
                logging.info(f'Invoice {invoice.id}')

                invoices_conciliadas = self.env['account.move.line'].search([
                    ('partner_id', '=', invoice.partner_id.id),
                    ('move_id', '=', invoice.id),
                    ('reconciled', '=', True),
                    ('account_id.id', '=', 5),
                ], order='date')

                for conciliadas in invoices_conciliadas:

                    glosa = "Ingreso por "
                    glosa += f" {invoice.ref}"
                    document_types = (60, 62,63,66,68,70)
                    invoices_encontradas = self.env['account.move.line'].search([
                        ('partner_id', '=', conciliadas.partner_id.id),
                        ('matching_number', '=', conciliadas.matching_number),
                        ('account_id.id', '=', 5),
                        #('reconciled', '=', True),
                        ('l10n_latam_document_type_id', 'in', document_types),
                    ], order='date')

                    for invoice_line in invoices_encontradas:
                        logging.info(f'invoices_pagadas {invoice_line.id}')

                        # Calcular el monto exento como la diferencia entre el monto total y el monto residual de la factura
                        monto_exento = invoice_line.move_id.amount_total - invoice_line.move_id.amount_residual

                        # Escribir los datos de la factura en la hoja de cálculo
                        worksheet.write(row, 0, invoice_line.write_date.strftime('%d-%m-%Y'))  # Formatear la fecha como una cadena
                        worksheet.write(row, 1, '61')  # Asumiendo que 'Tipo Docto' es constante '40'
                        worksheet.write(row, 2, invoice_line.name)  # O el número de factura si está disponible
                        worksheet.write(row, 3, invoice.partner_id.x_studio_marco_para_icontador)
                        worksheet.write(row, 4, invoice.partner_id.name)
                        worksheet.write(row, 5, '')  # Campo vacío para 'Cliente' (¿Quizás se refiere a otro campo?)
                        worksheet.write(row, 6, '')  # Campo vacío para 'CTA Neto'
                        worksheet.write(row, 7, '')  # Campo vacío para 'CA Neto'
                        worksheet.write(row, 8, '')  # Campo vacío para 'Monto Neto'
                        worksheet.write(row, 9, CTA_Exento)  # Asumiendo que 'CTA Exento' es constante '502010'
                        worksheet.write(row, 10, '')  # Campo vacío para 'CA Exento'
                        worksheet.write(row, 11, '')  # Campo vacío para 'CC Exento'
                        worksheet.write(row, 12, monto_exento)  # 'Monto Exento'
                        worksheet.write(row, 13, '')  # Campo vacío para 'COD SII Otro'
                        worksheet.write(row, 14, '')  # Campo vacío para 'CTA Otro'
                        worksheet.write(row, 15, '')  # Campo vacío para 'CA Otro'
                        worksheet.write(row, 16, '')  # Campo vacío para 'CC Otro'
                        worksheet.write(row, 17, '')  # Campo vacío para 'Monto Otro'
                        worksheet.write(row, 18, '')  # Campo vacío para '% IVA'
                        worksheet.write(row, 19, '')  # Campo vacío para 'IVA'
                        worksheet.write(row, 20, monto_exento)  # Campo vacío para 'TOTAL'
                        worksheet.write(row, 21, glosa)  # Escribir la glosa en la hoja de cálculo

                        # Incrementar el contador de fila para la siguiente factura
                        row += 1

            # Cerrar el libro y guardar el archivo Excel
        workbook.close()

        # Leer el contenido del archivo Excel generado
        with open(temp_file_path, 'rb') as excel_file:
            excel_content = excel_file.read()

        # Codificar el contenido del archivo Excel en base64
        encoded_content = base64.b64encode(excel_content)

        # Actualizar el campo de archivo binario en el modelo
        self.write({'reporte_excel_multas': encoded_content,
                    'nombre_reporte_excel_multas': 'Reporte_Cobros.xlsx'})

        # Eliminar el archivo temporal
        os.unlink(temp_file_path)

        # Devolver la acción para descargar el archivo Excel
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=%s&id=%s&field=reporte_excel_multas&filename_field=nombre_reporte_excel_multas&download=true' % (
                self._name, self.id),
            'target': 'self'
        }


