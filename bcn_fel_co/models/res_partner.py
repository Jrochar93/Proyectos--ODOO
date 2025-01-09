#-- coding: utf-8 --
from odoo import models, fields

# -----------------------------------------------
# Modelo Heredado /res.partner
# -----------------------------------------------

    
class ResPartnerBcnFelCo(models.Model):
    _inherit = 'res.partner'
    
    """nit = fields.Integer(string='NIT sin DV', invisible=True)
    
    dvnit = fields.Integer(string='DV NIT', invisible=True)  
    tercero_idendoc = fields.Selection(
        [('11', 'Tarjeta de identidad'),('12', 'Cédula de ciudadanía'),('13', 'Tarjeta de extranjería'),('14', 'Cédula de extranjería'),
         ('31', 'NIT'),('41', 'Pasaporte'),('42', 'identificación extranjero'),('50', 'NIT de otro país'),('91', 'NUIP')],
        string=' Identificación Tercero',
        default='31'
    )"""
    tercero_respon = fields.Char(string='Tercero Responsabilidades', invisible=True,default='R-99-PN')
    tercero_tipo_emp = fields.Selection(
        [('1', 'Persona Jurídica'),('2', 'Persona Natural')],
        string=' Tipo de Empresa',
        default='2'
    )
    
    #tercero_pais_leng = fields.Char(string='Tercero Lenguaje', invisible=True,default='es')
    
    tercero_regimen = fields.Selection(
        [('48', 'Responsable del impuesto sobre las ventas–IVA'),('49', 'No responsable de IVA')],
        string=' Regimen'      
    )
    
    #tercero_mun_cod = fields.Char(string='Tercero Municipio Codigo', invisible=True)
    
    #tercero_dep_cod = fields.Char(string='Tercero Departamento Codigo', invisible=True)
    
    #tercero_pais_cod = fields.Char(string='Tercero Pais Codigo', invisible=True)

