# -*- coding: utf-8 -*-
{
    'name': "Mp segumiento de Guías",

    'summary': """
        Mp segumiento de Guías""",

    'description': """
        Mp segumiento de Guías
    """,
    'author': "TI Department More Products S.A.S",
    'website': "http://www.moreproducts.com",
    'category': 'Sales',
    'version': '2.1.2',
    'depends': [
            'base',
            'sale',
            'stock',
            'delivery',  
            'mp_products',
            ],
    'data': [
        'security/ir_security.xml',
        'security/ir.model.access.csv',
        'report/sale_order_picking_report_view.xml',
        'report/sale_order_trk_guide_sac_report_view.xml', 
        'views/menuitems.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    
}
