# -*- coding: utf-8 -*-
{
    'name' : "Ahorasoft EQUIMETAL stock  customizaciones",
    'version' : "1.0.2",
    'author'  : "Ahorasoft",
    'description': """
stock equimetal
===========================

Custom module for Latproject
    """,
    'category' : "Stock",
    'depends' : ["base","stock"],
    'website': 'http://www.ahorasoft.com',
    'data' : [
                'wizard/as_menu.xml',
                'views/as_campos_x.xml',
                'report/as_reportes_etiquetas_pdf.xml',
                'report/as_reporte_2.xml',
                'views/as_format_report.xml',
                'security/ir.model.access.csv',
             ],
    'demo' : [],
    'installable': True,
    'auto_install': False
}
