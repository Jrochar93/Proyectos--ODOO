# -- coding: utf-8 --
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

# Lib Call Webservice
import requests
import json

# Lib Config Logger
import logging
logging.basicConfig(filename="/var/log/odoo/odoo-server.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')


class InvoiceGetfel(models.Model):
    _inherit = 'account.move'

    logger = logging.getLogger()

    def descarga_bcn_getdte(self):
        getdte_amb_id = self.env.company.ambiente_portal
        getdte_emp_id = self.env.company.empresa_portal
        url_portal_api = self.env.company.url_portal
        getdte_user = self.env.company.usuario_portal
        getdte_pass = self.env.company.contrasena
        getdte_odoo_company_id = 2
        recepcion_inicio = "2024-01-22"

        log_message = f"Conexion PORTAL - Ambiente: {getdte_amb_id}, Empresa: {getdte_emp_id}, URL: {url_portal_api}, Usuario: {getdte_user}, Password: {getdte_pass}\n"
        logging.info(log_message)

        api_url_login = url_portal_api + "/api/login"
        headers = {"Content-Type": "application/json"}
        login_data = {"ambiente_id": getdte_amb_id, "empresa_id": getdte_emp_id, "usuario": getdte_user,
                      "contrasena": getdte_pass}

        login_response = requests.post(api_url_login, json=login_data, headers=headers)
        login_response.raise_for_status()
        login_data_resp = login_response.json()
        res_json = json.dumps(login_data_resp)
        logging.info("LOGIN: " + str(res_json) + "\n")

        if login_response.status_code == 200:
            token = login_data_resp['token']['token']
            api_url_documentos = url_portal_api + "/api/documentos"
            headers = {"Content-Type": "application/json"}

            company_id = self.env['res.company'].browse(self.env.company.id)
            country_code = company_id.account_fiscal_country_id.code if company_id.account_fiscal_country_id else False

            logging.info('country_code')
            logging.info(country_code)

            if country_code == 'CL':
                logging.info('aquiii estoy')
                data = {
                    "token": token,
                    "tipo_ingreso": "EMITIDO",
                    "xml_descargado": 0,
                    "emision_inicio": recepcion_inicio
                }
                logging.info("ODOO DOCUMENTO : " + str(data) + "\n")

                response = requests.get(api_url_documentos, json=data, headers=headers)
                response.raise_for_status()
                data_resp = response.json()

                # Handle the response data
                if 'respuesta' in data_resp and 'codigo' in data_resp['respuesta']:
                    if data_resp['respuesta']['codigo'] == 0:
                        # API request successful
                        logging.info("API request successful")
                        logging.info(data_resp)

                        # Process the data and create invoices
                        invoices = self.create_invoices_from_api_response(data_resp)

                        # Further processing or logging as needed
                        logging.info(f"Created {len(invoices)} invoices")

    def create_invoices_from_api_response(self, data_resp):
        invoices = []

        for invoice_detail in data_resp.get('datos', {}).get('detalle', []):
            doc_folio = invoice_detail.get('doc_folio')

            # Check if an invoice with the same identifier already exists
            existing_invoice = self.env['account.move'].search([('ref', '=', doc_folio)], limit=1)

            if not existing_invoice:
                # Invoice does not exist, create a new one
                doc_tipo_dte_desc = invoice_detail.get('doc_tipo_dte_desc')
                doc_emisor_razonsocial = invoice_detail.get('doc_emisor_razonsocial')
                doc_monto_total = invoice_detail.get('doc_monto_total')

                # Replace with the actual partner_id based on your data
                partner = self.env['res.partner'].search([('name', '=', doc_emisor_razonsocial)], limit=1)

                # Replace with the actual journal_id based on your data
                journal_name = 'Facturas de cliente'  # Replace with the actual name of your journal
                journal = self.env['account.journal'].search([('name', '=', journal_name), ('l10n_latam_use_documents', '!=', True),('company_id.id', '!=', '1')], limit=1)

                if not partner or not journal:
                    # If partner or journal is not found, log an error and skip this invoice
                    logging.error(f"Partner or Journal not found for doc_folio: {doc_folio}")
                    continue

                # Create Invoice Header
                invoice_data = {
                    'partner_id': partner.id,
                    'journal_id': journal.id,
                    'move_type': 'in_invoice',
                    'invoice_date': invoice_detail.get('doc_fecha_emision'),
                    'invoice_date_due': invoice_detail.get('doc_fecha_vencimiento'),
                    'ref': doc_folio,
                    'amount_total': float(doc_monto_total),
                    # Add other fields as needed
                }

                invoice = self.env['account.move'].sudo().create(invoice_data)
                invoices.append(invoice)

                # Create Invoice Line
                account_id = self.env['account.account'].search([('code', '=', '310115')], limit=1)
                invoice_line_data = {
                    'move_id': invoice.id,
                    'account_id': account_id.id if account_id else False,
                    'quantity': 1,
                    'price_unit': float(doc_monto_total),
                    'name': f"{doc_tipo_dte_desc} - {doc_emisor_razonsocial}",
                    # Add other fields as needed
                }

                self.env['account.move.line'].sudo().create(invoice_line_data)

        return invoices