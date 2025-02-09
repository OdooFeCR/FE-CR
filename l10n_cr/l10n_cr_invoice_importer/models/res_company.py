# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CompanyElectronic(models.Model):
    _name = 'res.company'
    _inherit = ['res.company', 'mail.thread', ]



    def _get_default_journal_id(self):
        return self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)

    # Fields for automatic import invoice from email
    import_bill_automatic = fields.Boolean(
        string='Import Vendor Bills',
        help='Select to upload vendor bills from incoming email')
    import_bill_mail_server_id = fields.Many2one('fetchmail.server', string='Mail Server',
                                                 help='Select the Incoming Mail Server')
    import_bill_journal_id = fields.Many2one(string='Journal', comodel_name='account.journal',
                                             domain="[('type', '=', 'purchase')]", default=_get_default_journal_id,
                                             help='Vendor Bills Journal')
    import_bill_product_id = fields.Many2one('product.product', string='Product',
                                             domain=[('purchase_ok', '=', True)],
                                             help='Set a product to each line')
    import_bill_account_id = fields.Many2one('account.account', string='Expense Account',
                                             domain=[('deprecated', '=', False)],
                                             help='Assign a spending account to each line')
    import_bill_account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                                      help='Assign an analytical account to each line')

    import_bill_folder_import = fields.Char(string='Folder to import', help='Source folder where the emails to be '
                                                                            'imported will be found')
