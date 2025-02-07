# -*- coding: utf-8 -*-
#     info@fakturacion.com
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class CabysProducto(models.Model):
    _name = 'cabys.producto'
    _description = 'Catálogo de bienes y servicios (Cabys)'

    name     = fields.Char('Descripción del bien o servicio', readonly=True)
    codigo   = fields.Char('Código Cabys', readonly=True)
    impuesto = fields.Float('Impuesto', digits=(12, 2), readonly=True)

    cabys_categoria8_id = fields.Many2one(comodel_name='cabys.categoria8', string='Categoría 8', readonly=True)
    cabys_categoria7_id = fields.Many2one(related='cabys_categoria8_id.cabys_categoria7_id', string='Categoría 7', readonly=True)
    cabys_categoria6_id = fields.Many2one(related='cabys_categoria7_id.cabys_categoria6_id', string='Categoría 6', readonly=True)
    cabys_categoria5_id = fields.Many2one(related='cabys_categoria6_id.cabys_categoria5_id', string='Categoría 5', readonly=True)
    cabys_categoria4_id = fields.Many2one(related='cabys_categoria5_id.cabys_categoria4_id', string='Categoría 4', readonly=True)
    cabys_categoria3_id = fields.Many2one(related='cabys_categoria4_id.cabys_categoria3_id', string='Categoría 3', readonly=True)
    cabys_categoria2_id = fields.Many2one(related='cabys_categoria3_id.cabys_categoria2_id', string='Categoría 2', readonly=True)
    cabys_categoria1_id = fields.Many2one(related='cabys_categoria2_id.cabys_categoria1_id', string='Categoría 1', readonly=True)

    product_ids = fields.One2many('product.template', 'cabys_product_id', string='Productos con este código')
    category_ids = fields.One2many('product.category', 'cabys_product_id', string='Categorias con este código')


    _sql_constraints = [('codigo_uniq', 'unique (codigo)', 'Ya existe un registro con el mismo código.'),]

    @api.depends('name', 'codigo', 'cabys_categoria8_id', 'cabys_categoria7_id', 'cabys_categoria6_id', 'cabys_categoria5_id')
    def name_get(self):
        result = []
        for product in self:
            # get all category names
            categories = [product.cabys_categoria8_id.name, product.cabys_categoria7_id.name,product.cabys_categoria6_id.name, product.cabys_categoria5_id.name]
            # eliminate duplicated strings
            categories = list(set(categories))
            # join category names
            categories = '[%s]' % '] ['.join(categories)
            # make one big nice line
            name = '%s %s %s' % (product.codigo, product.name, categories)
            # shorten result string
            name = '%s...' % name[:150] if len(name) > 150 else name[:150]

            result.append((product.id, name))
        return result
        
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """ search in name, code and category"""
        args = args or []
        domain = []
        if name:
            # search in name, codigo and categories
            domain = args + ['|', ('name', operator, name), ('codigo', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
