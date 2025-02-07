{
    'name': "Catálogo de bienes y servicios para uso tributario y Cuentas Nacionales",

    'summary': "Catálogo de bienes y servicios para uso tributario y Cuentas Nacionales",
    'author': 'info@fakturacion.com',
    'website': "https://github.com/odoocr/cabys",
    'category': 'Account',
    'version': '15.0.1.0.0',
    'license': 'OPL-1',
    'depends': [
        'base', 'product',
    ],
    'data': [
        'views/cabys_producto_views.xml',
        'views/cabys_views.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
        'views/product_category_views.xml',
        'views/res_company_views.xml',
        'security/ir.model.access.csv'
    ],
    'assets': {
                'web.assets_backend': [
                    'cabys/static/src/js/cabys_import_button.js'
                ],
                'web.assets_qweb': [
                    'cabys/static/src/xml/**/*',
                ]
    },
    'installable': True,
}
