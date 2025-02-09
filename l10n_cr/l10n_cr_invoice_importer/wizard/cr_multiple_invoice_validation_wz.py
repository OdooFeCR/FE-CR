# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _, fields
from odoo.exceptions import UserError


class CrMultipleInvoiceValidation(models.TransientModel):
    _name = 'cr.multiple.invoice.validation'
    _description = 'Multiple invoice validation Wz'

    iva_condition = fields.Selection([
        ('gecr', 'Generate IVA credit'),
        ('crpa', 'Generates partial IVA credit'),
        ('bica', 'Capital assets'),
        ('gcnc', 'Current spending does not generate credit'),
        ('prop', 'Proportionality')],
        string='IVA Condition',
        required=False,
        default='gecr',
    )
    company_activity_id = fields.Many2one("economic.activity", string="Default economic activity", required=False,
                                          context={'active_test': False})

    state_invoice_partner = fields.Selection(
        [('1', 'Accepted'),
         ('2', 'Partial acceptance'),
         ('3', 'Rejected')],
        'Customer response')

    invoice_ids = fields.Many2many('account.invoice', string='Invoices')

    alert_warning = fields.Html(string='Alert_warning')

    import_bill_account_id = fields.Many2one('account.account', string='Expense Account',
                                             domain=[('deprecated', '=', False)],
                                             help='Assign a spending account to each line')
    import_bill_account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account',
                                                      help='Assign an analytical account to each line')


    @api.onchange('invoice_ids')
    def _onchange_invoice_ids(self):
        if not self.invoice_ids:
            invoices = []
            exclude_invoices = []
            invoice_ids = self.env['account.invoice'].browse(self._context.get('active_ids'))
            for inv in invoice_ids:
                if inv.state != 'draft':
                    exclude_invoices.append(inv.partner_id.name)
                else:
                    invoices.append(inv.id)
            values = {'value': {'invoice_ids': [(4, item) for item in invoices]}}
            if exclude_invoices:
                alert_message = _("<div class='alert alert-danger' role='alert'> Some invoices were removed from the "
                                  "list, because they cannot be validated (%s) </div>") % " - ".join(exclude_invoices)
                values['value'].update({
                    'alert_warning': alert_message
                })
            return values

    @api.multi
    def run_validate(self):
        for inv in self.invoice_ids:
            inv.company_activity_id = self.company_activity_id
            inv.iva_condition = self.iva_condition
            inv.state_invoice_partner = self.state_invoice_partner
            for rec in inv.invoice_line_ids:
                if self.import_bill_account_id:
                    rec.account_id = self.import_bill_account_id
                if self.import_bill_account_analytic_id:
                    rec.account_analytic_id = self.import_bill_account_analytic_id.id
            inv.action_invoice_open()
