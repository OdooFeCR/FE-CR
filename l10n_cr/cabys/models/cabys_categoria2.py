# -*- coding: utf-8 -*-
#     info@fakturacion.com
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class CabysCategoria2(models.Model):
    _name = 'cabys.categoria2'
    _description = 'Categoría 2 de Cabys'

    name   = fields.Char('Categoria 2', readonly=True)
    codigo = fields.Char('Código', readonly=True)

    cabys_categoria1_id = fields.Many2one(comodel_name='cabys.categoria1', readonly=True)
    cabys_categoria3_ids = fields.One2many('cabys.categoria3', 'cabys_categoria2_id', string='Categorías 3', readonly=True)


