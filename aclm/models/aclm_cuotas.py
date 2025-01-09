from odoo.exceptions import AccessError, UserError, ValidationError
import csv
from odoo import models, fields, api, _


from dateutil.relativedelta import relativedelta
import tempfile
import base64
from io import StringIO
from datetime import datetime
import xlsxwriter
import os

import calendar

import sys
import time

from functools import partial
import threading
from threading import Semaphore

MAX_THREADS = 4  # Número máximo de hilos permitidos simultáneamente
# Lib Config Logger
import logging
logging.basicConfig(filename="/var/log/odoo/odoo-server.log", format='%(asctime)s %(message)s', filemode='w')


class AclmCuotas(models.Model):
    _name = 'aclm.cuotas'
    _description = 'Generación de Cuotas (Normales, Multa, Extraordinarias)'


    # ------------------------------------------------------------------ #
    #                   Definición de Funciones Basicas                  #
    # ------------------------------------------------------------------ #

    def _get_typograph(self, num_cuota):
        if num_cuota == 1 or num_cuota == 3:
            typograph = 'ra'
        elif num_cuota == 2:
            typograph = 'da'
        elif num_cuota == 4 or num_cuota == 5 or num_cuota == 6:
            typograph = 'ta'
        elif num_cuota == 7:
            typograph = 'ma'
        elif num_cuota == 8:
            typograph = 'va'
        elif num_cuota == 9:
            typograph = 'na'
        else: 
            typograph = '-'
        return typograph

    def _get_first_day_of_month(self, anio, mes, date_format='%Y-%m-%d'):
        init_date = datetime(anio, mes, 1)
        return init_date.strftime(date_format)
    
    def _get_last_day_of_month(self, anio, mes, date_format='%Y-%m-%d'):
        ultimo_dia = calendar.monthrange(anio, mes)[1]
        last_date = datetime(anio, mes, ultimo_dia)
        return last_date.strftime(date_format)

    def _get_month_year(self):
        months_options = [
            ('1', 'Enero'),
            ('2', 'Febrero'),
            ('3', 'Marzo'),
            ('4', 'Abril'),
            ('5', 'Mayo'),
            ('6', 'Junio'),
            ('7', 'Julio'),
            ('8', 'Agosto'),
            ('9', 'Septiembre'),
            ('10', 'Octubre'),
            ('11', 'Noviembre'),
            ('12', 'Diciembre')
        ]

        return months_options


    # Función que obtiene listado de Accionistas - Holding.
    def _get_users_between_params(self, accionista_de_id, accionista_a_id, tipo_req):

        accionista_de = self.env['res.partner'].browse(accionista_de_id) if accionista_de_id else None
        accionista_a  = self.env['res.partner'].browse(accionista_a_id) if accionista_a_id else None

        if (accionista_de and accionista_a) and (accionista_de_id and accionista_a_id):
            usuarios = self.env['res.partner'].search([
                ('name', '>=', accionista_de.name),
                ('name', '<=', accionista_a.name),
                ('x_studio_accionista', '=', 'Activo')
            ], order='name')
        
        elif (accionista_de and accionista_de_id) and (not accionista_a_id or  not accionista_a_id):
            usuarios = self.env['res.partner'].search([
                    ('name', '>=', accionista_de.name),
                    ('x_studio_accionista', '=', 'Activo')
                ], order='name')
        else:
            usuarios = self.env['res.partner'].search([
                ('x_studio_accionista', '=', 'Activo')
            ], order='name')
        
        
        return usuarios   

    def get_partner_holdings(self):
        # obtener los registros de partner donde 'x_studio_accionista' es 'Activo'
        partners = self.env['res.partner'].search([('x_studio_accionista', '=', 'Activo')], order='id asc')
        # crear un conjunto de los valores x_studio_holding únicos
        unique_holdings = {partner.x_studio_holding for partner in partners}
        # crear una lista de tuplas de los valores únicos
        return [(holding, holding) for holding in unique_holdings]

    # ------------------------------------------------------------------ #
    #               Definición de Campos de Modelo                       #
    # ------------------------------------------------------------------ #

    accionista_de   = fields.Many2one('res.partner', string='Accionista de', domain=[('x_studio_accionista', '=', 'Activo')])
    accionista_a    = fields.Many2one('res.partner', string='Accionista a', domain=[('x_studio_accionista', '=', 'Activo')])
    holding_de      = fields.Many2one('res.partner', string='Holding de', domain=[('x_studio_accionista', '=', 'Activo')])
    holding_a       = fields.Many2one('res.partner', string='Holding a', domain=[('x_studio_accionista', '=', 'Activo')])

    monto_valor_cuota = fields.Integer(string='Monto valor Cuota', required=True)
    anio_inicio     = fields.Integer(string='Año Inicio', default=lambda self: fields.Date.today().year, required=True)
    mes_inicio      = fields.Selection(string='Mes Inicio', selection = _get_month_year, default=lambda self: str(fields.Date.today().month), required=True)
    docto_autoriza  = fields.Text(string='Docto Autoriza', required=True)
    numero_cuotas   = fields.Integer(string='Numero Cuotas', required=True)
    tipo_cuota      = fields.Selection([
        ('0', 'Cuota Normal'),
        ('3', 'Extraordinaria'),
    ], string='Tipo Cuota', required=True)
    cuota_procesada = fields.Boolean(default=False)
    cuota_valida    = fields.Boolean(default=False)

    # ------------------------------------------------------------------ #
    #                Logica de Generación de Datos                       #
    # ------------------------------------------------------------------ #

    def generate_data_from_period(self, datos_cuota, tipo_req):

        data_csv    = []  # Lista para almacenar los datos
        list_months = self._get_month_year()
        anio_inicio = datos_cuota['anio_inicio']
        usuarios    = self._get_users_between_params(datos_cuota['accionista_de'],datos_cuota['accionista_a'],'accionista')

        for usuario in usuarios:
            
            month_now             = int(datos_cuota['mes_inicio'])
            cantidad_acciones     = float(str(usuario.x_studio_cantidad_1).replace(',', '.'))
            cuota_mensual_usuario = (float(datos_cuota['monto_valor_cuota']) * cantidad_acciones) / float(datos_cuota['numero_cuotas'])
            
            posicion = 1
            for  _ in enumerate(range(datos_cuota['numero_cuotas'])):

                if posicion > datos_cuota['numero_cuotas']:
                    break

                if month_now > len(list_months):
                    month_now = 1
                    anio_inicio += 1

                
                typograph       = self._get_typograph(posicion)

                #AGREGAR IR CUOTA o EXTRA
                if datos_cuota['tipo_cuota'] == '0':
                    des_tipo     = ' Cuota '
                else:
                    des_tipo     = ' Extra '
                        
                description     = str(posicion) + typograph + des_tipo + str(anio_inicio) +" "+ usuario.x_studio_cod_de_marco
                des             = str(posicion) + typograph
                
                if(tipo_req == 'borrador'):
                    description     = str(posicion) + typograph + des_tipo + str(anio_inicio)
                    fecha_cuota             = self._get_first_day_of_month(anio_inicio, month_now, '%d-%m-%Y')
                    fecha_cuota_vencimiento = self._get_last_day_of_month(anio_inicio, month_now, '%d-%m-%Y')
                    data_csv.append({
                        'nombre_usuario'            : usuario.name,
                        'codigo_marco'              : usuario.x_studio_cod_de_marco,
                        'cantidad_acciones'         : usuario.x_studio_cantidad_1,
                        'cuota_mensual'             : cuota_mensual_usuario,
                        'cuota'                     : datos_cuota['monto_valor_cuota'],
                        'posicion'                  : posicion,
                        'descripcion'               : description,
                        'des'                       : des,
                        'fecha_vencimiento_cuota'   : fecha_cuota_vencimiento,
                        'fecha_cuota'               : fecha_cuota,
                    })

                if(tipo_req == 'firme'):

                    try:
                        fecha_cuota             = self._get_first_day_of_month(anio_inicio, month_now)
                        fecha_cuota_vencimiento = self._get_last_day_of_month(anio_inicio, month_now)

                        query = "%%%s%%" % datos_cuota['tipo_cuota']  # Agregar los símbolos '%' al valor
                        product_template_id = self.env['product.template'].search([('x_studio_tipo_docto_1', 'ilike', query)], limit=1)
                        
                        #product_template_id = self.env['product.template'].search([('x_studio_tipo_docto_1', 'ilike', data_firme_cuota['x_studio_tipo_docto_1'][0])], limit=1)
                        if not product_template_id:
                            raise models.ValidationError('No se encontró ningún producto Template con ese tipo de documento.')
                        
                        product_id = self.env['product.product'].search([('product_tmpl_id', '=', product_template_id.id)], limit=1)
                        if not product_id:
                            raise models.ValidationError('No se encontró ningún producto con ese tipo de documento.')
                        
                        document_type_id = self.env['l10n_latam.document.type'].search([('code', '=', datos_cuota['tipo_cuota'])], limit=1)
                        if not document_type_id:
                            raise models.ValidationError('No se encontró el tipo de documento {} para la creación de la cuota'.format(data_firme_cuota['l10n_latam_document_type_id']))
                        

                        data_csv.append({
                            'l10n_latam_document_type_id': document_type_id.id,
                            'product_id'        : product_id.id,
                            'product_name'      : product_id.name,
                            'name'              : description,
                            'invoice_date_due'  : fecha_cuota_vencimiento,
                            'invoice_date'      : fecha_cuota,
                            'partner_id'        : usuario.id,
                            'x_studio_tipo_docto_1': datos_cuota['tipo_cuota'],
                            'price_unit'        : cuota_mensual_usuario,
                            'account_id': product_id.property_account_income_id.id or product_id.categ_id.property_account_income_categ_id.id,
                        })

                    
                    except Exception as e:
                        # Manejo de la excepción y registro del error
                        logging.error("Error generate_data_from_period FIRME: %s", str(e))

                month_now += 1
                posicion  += 1
        return data_csv


    def generar_borrador(self, *args, **kwargs):

        accionista_de   = self.env.context.get('accionista_de')
        accionista_a    = self.env.context.get('accionista_a')
        holding_de      = self.env.context.get('holding_de')
        holding_a       = self.env.context.get('holding_a')
        monto_valor_cuota = self.env.context.get('monto_valor_cuota')
        anio_inicio     = self.env.context.get('anio_inicio')
        mes_inicio      = self.env.context.get('mes_inicio')
        docto_autoriza  = self.env.context.get('docto_autoriza')
        numero_cuotas   = self.env.context.get('numero_cuotas')
        tipo_cuota      = self.env.context.get('tipo_cuota')

        cuotas = {
            'accionista_de' : accionista_de,
            'accionista_a'  : accionista_a,
            'holding_de'    : holding_de,
            'holding_a'     : holding_a,
            'monto_valor_cuota': monto_valor_cuota,
            'anio_inicio'   : anio_inicio,
            'mes_inicio'    : mes_inicio,
            'docto_autoriza': docto_autoriza,
            'numero_cuotas' : numero_cuotas,
            'tipo_cuota'    : tipo_cuota
        }
        
        data_borrador = self.generate_data_from_period(cuotas, 'borrador')
        return self.crear_excel(data_borrador)



    def generar_firme(self, *args, **kwargs):
        
        accionista_de   = self.env.context.get('accionista_de')
        accionista_a    = self.env.context.get('accionista_a')
        holding_de      = self.env.context.get('holding_de')
        holding_a       = self.env.context.get('holding_a')
        monto_valor_cuota = self.env.context.get('monto_valor_cuota')
        anio_inicio     = self.env.context.get('anio_inicio')
        mes_inicio      = self.env.context.get('mes_inicio')
        docto_autoriza  = self.env.context.get('docto_autoriza')
        numero_cuotas   = self.env.context.get('numero_cuotas')
        tipo_cuota      = self.env.context.get('tipo_cuota')

        cuotas = {
            'accionista_de': accionista_de,
            'accionista_a': accionista_a,
            'holding_de'    : holding_de,
            'holding_a'     : holding_a,
            'monto_valor_cuota': monto_valor_cuota,
            'anio_inicio': anio_inicio,
            'mes_inicio': mes_inicio,
            'docto_autoriza': docto_autoriza,
            'numero_cuotas': numero_cuotas,
            'tipo_cuota': tipo_cuota
        }

        valida_cuota = self._valida_registra_cuota(cuotas)
        
        if valida_cuota != True:
            mensaje = valida_cuota
            title = 'Error'
        else:
            mensaje = 'Las Cuotas se generarán.'
            title = 'Éxito'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': mensaje,
                'sticky': False,  # True si quieres que sea pegajoso y no desaparezca automáticamente
            },
        }


    def _valida_registra_cuota(self, cuotas):
        
        delete_registro_existente_valido = self.env['aclm.cuotas'].search([('cuota_valida', '=', False)])
        #delete_registro_existente_valido.unlink()

        tipo_cuota = int(cuotas['tipo_cuota'])
        anio_inicio = int(cuotas['anio_inicio'])
        mes_inicio = int(cuotas['mes_inicio'])
        meses_adicionales = cuotas['numero_cuotas']

        # Crear la fecha de inicio
        fecha_inicio = datetime(anio_inicio, mes_inicio, 1)

        # Calcular la fecha final sumando meses adicionales
        fecha_final = fecha_inicio + relativedelta(months=meses_adicionales)

        # Obtener el año y mes resultantes
        anio_nuevo = fecha_final.year
        mes_nuevo = fecha_final.month

        # Ajustar el año si el mes resultante supera 12
        if mes_nuevo > 12:
            anio_nuevo += 1
            mes_nuevo %= 12

        # Obtener la fecha final en formato 'YYYY-MM-DD'
        fecha_final_str = fecha_final.strftime('%Y-%m-%d')

        # Ordenar los valores de accionista_de y accionista_a en orden ascendente
        accionista_min = min(cuotas['accionista_de'], cuotas['accionista_a'])
        accionista_max = max(cuotas['accionista_de'], cuotas['accionista_a'])

        existe_cuota = self.env['account.move'].search([
            ('partner_id', '>=', accionista_min),
            ('partner_id', '<=', accionista_max),
            ('invoice_date', '>=', fecha_inicio),
            ('invoice_date', '<=', fecha_final_str),
            ('l10n_latam_document_type_id', '=', 62)
        ])

        registro_existente = self.env['aclm.cuotas'].search([
            ('accionista_de', '=', cuotas['accionista_de']),
            ('accionista_a', '=', cuotas['accionista_a']),
            ('anio_inicio', '=', cuotas['anio_inicio']),
            ('mes_inicio', '=', cuotas['mes_inicio']),
            ('tipo_cuota', '=', cuotas['tipo_cuota']),
            ('cuota_valida', '=', True)
        ], limit=1)

        logging.info("registro_existente")
        logging.info(registro_existente)
        if registro_existente and tipo_cuota == 0 and existe_cuota:
            
            borra_cuota_no_valida = self.env['aclm.cuotas'].search([
                ('accionista_de', '=', cuotas['accionista_de']),
                ('accionista_a', '=', cuotas['accionista_a']),
                ('anio_inicio', '=', cuotas['anio_inicio']),
                ('mes_inicio', '=', cuotas['mes_inicio']),
                ('tipo_cuota', '=', tipo_cuota)
            ])
            logging.info("borra_cuota_no_valida")
            logging.info(borra_cuota_no_valida)
            #borra_cuota_no_valida.unlink()

            logging.info('Ya existen cuotas registradas en el sistema para el periodo. Alguno de los accionistas ya registra cuotas.')
            return 'Ya existen cuotas registradas en el sistema para el periodo. Alguno de los accionistas ya registra cuotas.'
        
        if registro_existente and tipo_cuota == 0 and not existe_cuota:
            
            logging.info('Borrando Cuota Anterior.')
            registro_existente.write({
                'cuota_valida': False,
            })


        # Crear un nuevo registro
        nuevo_registro = self.env['aclm.cuotas'].create({
            'accionista_de': cuotas['accionista_de'],
            'accionista_a': cuotas['accionista_a'],
            'anio_inicio': cuotas['anio_inicio'],
            'mes_inicio': cuotas['mes_inicio'],
            'tipo_cuota': cuotas['tipo_cuota'],
            'numero_cuotas': cuotas['numero_cuotas'],
            'monto_valor_cuota': cuotas['monto_valor_cuota'],
            'docto_autoriza': cuotas['docto_autoriza'],
            'cuota_valida': True,
        })

        return True


    def cron_job_create_invoice_old(self):
        logging.info("llamado crontab cron_job_create_invoice_old() ")
        
        cuotas_pendientes = self.search([
            ('cuota_procesada', '=', False),
            ('cuota_valida', '=', True),
        ])
        
        for registro in cuotas_pendientes:
            try:
                registro.write({'cuota_procesada': True})
                cuotas = {
                    'accionista_de': registro.accionista_de.id,
                    'accionista_a': registro.accionista_a.id,
                    'monto_valor_cuota': registro.monto_valor_cuota,
                    'anio_inicio': registro.anio_inicio,
                    'mes_inicio': registro.mes_inicio,
                    'docto_autoriza': registro.docto_autoriza,
                    'numero_cuotas': registro.numero_cuotas,
                    'tipo_cuota': registro.tipo_cuota
                }
                data_firme = self.generate_data_from_period(cuotas, 'firme')
                logging.info("Creando Cuotas")
                for data_firme_cuota in data_firme:
                    self.create_invoice_old(data_firme_cuota)
                
            except Exception as e:
                # Manejo de la excepción y registro del error
                logging.error("Error al procesar la cuota: %s", str(e))
            
        return True


    def create_invoice_old(self, data_firme_cuota):
        try:
            if data_firme_cuota:
                invoice_line_data = [(0, 0, {
                    'product_id': data_firme_cuota['product_id'],
                    'quantity': 1.0,
                    'name': data_firme_cuota['product_name'],
                    'price_unit': data_firme_cuota['price_unit'],
                    'account_id': data_firme_cuota['account_id'],
                    'tax_ids': [(5, 0, 0)]  # Esto establecerá tax_ids como una lista vacía
                })]

                logging.info("Cuota: %s", data_firme_cuota['name'])
            
                self.env['account.move'].create({
                        'move_type': 'out_invoice',  # Factura de cliente
                        'partner_id': data_firme_cuota['partner_id'],
                        'invoice_date': data_firme_cuota['invoice_date'],
                        'invoice_date_due': data_firme_cuota['invoice_date_due'],
                        'invoice_line_ids': invoice_line_data,
                        'name': data_firme_cuota['name'],
                        'l10n_latam_document_type_id': data_firme_cuota['l10n_latam_document_type_id'],
                    })
                self.env.cr.commit()  # Realizar commit explícito

                return True

            else:
                raise models.ValidationError("Dato Vacio no se registrará")

        except Exception as e:
            logging.error("Error en create_invoice: %s", str(e))


    def cron_job_create_invoice(self):
        logging.info("llamado crontab cron_job_create_invoice() ")

        cuotas_pendientes = self.search([
            ('cuota_procesada', '=', False),
            ('cuota_valida', '=', True),
        ])

        threads = []
        max_threads = 1  # Número máximo de hilos en paralelo

        sem = Semaphore(max_threads)

        for registro in cuotas_pendientes:
            try:
                registro.write({'cuota_procesada': True})
                logging.info("Accionista: %s", registro.accionista_de.name)
                cuotas = {
                    'accionista_de': registro.accionista_de.id,
                    'accionista_a': registro.accionista_a.id,
                    'monto_valor_cuota': registro.monto_valor_cuota,
                    'anio_inicio': registro.anio_inicio,
                    'mes_inicio': registro.mes_inicio,
                    'docto_autoriza': registro.docto_autoriza,
                    'numero_cuotas': registro.numero_cuotas,
                    'tipo_cuota': registro.tipo_cuota
                }
                data_firme = self.generate_data_from_period(cuotas, 'firme')
                logging.info("Creando Cuotas")

                for data_firme_cuota in data_firme:
                    sem.acquire()
                    thread = threading.Thread(target=self.create_invoice, args=(data_firme_cuota, sem))
                    threads.append(thread)
                    thread.start()

                # Esperar a que todos los hilos terminen antes de continuar
                for thread in threads:
                    thread.join()

                threads = []  # Limpiar la lista de hilos después de cada lote

                logging.info("ID: %s", registro.id)
                # Si todo funciona correctamente, actualiza cuota_procesada a True

            except Exception as e:
                # Manejo de la excepción y registro del error
                logging.error("Error al procesar la cuota: %s", str(e))

        return True


    def create_invoice(self, data_firme_cuota, sem):
        
        new_cr = registry(self.env.cr.dbname).cursor()
        new_env = api.Environment(new_cr, self.env.uid, self.env.context)
        try:
            if data_firme_cuota:
                invoice_line_data = [(0, 0, {
                    'product_id': data_firme_cuota['product_id'],
                    'quantity': 1.0,
                    'name': data_firme_cuota['product_name'],
                    'price_unit': data_firme_cuota['price_unit'],
                    'account_id': data_firme_cuota['account_id'],
                    'tax_ids': [(5, 0, 0)]  # Esto establecerá tax_ids como una lista vacía
                })]

                logging.info("Cuota: %s", data_firme_cuota['name'])

                new_env['account.move'].create({
                    'move_type': 'out_invoice',  # Factura de cliente
                    'partner_id': data_firme_cuota['partner_id'],
                    'invoice_date': data_firme_cuota['invoice_date'],
                    'invoice_date_due': data_firme_cuota['invoice_date_due'],
                    'invoice_line_ids': invoice_line_data,
                    'name': data_firme_cuota['name'],
                    'l10n_latam_document_type_id': data_firme_cuota['l10n_latam_document_type_id'],
                })

                return True

            else:
                raise models.ValidationError("Dato Vacio no se registrará")

        except Exception as e:
            logging.error("Error en create_invoice: %s", str(e))

        finally:
            new_cr.commit()
            new_cr.close()
            sem.release()

    def crear_excel(self, data_full_csv):
        # Crea un archivo temporal y luego cierra, dejando una ruta válida para usar
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()

        workbook = xlsxwriter.Workbook(temp_file.name)
        worksheet = workbook.add_worksheet()

        # Encabezado
        worksheet.write('A1', 'Accionista')
        worksheet.write('B1', 'Descrip. Transacción')
        worksheet.write('C1', 'Des')
        worksheet.write('D1', 'Monto Valor Cuota')
        worksheet.write('E1', 'Cantidad')
        worksheet.write('F1', 'Fecha de Cuota')
        worksheet.write('G1', 'Fecha Vcto Cuota')
        worksheet.write('H1', 'Cuota')
        worksheet.write('I1', 'Moneda')

        row = 1
        total_cantidad = 0
        total_cuotas = 0

        for data_excel in data_full_csv:
            #solo para la primera cuota de cada cliente-cod-marco distinto.
            if data_excel['des'] == '1ra':
                total_cantidad  = total_cantidad + float(data_excel['cantidad_acciones'].replace(',', '.'))

            total_cuotas    = total_cuotas + data_excel['cuota_mensual']
            acciones        = float(data_excel['cantidad_acciones'].replace(',', '.'))
            
            worksheet.write(row, 0, str(data_excel['nombre_usuario']))
            worksheet.write(row, 1, str(data_excel['descripcion']))
            worksheet.write(row, 2, str(data_excel['des']))
            worksheet.write(row, 3, "{:,.0f}".format(data_excel['cuota']).replace(',', '.'))
            worksheet.write(row, 4, acciones)
            worksheet.write(row, 5, data_excel['fecha_cuota'])
            worksheet.write(row, 6, data_excel['fecha_vencimiento_cuota'])
            worksheet.write(row, 7, "{:,.0f}".format(data_excel['cuota_mensual']).replace(',', '.'))
            worksheet.write(row, 8, 'CL')
            row += 1

        # PARA CAMPO TOTAL
        row += 1
        worksheet.write(row, 3, 'Total:')
        worksheet.write(row, 4, total_cantidad)
        worksheet.write(row, 6, 'Total:')
        worksheet.write(row, 7, "{:,.0f}".format(total_cuotas).replace(',', '.'))
        
        workbook.close()

        # Lectura del archivo creado y su codificación a base64 para el attachment
        with open(temp_file.name, 'rb') as f:
            byte_data = base64.b64encode(f.read())

        # Eliminamos el archivo temporal después de leerlo
        os.unlink(temp_file.name)

        attachment = self.env['ir.attachment'].create({
            'name': 'cuotas.xlsx',
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


    def cron_job_delete_cuotas_no_validas(self):
        
        delete_registro_existente_valido = self.env['aclm.cuotas'].search([('cuota_valida', '=', False)])
        delete_registro_existente_valido.unlink()