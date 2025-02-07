# -*- coding: utf-8 -*-
#     info@fakturacion.com
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class CabysCategoria7(models.Model):
    _name = 'cabys.categoria7'
    _description = 'Categoría 7 de Cabys'

    name   = fields.Char('Categoria 7', readonly=True)
    codigo = fields.Char('Código', readonly=True)

    cabys_categoria6_id = fields.Many2one(comodel_name='cabys.categoria6', readonly=True)
    cabys_categoria8_ids = fields.One2many('cabys.categoria8', 'cabys_categoria7_id', string='Categorías 8', readonly=True)

