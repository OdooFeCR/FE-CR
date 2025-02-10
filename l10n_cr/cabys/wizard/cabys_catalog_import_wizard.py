# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from xlrd import open_workbook
import logging
import base64
import urllib.request

_logger = logging.getLogger(__name__)

# The catalog file is an Excel file where every row
# contains all the product and categories information
# The following is a column mapping of the data fields and its meaning

# Categories description and codes
categories_map = [
    {
        'category': '1',
        'code': 0, 
        'description': 1
    },
    {
        'category': '2',
        'code': 2,
        'description': 3, 
        'subcategory': 0
    },
    {
        'category': '3',
        'code': 4,
        'description': 5, 
        'subcategory': 2
    },
    {
        'category': '4',
        'code': 6,
        'description': 7, 
        'subcategory': 4
    },
    {
        'category': '5',
        'code': 8,
        'description': 9, 
        'subcategory': 6
    },
    {
        'category': '6',
        'code': 10,
        'description': 11,
        'subcategory': 8
    },
    {
        'category': '7',
        'code': 12,
        'description': 13,
        'subcategory': 10
    },
    {
        'category': '8',
        'code': 14,
        'description': 15,
        'subcategory': 12
    }
]
# Cabys product description, code, tax and category
products_map = {
    'category': 14,
    'code': 16,
    'description': 17,
    'tax': 18,
    'first_description': 19,
    'second_description': 20
}
# Expected header titles for data columns
# we'll use this to check if the catalog file is a correct catalog cabys file
headers_map = [
    {
        'column': 0,  'header': 'Categoría 1'
    },
    {
        'column': 1,  'header': 'Descripción (categoría 1)'
    },
    {
        'column': 2,  'header': 'Categoría 2'
    },
    {
        'column': 3,  'header': 'Descripción (categoría 2)'
    },
    {
        'column': 4,  'header': 'Categoría 3'
    },
    {
        'column': 5,  'header': 'Descripción (categoría 3)'
    },
    {
        'column': 6,  'header': 'Categoría 4'
    },
    {
        'column': 7,  'header': 'Descripción (categoría 4)'
    },
    {
        'column': 8,  'header': 'Categoría 5'
    },
    {
        'column': 9,  'header': 'Descripción (categoría 5)'
    },
    {
        'column': 10, 'header': 'Categoría 6'
    },
    {
        'column': 11, 'header': 'Descripción (categoría 6)'
    },
    {
        'column': 12, 'header': 'Categoría 7'
    },
    {
        'column': 13, 'header': 'Descripción (categoría 7)'
    },
    {
        'column': 14, 'header': 'Categoría 8'
    },
    {
        'column': 15, 'header': 'Descripción (categoría 8)'
    },
    {
        'column': 16, 'header': 'Categoría 9'
    },
    {
        'column': 17, 'header': 'Descripción (categoría 9)'
    },
    {
        'column': 18, 'header': 'Impuesto'
    },
    {
        'column': 19, 'header': 'Nota explicativa 1. Incluye'
    },
    {
        'column': 20, 'header': 'Nota explicativa 2. Excluye'
    },
]


class CabysCatalogImportWizard(models.TransientModel):
    _name = 'cabys.catalog.import.wizard'
    _description = 'Import the Cabys Catalog from an Excel file.'

    cabys_excel_file = fields.Binary(
        string='Archivo de Excel', copy=False, attachment=True)
    notes = fields.Text("Descripción", readonly=True)
    button_enable = fields.Boolean()
    file_url = fields.Char(
        default='https://www.bccr.fi.cr/indicadores-economicos/cabys/Cabys_catalogo_historial_de_cambios.xlsx'
    )

    def download_catalog(self):
        ''' Download the Cabys catalog Excel file from BCCR.
        '''
        _logger.info('downloading catalog %s' % self)
        response = urllib.request.urlopen(self.file_url)
        _logger.info(response)
        self.cabys_excel_file = base64.b64encode(response.read())
        self.onchange_cabys_excel_file()

        return {
            'name': _("Actualización de catálogo Cabys"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cabys.catalog.import.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': self.id,
        }

    def update_catalog(self):
        ''' Update the Cabys catalog from an Excel file.
        '''
        _logger.info('update_catalog %s' % self)
        if not self.cabys_excel_file:
            return

        # update the database with the data from the catalog file
        products_new, products_updated,  products_deleted, categories_new, categories_updated, categories_deleted = self._update_catalog_from_excel_file()

        msg = 'El Catálogo Cabys fue actualizado con éxito\n'
        if products_new:
            msg += '%s nuevos registros\n' % len(products_new)
        if products_updated:
            msg += '%s registros actualizados\n' % len(products_updated)
        if products_deleted:
            msg += '%s registros eliminados\n' % len(products_deleted)
        msg += '\n'
        if categories_new:
            msg += '%s nuevas categorias\n' % len(categories_new)
        if categories_updated:
            msg += '%s categorias actualizadas\n' % len(categories_updated)
        if categories_deleted:
            msg += '%s categorias eliminadas\n' % len(categories_deleted)

        self.notes = msg
        self.button_enable = False

        context = dict(self.env.context or {})

        return {
            'name': _("Catálogo Cabys actualizado exitosamente"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cabys.catalog.import.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
            'view_id': False,
            'domain': '[]',
            'res_id': self.id,
        }

    @api.onchange('cabys_excel_file')
    def onchange_cabys_excel_file(self):
        """Preprocess Excel File."""

        if self.cabys_excel_file:
            # get file contents
            excel_file = base64.b64decode(self.cabys_excel_file)
            # open it as an Excel file
            workbook = open_workbook(file_contents=excel_file)
            # Get first sheet, that's where all the data should be
            xl_sheet = workbook.sheet_by_index(0)
            # second row has the headers of the file
            # we will check the headers names to infer if this is a Cabys catalog file
            for header in headers_map:
                cell = xl_sheet.cell(1, header['column'])
                if cell.value != header['header']:
                    self.notes = 'El archivo seleccionado no parece ser un catálogo Cabys'
                    self.button_enable = False
                    return

            # if we haven't returned at this point, the file's headers are correct
            # we then compare the records in the file against the records in the database
            products_new, products_updated, products_deleted = self._analyze_excel_file()

            msg = 'Actualizar el catálogo comprende los siguientes cambios:\n'
            msg += '%s nuevos registros\n' % len(products_new)
            msg += '%s registros actualizados\n' % len(products_updated)
            msg += '%s registros eliminados\n' % len(products_deleted)
            self.notes = msg
            self.button_enable = True

        else:
            self.notes = 'Suba su archivo con el catálogo Cabys o descarguelo del BCCR\n'
            self.button_enable = False

    def _analyze_excel_file(self):
        products_new = []
        products_updated = []
        products_deleted = []

        if self.cabys_excel_file:
            # get Excel file
            excel_file = base64.b64decode(self.cabys_excel_file)
            _logger.info('Loading Cabys catalog from Excel file')
            # open it as xlrd workbook
            workbook = open_workbook(file_contents=excel_file)
            _logger.info('workbook %s' % workbook)
            # get first sheet, that's where the data is
            xl_sheet = workbook.sheet_by_index(0)
            _logger.info('Sheet %s name %s' % (xl_sheet, xl_sheet.name))
            # get rows of data from workbook sheet
            rows = xl_sheet.get_rows()
            # skip first two header rows
            rows.__next__()
            rows.__next__()
            # here we will process all the records (rows in catalog file)
            products_codes = []
            # iterate over every row
            for row in rows:
                # get product data
                code = row[products_map['code']].value
                cabys_categoria8_id = row[products_map['category']].value
                name = row[products_map['description']].value
                tax_data = row[products_map['tax']].value
                tax_converted = 0.0
                if isinstance(tax_data, str) and '%' in tax_data:
                    # Remueve el símbolo de porcentaje y luego divide por 100
                    tax_converted = float(tax_data[:-1]) / 100
                else:
                    try:
                        tax_converted = float(tax_data)
                    except ValueError:
                        # Si el valor no es numérico, establece un NaN
                        tax_converted = 0.0
                impuesto = tax_converted

                products_codes.append(code)

                # search record
                record_id = self.env['cabys.producto'].search(
                    [('codigo', '=', code)])
                # if record exist and its values are different, it should be updated
                if record_id:
                    if record_id.name != name or \
                       record_id.cabys_categoria8_id.codigo != cabys_categoria8_id or \
                       record_id.impuesto != impuesto:
                        products_updated.append(code)
                # if record doesn't exist, it should be created
                else:
                    products_new.append(code)

            # products in db but not in the catalog file should be deleted
            record_ids = self.env['cabys.producto'].search(
                [('codigo', 'not in', products_codes)])
            products_deleted = record_ids.mapped('codigo')

        return products_new, products_updated, products_deleted