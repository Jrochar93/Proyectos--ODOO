import json
from re import search
import xlrd
import os

import xmlrpc.client
url = 'http://odoo-bcn-dev.dtebcn.cl:8069/'
db = 'bcn-produccion'
username = 'jzamudio@bcncons.com'
password = 'B+y0kdg='



def main():

    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    print('after uid')

    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    print(uid)
    #models.execute_kw(db, uid, password, model_name, function, domain, options)
    ids_partner_company = models.execute_kw(db, uid, password, 'res.partner', 'search', [[['is_company','=',True]]], {'limit':1})
    print(ids_partner_company)

    [record] = models.execute_kw(db, uid, password, 'res.partner', 'read', [ids_partner_company])
    len(record)
    print(len(record))

    data_partner_fields = models.execute_kw(db, uid, password,'res.partner','read',[ids_partner_company], {'fields':['name','country_id','comment']})
    print(data_partner_fields)

    print('\n short cut')
    partner_company = models.execute_kw(db, uid, password, 'res.partner', 'search_read', 
        [[['is_company','=',True]]],
        {'fields': ['name', 'country_id', 'comment'],
        'limit':1})
    print(partner_company)


if __name__ == '__main__':
    main()
