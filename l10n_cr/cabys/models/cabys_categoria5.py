# -*- coding: utf-8 -*-
#     info@fakturacion.com
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class CabysCategoria5(models.Model):
    _name = 'cabys.categoria5'
    _description = 'Categoría 5 de Cabys'

    name   = fields.Char('Categoria 5', readonly=True)
    codigo = fields.Char('Código', readonly=True)

    cabys_categoria4_id = fields.Many2one(comodel_name='cabys.categoria4', readonly=True)
    cabys_categoria6_ids = fields.One2many('cabys.categoria6', 'cabys_categoria5_id', string='Categorías 6', readonly=True)

