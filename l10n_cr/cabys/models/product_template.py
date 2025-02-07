# -*- coding: utf-8 -*-

import logging, re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', ]

    cabys_product_id = fields.Many2one("cabys.producto", "Producto en el catálogo Cabys")
    cabys_code = fields.Char(related='cabys_product_id.codigo', readonly=True)
    cabys_tax = fields.Float(related='cabys_product_id.impuesto', readonly=True)
