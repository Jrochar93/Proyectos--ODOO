# -*- coding: utf-8 -*-

{
    'name': 'BCN Factura Electronica Colombia',
    
    'summary': """BCN Factura Electronica Colombia""",

    'description': """
        BCN Factura Electronica Colombia
        """,
    
    'author': 'BCN',
    
    'website': '',
    
    'category': 'Customizations',
    'version': '0.1',
    
    'depends': ['bcn_fel'],
    
    'data': [
        'security/bcn_security.xml',
        'security/ir.model.access.csv',        
        'views/account_move_views.xml',
        'views/res_partner_views.xml',
        'views/account_tax_views.xml',
        'data/l10n_latam.document.type.csv',
        'data/res.city.csv'
        
       
    ],
    'demo': [
        'demo/diccionario_fud_demo.xml',
    ],
    #Add license to remove License Warning
    'license': 'OPL-1'
}