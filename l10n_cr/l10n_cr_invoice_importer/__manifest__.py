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

    # any module necessary for this one to work correctly
    'depends': ['cr_electronic_invoice', 'mail'],

    # always loaded
    'data': [
        'views/res_company_views.xml',
        'views/account_move.xml'
    ],
    'application': True,
    'installable': True,
    'icon': 'l10n_cr_invoice_importer/static/description/icon.png',
}
