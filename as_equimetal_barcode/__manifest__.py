# -*- coding: utf-8 -*-
{
    'name' : "Ahorasoft EQUIMETAL Barcode",
    'version' : "1.0.3",
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
        ],
    'website': 'http://www.ahorasoft.com',
    'data' : [
            # 'security/ir.model.access.csv',
            'views/templates.xml',
             ],
    'demo' : [],
    'installable': True,
    'application': True,
    'auto_install': False
}
