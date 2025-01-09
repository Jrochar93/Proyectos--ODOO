# -*- coding: utf-8 -*-
{
    'name': "BCN Conector GetW1 Chile",

    'summary': """
        BCN Conector GetW1 Chile""",

    'description': """
        BCN Conector GetW1 Chile
    """,

    'author': "BCN",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','l10n_latam_invoice_document'],

    # always loaded
    'data': [
        'views/res_config_settings_views.xml',
        # 'security/ir.model.access.csv',
        #'views/views.xml',
        #'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
