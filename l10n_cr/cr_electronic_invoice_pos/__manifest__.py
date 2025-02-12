{
    'name': 'Facturación electrónica Costa Rica POS',
    'version': '17.0.0.0.0',
    'author': 'Singulary',
    'license': 'AGPL-3',
    'website': 'https://singulary.online',
    'category': 'Account',
    'description':
    '''
    Facturación electronica POS Costa Rica.
    ''',
    'depends': [
        'cr_electronic_invoice',
        'point_of_sale'
    ],
    'data': [

        'data/ir_cron_data.xml',
        'data/paper_format_data.xml',
        'data/payment_methods_data.xml',
        'report/pos_report.xml',        
        'views/pos_config_view.xml',
        'views/res_config_settings_views.xml',
        'views/pos_order_view.xml',
        'views/pos_payment_method.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'cr_electronic_invoice_pos/static/src/js/models.js',
            'cr_electronic_invoice_pos/static/src/js/payment_screen.js',
            'cr_electronic_invoice_pos/static/src/xml/custom_orderReceipt.xml',
        ],
    },
    'installable': True,
}
