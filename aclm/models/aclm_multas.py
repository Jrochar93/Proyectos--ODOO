from odoo.exceptions import AccessError, UserError, ValidationError
import csv
from odoo import models, fields, api, _

import tempfile
import base64
from io import StringIO
from datetime import datetime
import xlsxwriter
import os

import calendar

import sys


# Lib Config Logger
import logging
logging.basicConfig(filename="/var/log/odoo/odoo-server.log", format='%(asctime)s %(message)s', filemode='w')


class AclmMultas(models.Model):
    _name = 'aclm.multas'
    _description = 'Generación de Multas '


    # ------------------------------------------------------------------ #
    #                   Definición de Funciones Basicas                  #
    # ------------------------------------------------------------------ #

    def name_get(self):
        if self._context.get('display_holding'):
            return [(partner.id, partner.x_studio_holding) for partner in self]
        else:
            return super().name_get()

 
    # Función que obtiene listado de Accionistas - Holding.
    @api.model
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
                    ('id', '>=', accionista_de.id),
                    ('x_studio_accionista', '=', 'Activo')
                ], order='name')
        else:
            usuarios = self.env['res.partner'].search([
                ('x_studio_accionista', '=', 'Activo')
            ], order='name')
        
        return usuarios   


    @api.constrains('fecha_campo')
    def check_fecha(self):
        for record in self:
            if record.fecha_campo < date.today():
                raise models.ValidationError(_("La fecha debe ser mayor o igual a la fecha actual."))

    # ------------------------------------------------------------------ #
    #               Definición de Campos de Modelo                       #
    # ------------------------------------------------------------------ #

    accionista_de   = fields.Many2one('res.partner', string='Accionista de', domain=[('x_studio_accionista', '=', 'Activo'),])
    accionista_a    = fields.Many2one('res.partner', string='Accionista a', domain=[('x_studio_accionista', '=', 'Activo')])
    
    holding_de      = fields.Many2one('res.partner', string='Holding de', domain=[('x_studio_accionista', '=', 'Activo')],context={'display_holding': True},)
    holding_a       = fields.Many2one('res.partner', string='Holding a', domain=[('x_studio_accionista', '=', 'Activo')],context={'display_holding': True},)

    pctj_multa      = fields.Integer(string='% Multa', required=True)
    fecha_inicio = fields.Date(string='Fecha Inicio', required=True)

    docto_autoriza  = fields.Text(string='Docto Autoriza', required=True)
    
    @api.model
    def ultimo_dia_del_mes(self, fecha, date_format='%Y-%m-%d'):
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        ultimo_dia = calendar.monthrange(fecha_obj.year, fecha_obj.month)[1]
        fecha_final = fecha_obj.replace(day=ultimo_dia)
        fecha_final_str = fecha_final.strftime(date_format)

        return fecha_final_str
    
    @api.model
    def cambiar_formato_fecha(self, fecha, formato_salida='%d-%m-%Y'):
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        fecha_nuevo_formato = fecha_obj.strftime(formato_salida)

        return fecha_nuevo_formato

    @api.model
    def valida_pagos_no_conciliados(self, partner_id):
        pagos_obj = self.env['account.payment']
        pagos_conciliados = pagos_obj.search([
            ('is_reconciled', '=', False),
            ('partner_id', '=', partner_id)
        ], limit=1)
        
        if not pagos_conciliados:
            return False
        
        return pagos_conciliados


    @api.model
    def buscar_facturas_no_pagadas(self, partner_id, fecha):
        fecha_objetivo = datetime.strptime(fecha, '%Y-%m-%d').date()
        factura_obj = self.env['account.move']
        facturas_no_pagadas = factura_obj.search([
            ('invoice_date_due', '<=', fecha_objetivo), 
            ('move_type', '=', 'out_invoice'),
            ('partner_id', '=', partner_id),
            ('payment_state','!=','paid')
        ])

        logging.info("out_invoice - invoice_date_due <=: %s", fecha_objetivo)
        logging.info("out_invoice - partner_id : %s", partner_id)
        logging.info("out_invoice - facturas_no_pagadas : %s", facturas_no_pagadas)
        
        total_residual  = 0
        total_pagos_facturados  = 0
        residual_linea    = []  # Lista para almacenar los datos
        for factura in facturas_no_pagadas:
            total_residual += factura.amount_residual_signed
            '''
            pagos = self.env['account.move'].search([
                ('ref', '=', factura.payment_reference),
                ('date', '<=', fecha_objetivo), 
                ('move_type', '=', 'entry'),
                ('partner_id', '=', partner_id)
            ])

            logging.info("entry - date  <=: %s", fecha_objetivo)
            logging.info("entry - ref  =: %s", factura.payment_reference)
            logging.info("entry - partner_id : %s", partner_id)

            pagos_facturados = sum(pago.amount_total_signed for pago in pagos)
            logging.info("pagos_facturados (SUM) : %s", pagos_facturados)
            if pagos_facturados > 0:
                total_residual = factura.amount_total_signed - pagos_facturados
                logging.info("factura.amount_total_signed : %s", factura.amount_total_signed)
                logging.info("pagos_facturados : %s", pagos_facturados)
                logging.info("total_residual > 0 (factura.amount_total_signed - pagos_facturados) : %s", total_residual)
            else:
                total_residual = factura.amount_total_signed
                logging.info("total_residual < 0  : %s", total_residual)
            logging.info("\n")
            residual_linea.append(total_residual)

        logging.info("\n\n")
        total_residual = 0
        for linea in residual_linea:
            if linea > 0:
                total_residual += linea
                logging.info("MAYOR 0 LINEA : %s", linea)
            else:
                total_residual += linea
                logging.info("MENOR 0 LINEA : %s", linea)
        #total_residual = sum(factura.amount_residual_signed for factura in facturas_no_pagadas)
        '''
        logging.info("FINAL TOTAL RESIDUAL : %s", total_residual)
        
        return total_residual


    @api.model
    def generate_data_from_period(self, datos_multas, tipo_req):

        data_csv    = []  # Lista para almacenar los datos
        porcentaje              = datos_multas['pctj_multa']
        fecha_inicio_multa      = datos_multas['fecha_inicio']
        usuarios    = self._get_users_between_params(datos_multas['accionista_de'],datos_multas['accionista_a'],'accionista')
        logging.info("len(usuarios): %s",len(usuarios))
        for usuario in usuarios:
            total_residual_usuario  = self.buscar_facturas_no_pagadas(usuario.id, fecha_inicio_multa)
            monto_multa             = (total_residual_usuario * porcentaje) / 100
            
            if(tipo_req == 'borrador'):
                logging.info("Total residual: %s", fecha_inicio_multa)
                
                fecha_multa             = self.cambiar_formato_fecha(str(fecha_inicio_multa))
                fecha_vencimiento_multa = self.ultimo_dia_del_mes(str(fecha_inicio_multa))
                fecha_vencimiento       = self.cambiar_formato_fecha(str(fecha_vencimiento_multa))
                #description             = 'Multa ' + str(fecha_multa) +" "+ usuario.x_studio_cod_de_marco
                description             = 'Multa ' + str(fecha_multa)
                if (total_residual_usuario > 0 or monto_multa > 0):
                    data_csv.append({
                        'descripcion': description,
                        'nombre_usuario': usuario.name,
                        'codigo_marco': usuario.x_studio_cod_de_marco,
                        'fecha_vencimiento_multa' : fecha_vencimiento,
                        'fecha_multa' : fecha_multa,
                        'porcentaje' : porcentaje,
                        'monto_vencimiento': total_residual_usuario,
                        'monto_multa':monto_multa,
                        'cantidad_acciones': usuario.x_studio_cantidad_1,
                    })

            if(tipo_req == 'firme'):
                    usuario_pago_conciliado = self.valida_pagos_no_conciliados(usuario.id)
                    if usuario_pago_conciliado == False :

                        #description             = 'Multa ' +datos_multas['docto_autoriza']+ str(fecha_inicio_multa) +" "+ usuario.x_studio_cod_de_marco
                        description             = 'Multa ' + str(fecha_inicio_multa) +" "+ usuario.x_studio_cod_de_marco
                        #logging.info("DESC: %s", description)
                        fecha_vencimiento_multa = self.ultimo_dia_del_mes(str(fecha_inicio_multa))
                        total_residual_usuario_porcentmulta = "{:,.0f}".format(total_residual_usuario).replace(',', '.')
                        x_studio_porcentmulta   = str(porcentaje)+'%'+" x $"+str(total_residual_usuario_porcentmulta)
                        if ( monto_multa > 0):
                            data_csv.append({
                                'name': description,
                                'invoice_date_due' : fecha_vencimiento_multa,
                                'invoice_date' : fecha_inicio_multa,
                                'partner_id' : usuario.id,
                                'l10n_latam_document_type_id': 2, #Multa l10n_latam_document_type
                                'x_studio_tipo_docto_1': 2,#Multa product_template
                                'price_unit': monto_multa,
                                'x_studio_porcentmulta' : x_studio_porcentmulta
                            })
                        else:
                            if len(usuarios) ==1:
                                raise models.ValidationError('El monto a generar de la multa es 0!.')
                    else:
                        raise models.ValidationError('Existen pagos no asociados, favor conciliar pagos para el usuario: {} (Monto: {})'.format(usuario.name, usuario_pago_conciliado.amount))
        return data_csv


    @api.model
    def crear_excel(self, data_full_csv):
        # Crea un archivo temporal y luego cierra, dejando una ruta válida para usar
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()

        workbook = xlsxwriter.Workbook(temp_file.name)
        worksheet = workbook.add_worksheet()

        # Encabezado
        worksheet.write('A1', 'Accionista')
        worksheet.write('B1', 'Descrip. Transacción')
        worksheet.write('C1', 'Monto Deudor Vencido')
        worksheet.write('D1', '% Multa')
        worksheet.write('E1', 'Cantidad')
        worksheet.write('F1', 'Fecha de Multa')
        worksheet.write('G1', 'Fecha Vcto Multa')
        worksheet.write('H1', 'Monto Multa Aplicado')
        worksheet.write('I1', 'Moneda')

        row = 1
        total_cantidad = 0
        total_monto_vencido = 0
        total_multas = 0
        for data_excel in data_full_csv:
            total_cantidad = total_cantidad + float(data_excel['cantidad_acciones'].replace(',', '.'))
            total_monto_vencido = total_monto_vencido + data_excel['monto_vencimiento']
            total_multas = total_multas + data_excel['monto_multa']
            
            worksheet.write(row, 0, str(data_excel['nombre_usuario']))
            worksheet.write(row, 1, str(data_excel['descripcion']))
            worksheet.write(row, 2, "{:,.0f}".format(data_excel['monto_vencimiento']).replace(',', '.'))
            worksheet.write(row, 3, data_excel['porcentaje'])
            worksheet.write(row, 4, float(data_excel['cantidad_acciones'].replace(',', '.')))
            worksheet.write(row, 5, data_excel['fecha_multa'])
            worksheet.write(row, 6, data_excel['fecha_vencimiento_multa'])
            worksheet.write(row, 7, "{:,.0f}".format(data_excel['monto_multa']).replace(',', '.'))
            worksheet.write(row, 8, 'CL')
            row += 1

        # PARA CAMPO TOTAL
        row += 1
        worksheet.write(row, 1, 'Total:')
        worksheet.write(row, 2, "{:,.0f}".format(total_monto_vencido).replace(',', '.').replace(',', '.'))
        worksheet.write(row, 3, 'Total:')
        worksheet.write(row, 4, total_cantidad)
        worksheet.write(row, 6, 'Total:')
        worksheet.write(row, 7, "{:,.0f}".format(total_multas).replace(',', '.').replace(',', '.'))
        
        workbook.close()

        # Lectura del archivo creado y su codificación a base64 para el attachment
        with open(temp_file.name, 'rb') as f:
            byte_data = base64.b64encode(f.read())

        # Eliminamos el archivo temporal después de leerlo
        os.unlink(temp_file.name)

        attachment = self.env['ir.attachment'].create({
            'name': 'multas.xlsx',
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
    def generar_borrador(self, *args, **kwargs):

        accionista_de   = self.env.context.get('accionista_de')
        accionista_a    = self.env.context.get('accionista_a')
        holding_de      = self.env.context.get('holding_de')
        holding_a       = self.env.context.get('holding_a')
        fecha_inicio    = self.env.context.get('fecha_inicio')
        docto_autoriza  = self.env.context.get('docto_autoriza')
        pctj_multa      = self.env.context.get('pctj_multa')

        multas = {
            'accionista_de': accionista_de,
            'accionista_a': accionista_a,
            'holding_de'    : holding_de,
            'holding_a'     : holding_a,
            'fecha_inicio': fecha_inicio,
            'docto_autoriza': docto_autoriza,
            'pctj_multa': pctj_multa
        }
        
        data_borrador = self.generate_data_from_period(multas, 'borrador')
        return self.crear_excel(data_borrador)


    @api.model
    def create_invoice(self, data_firme):

        if data_firme:

            for data_firme_cuota in data_firme:

                # Realizar la búsqueda para verificar si ya existe un registro similar
                existing_invoice = self.env['account.move'].search([
                    ('partner_id', '=', data_firme_cuota['partner_id']),
                    ('name', '=', data_firme_cuota['name']),
                    ('invoice_date', '=', data_firme_cuota['invoice_date']),
                    ('invoice_date_due', '=', data_firme_cuota['invoice_date_due']),
                    ('l10n_latam_document_type_id', '=', data_firme_cuota['l10n_latam_document_type_id'])
                ], limit=1)
                
                if existing_invoice:
                    raise models.ValidationError('Ya existe un registro con los mismos datos: {}'.format(existing_invoice.name))


                product_template_id = self.env['product.template'].search([('x_studio_tipo_docto_1', 'ilike', f"{data_firme_cuota['x_studio_tipo_docto_1']}%")], limit=1)
                if not product_template_id:
                    raise models.ValidationError('No se encontró ningún producto Template con ese tipo de documento.')

                product_id = self.env['product.product'].search([('product_tmpl_id', '=', product_template_id.id)], limit=1)
                if not product_id:
                    raise models.ValidationError('No se encontró ningún producto con ese tipo de documento.')
                
                partner_id = self.env['res.partner'].search([('id', '=', data_firme_cuota['partner_id']), ('x_studio_accionista', '=', 'Activo')], limit=1)
                if not partner_id:
                    raise models.ValidationError('No se encontró el usuario '+data_firme_cuota['partner_id']+' para la creación de la cuota')
                
                document_type_id = self.env['l10n_latam.document.type'].search([('code' ,'=',data_firme_cuota['l10n_latam_document_type_id'])], limit=1)
                if not document_type_id:
                    raise models.ValidationError('No se encontró el tipo documento '+data_firme_cuota['l10n_latam_document_type_id']+' para la creación de la cuota')
                    
                invoice_line_data = [(0, 0, {
                    'product_id'    : product_id.id,
                    'quantity'      : 1.0,
                    'name'          : product_id.name,
                    'price_unit'    : data_firme_cuota['price_unit'],
                    #'price_unit': product_id.list_price,
                    'account_id'    : product_id.property_account_income_id.id or product_id.categ_id.property_account_income_categ_id.id,
                    'tax_ids': [(5, 0, 0)] # Esto establecerá tax_ids como una lista vacía
                    })]

                invoice = self.env['account.move'].create({
                    'move_type'                     : 'out_invoice', # Factura de cliente
                    'partner_id'                    : partner_id.id,
                    'invoice_date'                  : data_firme_cuota['invoice_date'],
                    'invoice_date_due'              : data_firme_cuota['invoice_date_due'],
                    'invoice_line_ids'              : invoice_line_data,
                    'name'                          : data_firme_cuota['name'],
                    'l10n_latam_document_type_id'   : document_type_id.id,
                    'x_studio_porcentmulta'         : data_firme_cuota['x_studio_porcentmulta']
                })

            return True

        else:
            raise models.ValidationError("No hay saldos adeudados para generar la Multa.")


    @api.model
    def generar_firme(self, *args, **kwargs):
        
        accionista_de   = self.env.context.get('accionista_de')
        accionista_a    = self.env.context.get('accionista_a')
        holding_de      = self.env.context.get('holding_de')
        holding_a       = self.env.context.get('holding_a')
        fecha_inicio    = self.env.context.get('fecha_inicio')
        docto_autoriza  = self.env.context.get('docto_autoriza')
        pctj_multa      = self.env.context.get('pctj_multa')

        multas = {
            'accionista_de': accionista_de,
            'accionista_a': accionista_a,
            'holding_de'    : holding_de,
            'holding_a'     : holding_a,
            'fecha_inicio': fecha_inicio,
            'docto_autoriza': docto_autoriza,
            'pctj_multa': pctj_multa
        }

        data_firme = self.generate_data_from_period(multas,'firme')
        if self.create_invoice(data_firme):
            self.create(multas)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Éxito',
                    'message': 'Todas las Multas han sido creadas exitosamente.',
                    'sticky': False,  # True si quieres que sea pegajoso y no desaparezca automáticamente
                },
            }
        else:

            raise models.ValidationError("Hubo un error y no fue posible crear las multas.")
        
    @api.model
    def generar_firme_automatico(self, *args, **kwargs):

        ultimo_registro = self.env['aclm.multas'].search([], order='id desc', limit=1)
        mes_siguiente   = datetime.now()
        multas = {
            'accionista_de' : ultimo_registro.accionista_de,
            'accionista_a'  : ultimo_registro.accionista_a,
            'holding_de'    : ultimo_registro.holding_de,
            'holding_a'     : ultimo_registro.holding_a,
            'fecha_inicio'  : mes_siguiente ,
            'docto_autoriza': ultimo_registro.docto_autoriza,
            'pctj_multa'    : ultimo_registro.pctj_multa
        }

        data_firme = self.generate_data_from_period(multas,'firme')

        if self.create_invoice(data_firme):
            self.create(multas)
        else:
            raise models.ValidationError("")

        return true