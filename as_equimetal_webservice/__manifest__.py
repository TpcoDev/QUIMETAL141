# -*- coding: utf-8 -*-
{
    'name' : "Ahorasoft EQUIMETAL customizaciones",
    'version' : "1.0.1",
    'author'  : "Ahorasoft",
    'description': """
Webservice dummy equimetal
===========================

Custom module for Latproject
    """,
    'category' : "Sale",
    'depends' : [
        "base",
        "purchase",
        "stock",
        "sale_management"
        ],
    'website': 'http://www.ahorasoft.com',
    'data' : [
            'security/ir.model.access.csv',
            'views/as_mesage_log.xml',
             ],
    'demo' : [],
    'installable': True,
    'auto_install': False
}
