# -*- coding: utf-8 -*-
from datetime import * 
from datetime import timedelta 

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import http.client
import json
import string
import requests
import os


class VtexOrdersPayments(models.Model):
    _name = 'vtex.orders.payments'
    _description = 'Vtex Orders Payments'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'


    name = fields.Char('Nombre')
    amount = fields.Float('Monto')
    date = fields.Date('Fecha')
    partner_id = fields.Many2one('res.partner', string='Cliente')

    item_payment_ids = fields.One2many('vtex.orders.payments.items', 'order_payment_id', string='Items Payments')

    order_vtex_id = fields.Many2one('vtex.orders', string='Id Order VTEX')
    sale_order_id = fields.Many2one('sale.order', string='Pedido de Venta', related='order_vtex_id.sale_order_id')
    invoice_id = fields.Many2one('account.move', string='Factura',  related='order_vtex_id.invoice_id')

    payment_id = fields.Many2one('account.move', string='Pago', )

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('validate', 'Validado'),
        ('error', 'Error'),
        ('cancel', 'Cancelado'),
    ], string='Estado',default='draft')
    color = fields.Integer('Color')
    
    state_pay = fields.Selection([
        ('draft', 'Borrador'),
        ('applied', 'Aplicado'),
        ('pay_confirmed', 'Pago confirmado'),
        ('pay_reconciliate', 'Pago conciliado'),
    ], string='Estado del Pago',default='draft')

    total_amount = fields.Float('Total Factura')
    total_amount_calculated = fields.Float('Total Calculado')
    total_amount_calculated_add = fields.Float('Total Calculado')
    total_amount_pay = fields.Float('Pago')

    total_commision_pay = fields.Float('Comision')
    total_shipping_pay = fields.Float('Costo de envio')
    total_chargue_shipp_pay = fields.Float('Cargo de envio')
    total_fee_pay = fields.Float('Tarifa')

    total_tax_pay = fields.Float('Total Impuesto')
    total_ica_pay = fields.Float('Total ICA')
    total_rtefuente_pay = fields.Float('Total RTFTE')
    

    @api.onchange('total_amount','total_amount_calculated','total_commision_pay','total_shipping_pay','total_fee_pay','total_tax_pay','total_ica_pay','total_rtefuente_pay')
    def _onchange_t_value(self):
        t_amt_cal = t_amt_cal_add = 0
        t_comm_cal = t_shipp_cal = t_tax_cal = t_ica_cal = t_rtefte_cal = t_ammount = 0

        for rec in self:
            t_ammount = rec.total_amount
            if abs(rec.total_commision_pay) > 0:
                t_comm_cal = rec.total_commision_pay
            if abs(rec.total_shipping_pay) > 0:
                t_shipp_cal = rec.total_shipping_pay
            if abs(rec.total_tax_pay) > 0:
                t_tax_cal = rec.total_tax_pay
            if abs(rec.total_ica_pay) > 0:
                t_ica_cal = rec.total_ica_pay
            if abs(rec.total_rtefuente_pay) > 0:
                t_rtefte_cal = rec.total_rtefuente_pay

            t_amt_cal_add = t_comm_cal + t_shipp_cal + t_tax_cal + t_ica_cal + t_rtefte_cal
            t_amt_cal = t_ammount - t_amt_cal_add

            rec.total_amount_calculated = t_amt_cal
            rec.total_amount_calculated_add = t_amt_cal_add

    def confirm_payment(self):
        for rec in self:
            rec.payment_id.action_post()
            

    def apply_payment(self):
        session_company_id = self.env.user.company_id
        get_config = self.env['config.vtex.access'].get_config_vtex()
        account_move = self.env['account.move']
        account_move_line = self.env['account.move.line']
        lines_move = []
        journal_default_id = get_config['journal_default_id']

        config_pay_ids = get_config['config_pay_ids']

        t_amt_cal = t_amt_cal_add = 0
        t_comm_cal = t_shipp_cal = t_tax_cal = t_ica_cal = t_rtefte_cal = t_ammount = 0

        for rec in self:
            # get account 
            for rec_config_p in config_pay_ids:
                if rec_config_p.apply_type == 'payment' and  rec_config_p.affects_pay == 'debit':
                    account_invoice_db = rec_config_p.account_id.id
                    
                if rec_config_p.apply_type == 'sale' and  rec_config_p.affects_pay == 'credit':
                    account_invoice_cr = rec_config_p.account_id.id
                
                if rec_config_p.apply_type == 'rtfte' and  rec_config_p.affects_pay == 'debit':
                    account_invoice_rtfte = rec_config_p.account_id.id

                if rec_config_p.apply_type == 'iva' and  rec_config_p.affects_pay == 'debit':
                    account_invoice_iva = rec_config_p.account_id.id    

                if rec_config_p.apply_type == 'ica' and  rec_config_p.affects_pay == 'debit':
                    account_invoice_ica = rec_config_p.account_id.id   

                if rec_config_p.apply_type == 'shipping' and  rec_config_p.affects_pay == 'debit':
                    account_invoice_envio = rec_config_p.account_id.id   

                if rec_config_p.apply_type == 'commision' and  rec_config_p.affects_pay == 'debit':
                    account_invoice_commision = rec_config_p.account_id.id   


            t_ammount = rec.amount
            if abs(rec.total_commision_pay) > 0:
                t_comm_cal = rec.total_commision_pay
            if abs(rec.total_chargue_shipp_pay) > 0:
                t_shipp_cal = rec.total_chargue_shipp_pay
            if abs(rec.total_tax_pay) > 0:
                t_tax_cal = rec.total_tax_pay
            if abs(rec.total_ica_pay) > 0:
                t_ica_cal = rec.total_ica_pay
            if abs(rec.total_rtefuente_pay) > 0:
                t_rtefte_cal = rec.total_rtefuente_pay

            t_amt_cal_add = t_comm_cal + t_shipp_cal + t_tax_cal + t_ica_cal + t_rtefte_cal
            t_amt_cal = t_ammount - t_amt_cal_add

            # move to credit
            lines_move.append((0,0,{
                        'account_id': account_invoice_cr,
                        'partner_id': rec.partner_id.id ,
                        'credit': abs(t_ammount) ,
                    }))
            
            # move to debit 
            lines_move.append((0,0,{
                        'account_id': account_invoice_db ,
                        'partner_id': rec.partner_id.id ,
                         'debit': abs(rec.total_amount_pay) ,
                    }))

            # rtfte
            if t_rtefte_cal > 0:
                lines_move.append((0,0,{
                            'account_id': account_invoice_rtfte,
                            'partner_id': rec.partner_id.id ,
                            'debit': abs(t_rtefte_cal) ,
                        }))
            # iva
            if t_tax_cal > 0:
                lines_move.append((0,0,{
                            'account_id': account_invoice_iva,
                            'partner_id': rec.partner_id.id ,
                            'debit': abs(t_tax_cal) ,
                        }))
            # ica
            if t_ica_cal > 0:
                lines_move.append((0,0,{
                            'account_id': account_invoice_ica,
                            'partner_id': rec.partner_id.id ,
                            'debit': abs(t_ica_cal) ,
                        }))
            # envio
            if t_shipp_cal > 0:
                lines_move.append((0,0,{
                            'account_id': account_invoice_envio,
                            'partner_id': rec.partner_id.id ,
                            'debit': abs(t_shipp_cal) ,
                        }))
            # commision
            if t_comm_cal > 0:
                lines_move.append((0,0,{
                            'account_id': account_invoice_commision,
                            'partner_id': rec.partner_id.id ,
                            'debit': abs(t_comm_cal) ,
                        }))

            line_ids = {
                        'journal_id': journal_default_id.id ,
                        'ref': rec.name ,
                        'x_studio_referencia_1_1': rec.invoice_id.name ,
                        'x_studio_referencia_2_1': rec.name ,
                        'client_order_ref_from_so': rec.name ,
                        'line_ids': lines_move,
            }
            recorsets = account_move.create(line_ids)
            rec.write({'payment_id': recorsets.id})

    def reconciliate_payment(self):
        session_company_id = self.env.user.company_id
        get_config = self.env['config.vtex.access'].get_config_vtex()
        config_pay_ids = get_config['config_pay_ids']

        for rec in self:
            invoice_id = rec.invoice_id
            payment_id = rec.payment_id

            for rec_config_p in config_pay_ids:
                if rec_config_p.apply_type == 'sale' and  rec_config_p.affects_pay == 'credit':
                    account_invoice_cr = rec_config_p.account_id.id

            line_id = False
            rec_config_p.account_id.id 

            for rec_pay in payment_id.line_ids:
                if rec_pay.account_id.id == account_invoice_cr:
                    line_id = rec_pay.id

            lines = self.env['account.move.line'].browse(line_id)
            lines += invoice_id.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
            lines.reconcile()
            if lines:
                rec.write({'state_pay': 'pay_reconciliate'})

    def sync_payment(self):
        # buscar registro segun e id  paymentIdMarketplace_cd
        item_payment_ids = self.env['vtex.orders.payments.items']
        vals_updt = {}
        tax_details_list = []
        list_d = []
        d1={}
        total_amount = total_amount_pay = total_commision_pay = total_shipping_pay = total_fee_pay =  total_fee_pay = cost_shipping_pay = am_f = am_iva = am_ica = chargue_shipping_pay = 0
        for record in self:
            if record.order_vtex_id.paymentIdMarketplace_cd:
                get_data_pay = item_payment_ids.search([
                                                    '|',
                                                    '|',
                                                    '|',
                                                    ('id_ref_shipping_pay','ilike',str(record.order_vtex_id.name)),
                                                    ('id_ref_shipping_pay','ilike',str(record.order_vtex_id.shipment_id_cd)),
                                                    ('id_ref_shipping_pay','ilike',str(record.order_vtex_id.paymentIdMarketplace_cd)),
                                                    ('id_oper_payment_market','ilike',str(record.order_vtex_id.paymentIdMarketplace_cd)),
                                            ])
                for record_p in get_data_pay:
                    tax_details = record_p.tax_details_pay
                    if tax_details != '' or tax_details != [] or tax_details != '[]' or tax_details != '[]':
                        tax_details_f1 = tax_details.replace('[','')
                        tax_details_f2 = tax_details_f1.replace(']','')
                        tax_details_f3 = tax_details_f2.replace('"fuente,','"fuente",')
                        tax_details_f4 = tax_details_f3.replace('"iva,','"iva",')
                        tax_details_f5 = tax_details_f4.replace('"ica,','"ica",')
                        tax_details_f6_f1 = tax_details_f5.replace(', "detail"', '", "detail"')
                        tax_details_f6 = tax_details_f6_f1.replace(' ', '')

                        tax_det = tax_details_f6.split(sep='{', maxsplit=1)
                        tax_det = tax_details_f6.split(sep='}', maxsplit=2)
                        tax_det = tax_details_f6.split(sep='{', maxsplit=3)

                        if  tax_details != '['']':
                            if len(tax_det) == 4:
                                # todos los impuestos
                                # crear diccionarios
                                dict_1 = "{"+tax_det[1]
                                dict_2 = "{"+tax_det[2]
                                dict_3 = "{"+tax_det[3]

                                # replace extra
                                dict_1_f = dict_1.replace('},','}')
                                dict_2_f = dict_2.replace('},','}')
                                dict_3_f = dict_3.replace('},','}')

                                dict_1_f_1 = json.loads(dict_1_f)
                                dict_2_f_2 = json.loads(dict_2_f)
                                dict_3_f_2 = json.loads(dict_3_f)

                                if dict_1_f_1['financial_entity'] == 'fuente':
                                    am_f = abs(float(dict_1_f_1['amount']))
                                if dict_2_f_2['financial_entity'] == 'iva':
                                    am_iva = abs(float(dict_2_f_2['amount']))
                                if dict_3_f_2['financial_entity'] == 'ica':
                                    am_ica = abs(float(dict_2_f_2['amount']))
                            else:
                                # crear diccionarios
                                dict_1 = "{"+tax_det[1]
                                dict_2 = "{"+tax_det[2]

                                # replace extra
                                dict_1_f = dict_1.replace('},','}')
                                dict_2_f = dict_2.replace('},','}')
                                
                                dict_1_f1 = dict_1_f.replace('""','"')
                                dict_2_f1 = dict_2_f.replace('""','"')

                                dict_1_f_1 = json.loads(dict_1_f1)
                                dict_2_f_2 = json.loads(dict_2_f1)

                                if dict_1_f_1['financial_entity'] == 'fuente':
                                    am_f = abs(float(dict_1_f_1['amount']))
                                if dict_2_f_2['financial_entity'] == 'iva':
                                    am_iva = abs(float(dict_2_f_2['amount']))

                        
                    # separar los valores 
                    if abs(float(record_p.value_sale_pay)) > 0:
                        total_amount = abs(float(record_p.value_sale_pay))
                    if abs(float(record_p.amount_oper_sale_pay)) > 0:
                        total_amount_pay = abs(float(record_p.amount_oper_sale_pay))
                    if abs(float(record_p.commision_meli_tax_pay)) > 0:
                        total_commision_pay = abs(float(record_p.commision_meli_tax_pay))
                    if  abs(float(record_p.cost_shipping_pay))  > 0:
                        cost_shipping_pay = abs(float(record_p.cost_shipping_pay))
                    if  abs(float(record_p.chargue_shipping_pay))  > 0:
                        chargue_shipping_pay = abs(float(record_p.chargue_shipping_pay))
                    #if float(record_p.total_fee_pay) > 0:
                    #    total_fee_pay = record_p.total_fee_pay

                    vals_updt = {
                        'total_amount': total_amount,
                        'total_amount_pay': total_amount_pay,
                        'total_commision_pay': total_commision_pay,
                        'total_shipping_pay': cost_shipping_pay,
                        'total_chargue_shipp_pay': chargue_shipping_pay,
                        'total_fee_pay': 0,
                        'total_tax_pay': am_iva,
                        'total_ica_pay': am_ica,
                        'total_rtefuente_pay': am_f,
                        
                    }
                record.write(vals_updt)
        


class VtexOrdersPaymentsItems(models.Model):
    _name = 'vtex.orders.payments.items'
    _description = 'Vtex Orders Payments Items'

    # Comisión por venta de Mercado Libre es tarifa
    name = fields.Char('NÚMERO DE IDENTIFICACIÓN')
    id_oper_payment_market = fields.Char('ID DE OPERACIÓN EN MERCADO PAGO')
    code_account_seller = fields.Char('CÓDIGO DE LA CUENTA DEL VENDEDOR')

    type_medium_pay= fields.Char('TIPO DE MEDIO DE PAGO')
    medium_pay = fields.Char('MEDIO DE PAGO')
    country_origin_pay = fields.Char('PAÍS DE ORIGEN DE LA CUENTA DE MERCADO PAGO')

    value_sale_pay = fields.Char('VALOR DE LA COMPRA')
    currency_pay = fields.Char('MONEDA')
    date_sale_pay = fields.Char('FECHA DE ORIGEN')


    commission_tax_pay = fields.Char('COMISIÓN MÁS IVA')
    amount_oper_sale_pay = fields.Char('MONTO NETO DE LA OPERACIÓN QUE IMPACTÓ TU DINERO')
    currency_settlement_pay = fields.Char('MONEDA DE LA LIQUIDACIÓN')

    date_approve_pay = fields.Char('FECHA DE APROBACIÓN')
    amount_net_oper_pay = fields.Char('MONTO NETO DE OPERACIÓN')

    data_extra = fields.Text('DATOS EXTRA')


    commision_meli_tax_pay = fields.Char('COMISIÓN DE MERCADO LIBRE MÁS IVA')
    cost_shipping_pay = fields.Char('COSTO DE ENVÍO')
    chargue_shipping_pay = fields.Char('CARGO DE ENVÍO')
    taxes_charged_pay = fields.Char('IMPUESTOS COBRADOS POR RETENCIONES IIBB')

    id_orden_meli_pay = fields.Char('ID DE LA ORDEN')
    id_ref_shipping_pay = fields.Char('ID DEL ENVÍO')
    mode_shipping_pay = fields.Char('MODO DE ENVÍO')

    id_ref_package_pay = fields.Char('ID DEL PAQUETE')
    tax_details_pay = fields.Text('IMPUESTOS DESAGREGADOS')

    number_inital_target_pay = fields.Char('NÚMERO INICIAL DE TARJETA')
    sale_channel_pay = fields.Char('CANAL DE VENTA')
    platform_payment_pay = fields.Char('PLATAFORMA DE COBRO')

    order_payment_id = fields.Many2one('vtex.orders.payments', string='Payment')
    
