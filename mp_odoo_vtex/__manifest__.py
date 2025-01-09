# -*- coding: utf-8 -*-
{
    'name': "Mp VTEX",

    'summary': """
        Integracion VTEX-ODOO""",

    'description': """
        Integracion VTEX-ODOO
    """,
    'author': "TI Department More Products S.A.S",
    'website': "http://www.moreproducts.com",
    'category': 'Sales',
    'version': '2.1.2',
    'depends': [
            'base',
            'account',
            'base_setup',
            'sale',
            'stock',
            'delivery',  
            'mp_products',
            ],
    'data': [
        'security/ir_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_view.xml',
        'views/vtex_config_views.xml',
        'views/validator_vtex_views.xml',
        'views/vtex_orders_views.xml',
        'views/product_template_views.xml',
        'wizard/wz_send_products_views.xml',
        'wizard/wz_orders_vtex_views.xml',
        'views/vtex_orders_payments_views.xml',
        'wizard/wz_orders_payments_views.xml',
        'wizard/wz_op_vtex_views.xml',
        'views/menuitems.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    
}
