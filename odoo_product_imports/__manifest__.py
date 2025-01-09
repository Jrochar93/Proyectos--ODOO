# -*- coding: utf-8 -*-
{
    'name': "Product Imports",

    'summary': """
        Product Imports""",

    'description': """
        Product Imports
    """,

    'category': 'Purchase',
    'version': '1.0',

    'depends': [
        #'purchase',
        'stock',
        'account',
        'account_extended',
        'stock_landed_costs',
        'sr_partial_bill_payment',
        'purchase_stock',
        #'purchase_order_advances',
        'purchase_requisition_extended',
        
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/purchase_import_views.xml',
        'views/purchase_view.xml',
        'views/stock_pick_view.xml',
        'views/account_move_view.xml',
        'views/account_payment_view.xml',
        'views/stock_landed_cost_views.xml',
        'views/valuation_adjustment_report_view.xml'
    ],
    'demo': [
    ],
}

