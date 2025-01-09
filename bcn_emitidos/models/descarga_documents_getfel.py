# -- coding: utf-8 --
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

# Lib Call Websrevice
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
        log_message = f"Conexion PORTAL - Ambiente: {getdte_amb_id}, Empresa: {getdte_emp_id}, URL: {url_portal_api}, Usuario: {getdte_user}, Password: {getdte_pass}\n"
        logging.info(log_message)

        api_url_login = url_portal_api + "/api/login"
        headers = {"Content-Type": "application/json"}
        login_data = {"ambiente_id": getdte_amb_id, "empresa_id": getdte_emp_id, "usuario": getdte_user, "contrasena": getdte_pass}

        try:
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

                if country_code == 'CO':
                    self.env.cr.execute("""
                    SELECT 
                        TO_CHAR(create_date, 'YYYY-MM-DD'),
                        TO_CHAR(invoice_date_due, 'YYYY-MM-DD'),
                        sequence_number,
                        (SELECT code FROM l10n_latam_document_type where id = l10n_latam_document_type_id ) as tipo_doc,
                        (SELECT company_registry FROM res_partner where id = account_move.partner_id ) as rut_receptor,
                        (SELECT company_registry FROM res_company inner join res_partner on partner_id = res_partner.id  where res_company.id = %s ),
                        account_move.id
                        FROM account_move
                        WHERE company_id = %s   and 
                        bcn_fel_status IN ('manual','not_sent','ask_for_status') or bcn_fel_status is null and state ='posted' and journal_id='15';""", [getdte_odoo_company_id, getdte_odoo_company_id])

                    list_account_pendientes = self.env.cr.fetchall()
                    
                    if list_account_pendientes:
                        for record in list_account_pendientes:
                            fecha_emision = record[0]
                            fecha_recepcion = record[1]
                            folio = record[2]
                            tipo_doc = record[3]
                            rut_receptor = record[4]
                            rut_emisor = record[5]
                            account_move_id = record[6]
                            
                            
                            data = {
                                "token": token,
                                "tipo_ingreso": "1",
                                "emision_inicio": fecha_emision,
                                "folio_numero": folio,
                                "rut_emisor": rut_emisor,
                                "rut_receptor": rut_receptor,
                                "tipo_documento": tipo_doc
                            }
                            logging.info("ODOO DOCUMENTO : " + str(data) + "\n")

                            try:
                                response = requests.get(api_url_documentos, json=data, headers=headers)
                                response.raise_for_status()
                                data_resp = response.json()
                            except requests.RequestException as e:
                                logging.error(f"Error en la solicitud GETDTE DOCUMENTO: {e}")
                                data_resp = {'respuesta': {'codigo': -1, 'mensaje': 'Error en la solicitud GETDTE DOCUMENTO'}}

                            res_doc_json = json.dumps(data_resp)
                            logging.info("GETDTE DOCUMENTO : " + str(res_doc_json) + "\n")

                            if data_resp.get('respuesta', {}).get('codigo') == 0 and data_resp.get('datos', {}).get('contador') > 0:
                                doc_dian_estado = data_resp['datos']['detalle'][0]['doc_dian_estado']   
                                doc_dian_estado_respuesta = self.diccioanario_getfel_bcn(doc_dian_estado)

                                logging.info("GETFEL doc_dian_estado : " + str(doc_dian_estado_respuesta) + "\n")
                                if doc_dian_estado_respuesta:
                                    
                                    
                                    logging.info("GETDTE DOCUMENTO ESTADO: "+str(doc_dian_estado)+" RECEP: "+str(doc_dian_estado_respuesta)+" FOLIO: "+str(folio)+" TIPO DOC: "+str(tipo_doc)+"\n")
                                    self.update_estado_documento(doc_dian_estado_respuesta, account_move_id)
                                else:
                                    logging.info("Estado no Valido para el Documento \n")

                                return {
                                    'bcn_fel_status': doc_dian_estado_respuesta
                                }
            
        except requests.RequestException as e:
            logging.error(f"Error en la solicitud GETDTE DOCUMENTO: {e}")
            data_resp = {'respuesta': {'codigo': -1, 'mensaje': 'Error en la solicitud GETDTE DOCUMENTO'}}
            return {
                'bcn_fel_status': 'default_value'
            }

    

    def update_estado_documento(self, doc_dian_estado_respuesta, account_move_id):
      
        query = """
            UPDATE public.account_move
            SET bcn_fel_status = %s
        WHERE id = %s
            """
        self.env.cr.execute(query, [doc_dian_estado_respuesta, account_move_id])
        
        # Asegúrate de que estado_odoo_sii tenga un valor, si es False, no agregues el mensaje
        if doc_dian_estado_respuesta:
            
            move=self.env['account.move'].browse(account_move_id)
            
            logging.info('Estado para chat')
            logging.info(doc_dian_estado_respuesta)
            body = '<h2>Resultado del documento es: %s</h2><br/>' % doc_dian_estado_respuesta
            move.message_post(body=body)

    
    def diccioanario_getfel_bcn(self, doc_dian_estado):
        doc_dian_estado_respuesta = 'default_value'  # Valor predeterminado

        if doc_dian_estado == 4:
            doc_dian_estado_respuesta = 'rejected'
            
        elif doc_dian_estado == 3:
            doc_dian_estado_respuesta = 'accepted'
            
        elif doc_dian_estado == 2:
            doc_dian_estado_respuesta = 'rejected'
        
        elif doc_dian_estado == 1:
            doc_dian_estado_respuesta = 'not_sent'
        
        elif doc_dian_estado == 0:
            doc_dian_estado_respuesta = 'rejected'

        return doc_dian_estado_respuesta
