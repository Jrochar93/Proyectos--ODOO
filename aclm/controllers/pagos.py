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
from http import HTTPStatus


# Lib Config Logger
import logging 
logging.basicConfig(filename="/var/log/odoo/odoo-server.log", format='%(asctime)s %(message)s', filemode='w') 

class CuentaCorriente(http.Controller):
    logger = logging.getLogger()
            

    @http.route('/aclm/pagos', type='http', auth='none', methods=['GET','OPTIONS'], csrf=False,cors="*")
    def get_pagos(self, **kw):

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

        
        partner_id= kw.get('partner_id')

        if not company_id:
            return http.Response('No es posible obtener la empresa del usuario.', status=401)

        if not partner_id:
                return http.Response('Debe ingresar partner_id.', status=401)
            
        pagos_pendientes = self.get_pagos_pendientes(partner_id)
        
        if pagos_pendientes:
            return http.Response(pagos_pendientes, status=200, content_type='application/json')
        else:
            return http.Response(json.dumps([]), status=404, content_type='application/json')

    @http.route('/aclm/pagos', type='http', auth='none', methods=['POST'], csrf=False,cors="*")
    def post_registra_pagos(self, **kw):
        logging.info('post_registra_pagos funcion')
        if request.httprequest.data:
            json_data       = json.loads(request.httprequest.get_data(as_text=True))
            rut    = json_data.get('rut')
            total = json_data.get('total')
            transaccion = json_data.get('transaccion')
            total_pagado = json_data.get('total_pagado')
            accionistasdata     = json_data.get('accionistas')
            

        auth = request.httprequest.headers.get('Authorization', None)
        if not auth:
            return http.Response('Credenciales no proporcionadas.', status=401)

        try:
            auth = base64.b64decode(auth.split(' ')[1]).decode('utf-8')
            username, password = auth.split(':')
        except (TypeError, ValueError):
            return http.Response('Credenciales no válidas.', status=401)
     
        if not rut:
            response = {
                    'status_code': 409,
                    'message': "Debe ingresar rut.",
                }
            return Response(json.dumps(response), status=409, mimetype='application/json')
        if not total:
            response = {
                    'status_code': 409,
                    'message': "Debe ingresar total.",
                }
            return Response(json.dumps(response), status=409, mimetype='application/json')
        if not total_pagado:
            response = {
                    'status_code': 409,
                    'message': "Debe ingresar total pagado.",
                }
            return Response(json.dumps(response), status=409, mimetype='application/json')
        
        if not transaccion:
            response = {
                    'status_code': 409,
                    'message': "Debe ingresar el numero de transaccion.",
                }
            return Response(json.dumps(response), status=409, mimetype='application/json')
        #logging.info('rut')
        #logging.info(rut)
        #logging.info('total')
        #logging.info(total)

        if isinstance(accionistasdata, str):  # if lista_pagos is a string, convert it to a list of dictionaries
            accionistasdata = json.loads(accionistasdata)
        
        if not accionistasdata:
            return self.response_error("Debe ingresar el listado de accionistas a pagar.")
            #return http.Response('Debe ingresar el listado de pagos.', status=401)
        

        db_name = 'ACLM-DEV01'
        if not db_name:
            return http.Response('Debe ingresar la DB.', status=401)
        else:
            request.session.db = db_name
            env = request.env
            uid = request.session.authenticate(request.db, username, password)

        if not uid:
            return self.response_error("Credenciales inválidas.")

        company_id = request.env.user.company_id.id
        
        if not company_id:
            return self.response_error("No es posible obtener la empresa del usuario.")
    
        #Se busca el payment_method_line que corresponda al payment_method=1 y name=Web
        payment_method_id=1
        domain = [
                        ('payment_method_id', '=', payment_method_id),
                        ('name','=','Web')
                    ]
        payment_method_line   = request.env['account.payment.method.line'].search(domain)
        payment_method_line_id=payment_method_line[0]['id']

        pago_validado = self.validaPagos(total_pagado, accionistasdata)
        AccountMove = request.env['account.move']
        AccountPayment = request.env['account.payment']
        if pago_validado:
            for accionistadata in accionistasdata:

                cod_marco = accionistadata['cod_marco']
        
                #logging.info(cod_marco)
                accionistas_por_cod_marco = self.get_accionista(cod_marco)
                if accionistas_por_cod_marco:
                    accionista=accionistas_por_cod_marco[0]

                    subtotal = accionistadata['subtotal']

                    lista_pagos = accionistadata['lista_pagos']
                    logging.info('lista_pagos')
                    logging.info(lista_pagos)

                    cantidad_pagos = len(lista_pagos)
                    logging.info('cantidad_pagos')
                    logging.info(cantidad_pagos)
                    if cantidad_pagos ==1:
                        pago = lista_pagos[0]
                        logging.info('pago')
                        logging.info(pago)
                        move_id = pago.get('id')
                        logging.info('move_id')
                        logging.info(move_id)
                        monto_pago = pago.get('monto_pago')
                        logging.info('monto_pago')
                        logging.info(monto_pago)

                        # Valida existencia de account moves
                        account_move = AccountMove.browse(move_id)
                        if not account_move.exists():
                            #TODO: si no existe el id de cuota, se debe crear el pago si o si
                            return self.response_error("El ID de cuota: "+ str(move_id)+" no existe.")

                        #Se validan pagos a monto cerrado, no abonos ni pre-pagos.
                        account_move = AccountMove.browse(move_id)
                        if account_move.amount_residual_signed != monto_pago:
                            
                            return self.response_error("El monto a pagar es: "+ str(account_move.amount_residual_signed)+", se esta pagando "+str(monto_pago)+". El monto debe ser exacto")

                        # Si es borrador se publica el documento
                        self.verifica_post(account_move)
                        

                        
                        # Se crea y Registra el Pago en Modulo de Pagos
                        logging.info('trata de crear el action de pago a partir de la cuota')
                        action = account_move.action_register_payment()
                        logging.info('trata de crear el pago')
                        PaymentRegister = request.env['account.payment.register']
                        payment_register = PaymentRegister.with_context(action['context']).create({})
                        payment_register.write({
                            'amount': monto_pago,
                            'payment_date': fields.Date.today(),
                            'payment_method_line_id': payment_method_line_id #METODO 6 WEB, METODO 3 MANUAL ACLM
                            #'payment_reference': transaccion
                        })
                        logging.info('escribio el pago')
                        #payment_register.action_create_payments()    
                        action=payment_register.action_create_payments()
                        new_payment_id=action['res_id']
                        new_payment=AccountPayment.browse(new_payment_id)
                        new_payment.write({'payment_reference': transaccion})
                    else:
                        logging.info('accionista[id]')
                        logging.info(accionista['id'])
                        
                        payment = request.env['account.payment'].create({
                            'partner_type': 'customer',  # O 'supplier' si se trata de un proveedor
                            'partner_id': accionista['id'],
                            'payment_type': 'inbound',   # O 'outbound' si es un proveedor
                            'payment_method_id': payment_method_id,  # Reemplaza con el ID del método de pago
                            'payment_method_line_id': payment_method_line_id ,
                            'amount': subtotal,
                            'date': fields.Date.today(),
                            'payment_reference': transaccion
                        })

                        # Realizar el pago
                        payment.action_post()
                        
                        logging.info('payment')
                        logging.info(payment)

                        payment_id =payment['id']
                        
                        mv_line_ids = []
                        #Tomar la account_move_line del pago  (la ultima)
                        #payment_id = 626
                        domain = [
                            ('payment_id', '=', payment_id),
                            ('credit','>',0)
                        ]

                        # Realiza la búsqueda en el modelo account.move
                        moves_payment   = request.env['account.move.line'].search(domain)
                        logging.info('moves_payment')
                        logging.info(moves_payment)
                        mv_line_ids.append (moves_payment[0]['id'])


                        #Validar que cada cuota exista y que esté posteado

                        suma_subtotal=0
                        for pago in lista_pagos:
                            move_id = pago.get('id')
                            logging.info('move_id')
                            logging.info(move_id)
                            monto_pago = pago.get('monto_pago')
                            logging.info('monto_pago')
                            logging.info(monto_pago)
                            
                            account_move = AccountMove.browse(move_id)
                            if not account_move.exists():
                                return self.response_error("El ID de cuota: "+ str(move_id)+" no existe.")
                            # Si es borrador se publica el documento
                            self.verifica_post(account_move)
                            logging.info('account_move')
                            logging.info(account_move)

                            if account_move.amount_residual_signed != monto_pago:
                                return self.response_error("El monto a pagar es: "+ str(account_move.amount_residual_signed)+", se esta pagando "+str(monto_pago)+". El monto debe ser exacto")
                            #Tomar todas las account_move_line de cada cuota
                            domain = [
                                ('move_id', '=', move_id),
                                ('debit','>',0)
                            ]
                            moves_cuota   = request.env['account.move.line'].search(domain)
                            logging.info('moves_cuota')
                            logging.info(moves_cuota)
                            

                            mv_line_ids.append (moves_cuota[0]['id'])
                        logging.info('mv_line_ids')
                        logging.info(mv_line_ids)
                        # Realiza la búsqueda en el modelo account.move
                        
                        
                        account_reconciliation = request.env['account.reconciliation.widget']
                        #respuesta = cuponera.generar_cuponera_general(my_json['accionistas'][0]['id'],"base64")
                        data = [{"id": '',"type": '',"mv_line_ids": mv_line_ids,"new_mv_line_dicts": []}]
                        result = account_reconciliation.process_move_lines(data)
            response_data = {
                'message': 'Pagos validados.',
                'status': HTTPStatus.OK.value
            }

            response = http.Response(
                status=HTTPStatus.OK,
                headers={
                    'Content-Type': 'application/json',
                    'cors_enable': 'true',
                    'proxy_mode': 'true'
                },
                response=json.dumps(response_data).encode('utf-8')
            )
            return response
        
        else:
             #El pago no coincide. Se crea 1 solo pago al primer accionista de la lista

            accionistadata = accionistasdata[0]
            cod_marco = accionistadata['cod_marco']
            #logging.info(cod_marco)
            accionistas_por_cod_marco = self.get_accionista(cod_marco)
            if accionistas_por_cod_marco:
                accionista=accionistas_por_cod_marco[0]

                payment = request.env['account.payment'].create({
                    'partner_type': 'customer',  # O 'supplier' si se trata de un proveedor
                    'partner_id': accionista['id'],
                    'payment_type': 'inbound',   # O 'outbound' si es un proveedor
                    'payment_method_id': payment_method_id,  # Reemplaza con el ID del método de pago
                    'payment_method_line_id': payment_method_line_id ,
                    'amount': total_pagado,
                    'date': fields.Date.today(),
                    'payment_reference': transaccion
                })

                logging.info('payment')
                logging.info(payment)    

                payment.write({'ref': 'Pago no coincide con el total para el rut '+rut})
            response_data = {
                    'message': 'Pago no coincide con el total.',
                    'status': HTTPStatus.OK.value
                }

            response = http.Response(
                    status=HTTPStatus.OK,
                    headers={
                        'Content-Type': 'application/json',
                        'cors_enable': 'true',
                        'proxy_mode': 'true'
                    },
                    response=json.dumps(response_data).encode('utf-8')
                )
            return response
        

    def validaPagos(self, total_pagado, accionistasdata):
        
        logging.info('total_pagado')
        logging.info(total_pagado)
        logging.info('accionistasdata')
        logging.info(accionistasdata)
        sumaSubTotales = 0
        for accionistadata in accionistasdata:
            cod_de_marco = accionistadata['cod_marco']
            subtotal = accionistadata['subtotal']
            sumaSubTotales +=subtotal

            lista_pagos = accionistadata['lista_pagos']
            sumaActualPago=0
            for pago in lista_pagos:
                actual_pago = pago['monto_pago']
                sumaActualPago+=actual_pago
            logging.info('sumaActualPago')
            logging.info(sumaActualPago)
            if sumaActualPago != subtotal:
                logging.info('no coincide la suma de los montos de pago con el subtotal para el cod de marco %s', cod_de_marco)
                return False    
        logging.info('sumaSubTotales')
        logging.info(sumaSubTotales)
        if(sumaSubTotales!=total_pagado):
            logging.info('no coincide la suma de los subtotales con el total pagado')
            return False

        return True

    def verifica_post(self, account_move):
        if account_move.state == 'draft':
            logging.info('se postea')
            account_move.action_post()

    def response_error(self, message):
        response = {
        'status_code': 409,
        'message': message,
        }
        return Response(json.dumps(response), status=409, mimetype='application/json')

    def get_pagos_pendientes(self, partner_id):
        partner_id_int = int(partner_id)  # Convertir a entero
        order = 'date ASC, l10n_latam_document_type_id ASC'  # Orden ascendente por fecha e ID de documento
        filter_value = [('partner_id', '=', partner_id_int), ('payment_state', '=', 'not_paid'), ('payment_id', '=', False)]

        pagos = request.env['account.move'].search_read(filter_value, ['id','name', 'amount_total', 'l10n_latam_document_type_id', 'invoice_date_due', 'date'],order = order)
        pagos_pend = [{'id': data['id'],'name': data['name'], 'amount_total': data['amount_total'], 'l10n_latam_document_type_id': data['l10n_latam_document_type_id'][1] if data['l10n_latam_document_type_id'] else '', 'invoice_date_due': data['invoice_date_due'].strftime('%Y-%m-%d') if data['invoice_date_due'] else '', 'date': data['date'].strftime('%Y-%m-%d') if data['date'] else ''} for data in pagos if 'name' in data]
        response_data = {
            'pagos_pendientes': pagos_pend
        }
        response_body = json.dumps(response_data).encode('utf-8')
        return response_body
    
    def get_accionista(self, cod_de_marco):
        logging.info('cod_de_marco')
        logging.info(cod_de_marco)
        filter_value = [('x_studio_cod_de_marco', '=', cod_de_marco), ('x_studio_accionista', '=', 'Activo')]
        accionistas = request.env['res.partner'].search_read(filter_value, ['id'])
        return accionistas