# -*- coding: utf-8 -*-
{
    'name' : "Ahorasoft EQUIMETAL customizaciones",
    'version' : "1.0.5",
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
        "sale_management",
        "l10n_cl_edi_stock",
        ],
    'website': 'http://www.ahorasoft.com',
    'data' : [
            'security/ir.model.access.csv',
            'views/as_mesage_log.xml',
            'views/as_stock_picking.xml',
            'views/as_res_config.xml',
             ],
    'demo' : [],
    'installable': True,
    'auto_install': False
}
