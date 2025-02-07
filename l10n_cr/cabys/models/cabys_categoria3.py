# -*- coding: utf-8 -*-
#     info@fakturacion.com
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


from odoo import models, fields, api

class CabysCategoria3(models.Model):
    _name = 'cabys.categoria3'
    _description = 'Categoría 3 de Cabys'

    name   = fields.Char('Categoria 3', readonly=True)
    codigo = fields.Char('Código', readonly=True)

    cabys_categoria2_id = fields.Many2one(comodel_name='cabys.categoria2', readonly=True)
    cabys_categoria4_ids = fields.One2many('cabys.categoria4', 'cabys_categoria3_id', string='Categorías 4', readonly=True)


