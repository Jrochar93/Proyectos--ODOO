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

        
    @http.route('/aclm/cuentacorriente', type='http', auth='none', methods=['GET','OPTIONS'], csrf=False,cors="*")
    def get_ws_cuentacorriente(self, **kw):
        #valida parametros envio
        tipo = kw.get('tipo')

        status_code = 200
        message = 'Generando Cuenta Corriente'
        
        rut=kw.get('rut')
        fecha_de = kw.get('fecha_de')
        fecha_a = kw.get('fecha_a')

        #valida parametros envio
        if request.httprequest.data:
            json_data       = json.loads(request.httprequest.get_data(as_text=True))
            rut    = json_data.get('rut', rut)
        if rut == None:    
            message = 'Rut es requerido.'
            status_code = 401

        if fecha_de == None:    
            message = 'Fecha desde es requerido.'
            status_code = 401
        if fecha_a == None:    
            message = 'Fecha hasta es requerido.'
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
        
        model_reportes = request.env['aclm.reportes']

        reportes = {
            'rut': rut,
            'fecha_inicio': fecha_de,
            'fecha_final': fecha_a,
            'solicita': 'base64'
        }
        report_pdf_base64_sindecode = model_reportes.generar_borrador_general(reportes)

        if(tipo=="cartola"):
            report_pdf_base64_sindecode = model_reportes.generar_borrador_general(reportes)
        elif (tipo=="abierto"):
            report_pdf_base64_sindecode = model_reportes.generar_saldo_abierto_general(reportes)        
        else:
            return http.Response('Tipo reporte no válido.', status=401)
        report_pdf_base64=report_pdf_base64_sindecode.decode('utf-8')

        response_data = {
            'report_pdf_base64': report_pdf_base64
        }

        response_body = json.dumps(response_data) 

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