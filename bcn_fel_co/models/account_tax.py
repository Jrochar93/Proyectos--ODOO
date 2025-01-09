#-- coding: utf-8 --
from odoo import models, fields

# -----------------------------------------------
# Modelo Heredado / account.tax
# -----------------------------------------------



class AccountTaxBcnFelCo(models.Model):
    _inherit = 'account.tax'
    
    imp_tipo = fields.Selection(
        [('impuesto', 'Impuesto'), ('retencion', 'Retención')],
        string='Tipo Impuesto'
    )

    imp_codigo = fields.Char(string='Codigo Impuesto', invisible=True)
