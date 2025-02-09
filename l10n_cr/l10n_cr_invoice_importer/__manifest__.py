# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Importador de Facturas Electronicas',
    'version': '17.0.0.0.0',
    'category': 'Accounting/Accounting',
    'author': 'Singulary, CR Factura',
    'license': 'AGPL-3',
    'website': 'https://singulary.online',
    'summary': 'Importador de Facturas Electronicas de Costa Rica',

    'description': """
        
    """,

    # any module necessary for this one to work correctly
    'depends': ['cr_electronic_invoice', 'mail'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'data/import_vendor_cron.xml',
        'views/res_company_views.xml',
        'views/account_move.xml'
        # 'views/account_view.xml',
        # 'views/account_invoice_view.xml',
        # 'wizard/cr_multiple_invoice_validation_wz_view.xml',
    ]
    ,
}
