#-- coding: utf-8 --
from odoo import models, fields

# -----------------------------------------------
# Modelo Heredado de l10n_cl/account.move
# -----------------------------------------------
class Account_Move_BcnFelCo(models.Model):
    _inherit = 'account.move'

    tipo_operacion = fields.Selection(
        [('01', 'Combustibles'),('02', 'Emisor es Autorretenedor'),('03', 'Excluidos y Exentos'),('04', 'Exportación'),('05', 'Genérica'),
         ('06', 'Genérica con pago anticipado'),('07', 'Genérica con periodo de facturación'),('08', 'Consorcio'),('09', 'UAI'),('10', 'Estándar'),
         ('11', 'Mandatos'),('12', 'Servicios')],
        string='Tipo Operación',
        default='10'
    )
    
    tipo_factura = fields.Selection(
        [('01', 'Factura_Venta'),('02', 'Factura_Exportación'),('03', 'Documento_transmisión_03'),('04', 'Documento_transmisión_04'),
         ('91', 'Nota_Crédito'),('92', 'Nota_Débito')],
        string='Tipo Factura',
        default='01'
    )
    
    pago_metodo = fields.Selection(
        [('1', 'Contado'),('2', 'Crédito')],
        string='Pago Método'
    )
    
    pagomediocodigo = fields.Char(string='Pago Medio Codigo', default='ZZZ')
    pagoid = fields.Integer(string='PagoID', default=1, invisible=True)
    
