# -*- coding: utf-8 -*-
{
    'name' : "Ahorasoft EQUIMETAL Barcode",
    'version' : "1.0.8",
    'author'  : "Ahorasoft",
    'description': """
Webservice dummy equimetal
===========================

Custom module for Latproject
    """,
    'category' : "stock",
    'depends' : [
        "web",
        "base",
        "stock",
        "stock_barcode",
        "barcodes",
        "base_gs1_barcode",
        ],
    'website': 'http://www.ahorasoft.com',
    'data' : [
            'security/ir.model.access.csv',
            'views/templates.xml',
            'views/as_barcode_log.xml',
             ],
    'demo' : [],
    'qweb': [
        "static/src/xml/as_abstract_client_action.xml",
    ],  
    'installable': True,
    'application': True,
    'auto_install': False
}
