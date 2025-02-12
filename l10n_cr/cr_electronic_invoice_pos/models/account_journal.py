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


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    payment_method_id = fields.Many2one(
        "payment.methods", string="Payment Methods")
