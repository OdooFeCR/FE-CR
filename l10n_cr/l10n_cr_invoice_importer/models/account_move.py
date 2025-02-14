
from odoo import models, fields, api, _

class AccountInvoiceElectronic(models.Model):
    _inherit = "account.move"

    iva_condition = fields.Selection([
        ('gecr', 'Genera crédito IVA'),
        ('crpa', 'Genera crédito parcial del IVA'),
        ('bica', 'Capital assets'),
        ('gcnc', 'El gasto corriente no genera crédito'),
        ('prop', 'Proporcionalidad')],
        string='Condición de IVA',
        required=False,
        default='gecr',
    )

    company_activity_id = fields.Many2one("economic.activity", string="Actividad económica compañia", required=False, default=lambda self: self.company_id.activity_id.id)
    # company_activities_ids = fields.Many2many(realted="company_id.economic_activities_ids")
