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

class CuentaCorriente(http.Controller):
    logger = logging.getLogger()


    @http.route('/aclm/cuponera', type='http', auth='none', methods=['GET','OPTIONS'], csrf=False,cors="*")
    def get_ws_cuponera(self, **kw):
        #valida parametros envio
        status_code = 200
        message = 'Generando Cuponera'
        
        #valida parametros envio
        rut_accionista = kw.get('rut_accionista')
        if rut_accionista == None:    
            message = 'El Rut es requerido.'
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
        '''
        accionistas = self.generate_accionistas(rut_accionista) 
        logging.info('accionistas')
        logging.info(accionistas)
        my_json = json.loads(accionistas.decode('unicode_escape'))
        accionistas_ids = [registro['id'] for registro in my_json['accionistas']]
        logging.info('accionistas_ids')
        logging.info(accionistas_ids)
        '''
        
        cuponera = request.env['aclm.cuponera']
        #respuesta = cuponera.generar_cuponera_general(my_json['accionistas'][0]['id'],"base64")
        #respuesta = cuponera.generar_cuponera_general(accionistas_ids,"base64")
        #logging.info("CIR-respuesta->"+str(respuesta))
        respuesta = cuponera.generar_cuponera_rut(rut_accionista,"base64")
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
    
    '''

    def generate_accionistas(self, rut_accionista):
        filter_value = [('vat', '=', rut_accionista), ('x_studio_accionista', '=', 'Activo')]
        accionistas = request.env['res.partner'].search_read(filter_value, ['x_studio_holding'])
        
        if accionistas:
            x_studio_holding = accionistas[0]['x_studio_holding']  # Obtener el valor de vat del primer registro encontrado
            filter_value = [('x_studio_holding', '=', x_studio_holding), ('x_studio_accionista', '=', 'Activo')]
            accionistas = request.env['res.partner'].search_read(filter_value, ['id'])

        response_data = {
            'accionistas': accionistas
        }
        response_body = json.dumps(response_data).encode('utf-8')
        return response_body
    '''