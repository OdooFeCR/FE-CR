import base64
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.cr_electronic_invoice.models import api_facturae
from xml.sax.saxutils import escape
import datetime
import pytz
from threading import Lock
lock = Lock()

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'
    sucursal = fields.Integer(string="Branch", default="1")
    terminal = fields.Integer(help="Terminal number", default="1")
    """
        TODO: Cambiar formato de estos campos conforme al siguiente patron [a-z_][a-z0-9_]{2,59}$
        Se podría hacer un prehook en donde se busque en la BD si estan estos campos FE_sequence_id y pasarlo al
        formato fe_sequence_id, nc_sequence_id, te_sequence_id
    """
    FE_sequence_id = fields.Many2one("ir.sequence", string="Electronic Invoice Sequence")
    NC_sequence_id = fields.Many2one("ir.sequence", string="Electronic Credit Note Sequence")
    TE_sequence_id = fields.Many2one("ir.sequence", string="Electronic Ticket Sequence")

    def create_sequences(self):
        if self.journal_id:
            inv_cedula = self.journal_id.company_id.vat
            if inv_cedula:
                inv_cedula = str(inv_cedula).zfill(12)
                sucursal = str(self.sucursal).zfill(3)
                terminal = str(self.terminal).zfill(5)

                tipo_doc = '01'

                fe_sequence_id = self.env['ir.sequence'].sudo().create({
                    'name': 'Secuencia de Factura Electrónica POS: ' + self.name,
                    'code': 'sequence.pos.FE.' + str(self.id),
                    'prefix': '506%(day)s%(month)s%(y)s' + inv_cedula + sucursal + terminal + tipo_doc,
                    'suffix': "1%(h12)s%(day)s%(month)s%(y)s",
                    'padding': 10,
                })

                self.FE_sequence_id = fe_sequence_id.id

                tipo_doc = '03'

                nc_sequence_id = self.env['ir.sequence'].sudo().create({
                    'name': 'Secuencia de Nota Crédito Electrónica POS: ' + self.name,
                    'code': 'sequence.pos.NC.' + str(self.id),
                    'prefix': '506%(day)s%(month)s%(y)s' + inv_cedula + sucursal + terminal + tipo_doc,
                    'suffix': "1%(h12)s%(day)s%(month)s%(y)s",
                    'padding': 10,
                })

                self.NC_sequence_id = nc_sequence_id.id

                tipo_doc = '04'

                te_sequence_id = self.env['ir.sequence'].sudo().create({
                    'name': 'Secuencia de Tiquete Electrónico POS: ' + self.name,
                    'code': 'sequence.pos.TE.' + str(self.id),
                    'prefix': '506%(day)s%(month)s%(y)s' + inv_cedula + sucursal + terminal + tipo_doc,
                    'suffix': "1%(h12)s%(day)s%(month)s%(y)s",
                    'padding': 10,
                })

                self.TE_sequence_id = te_sequence_id.id
            else:
                raise UserError('You must configure the identification on the company')
