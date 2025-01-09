# -*- coding: utf-8 -*-
{
    'name': "Sistema Control de Canales ACLM",

    'summary': """
        Sistema Control de Canales ACLM
        """,

    'description': """
        Sistema Control de Canales ACLM
    """,

    'author': "BCN Consultores",
    'website': "https://www.bcncons.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'security/aclm_security.xml',
        'security/ir.model.access.csv',
        'views/aclm_menu.xml',
        'views/aclm_cuotas.xml',
        'views/aclm_multas.xml',
        'views/aclm_reportes.xml',
        'views/aclm_accionistas.xml',
        'views/aclm_account_move.xml',
        'views/aclm_cuponera.xml',
        'views/aclm_icontador.xml'
    ],

    

    #Add license to remove License Warning
    'license': 'OPL-1'
}

