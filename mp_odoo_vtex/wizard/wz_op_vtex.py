# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import xlrd
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
import openpyxl
import base64
from io import BytesIO
import logging
from unidecode import unidecode
import http.client
import json
import logging

_logger = logging.getLogger(__name__)


class WzOpRequestVtex(models.TransientModel):
    _name = "wz.op.request.vtex"
    _description = "Confirmar multiple pedidos de ventas"

    request_ops_mp = fields.Many2many('vtex.sync.operations', 'wz_synx_op_to_products', string='Solicitudes')


    @api.onchange('request_ops_mp')
    def list_order_ids(self):
        list_orders = []
        for record in self.env['vtex.sync.operations'].browse(self._context['active_ids']):
            if record.state == 'draft':
                list_orders.append(record.id)
            else:
                if record.state == 'validate':
                    raise ValidationError("La solicitud %s ha sido sincronizada" % (record.name))
        
        self.request_ops_mp = [(6,self,list_orders)]
            

    def sync_multiple_request(self):
        for record in self.request_ops_mp:
            if record.state == 'draft':
                record.sync_op()