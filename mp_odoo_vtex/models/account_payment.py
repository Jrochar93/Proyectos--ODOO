# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import http.client
import json
import string

class AccountPayment(models.Model):
    _inherit = "account.payment"

    origin_ecommerce = fields.Boolean('Origen E-commerce', default=False)
    value_shipping = fields.Float('Valor de envio')
     


