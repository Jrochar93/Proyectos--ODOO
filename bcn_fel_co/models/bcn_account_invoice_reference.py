# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class BcnAccountInvoiceReference(models.Model):
    _inherit = 'bcn.account.invoice.reference'


    referencia_tipo = fields.Selection([
        ('Afectacion', 'Afectacion'),
        ('Orden', 'Orden'),
        ('Despacho', 'Despacho'),
        ('Recepcion', 'Recepcion'),
        ('', 'Otras'), 
        ], string='Referencia Tipo')
    
    bcn_reference_doc_type_id = fields.Many2one(
        'l10n_latam.document.type',
        string='Tipo de Documento CO',
        domain="[('country_id.code', '=', 'CO')]",
        attrs={'invisible': [('country_id.code', '!=', 'CO')]},  # Oculta el campo si el país no es "CO"
        )
