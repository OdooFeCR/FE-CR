# -*- coding: utf-8 -*-
#     info@fakturacion.com
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class CabysCategoria6(models.Model):
    _name = 'cabys.categoria6'
    _description = 'Categoría 6 de Cabys'

    name   = fields.Char('Categoria 6', readonly=True)
    codigo = fields.Char('Código', readonly=True)

    cabys_categoria5_id = fields.Many2one(comodel_name='cabys.categoria5', readonly=True)
    cabys_categoria7_ids = fields.One2many('cabys.categoria7', 'cabys_categoria6_id', string='Categorías 7', readonly=True)

