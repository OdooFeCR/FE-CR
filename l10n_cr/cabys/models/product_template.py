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


    registro_medicamento = fields.Char(string='Registro de Medicamento', required=True)
    forma_farmaceutica_id = fields.Many2one(
        comodel_name='pharmaceutical.form',
        string='Forma Farmaceutica',
        required=True,
    )

    # Campo para indicar si los campos deben mostrarse
    show_fields_based_on_cabys = fields.Boolean(
        string="Mostrar Campos",
        compute="_compute_show_fields_based_on_cabys",
        store=False  # No se guarda en la base de datos, solo en memoria
    )

    @api.depends('cabys_code')
    def _compute_show_fields_based_on_cabys(self):
        for record in self:
            # Verificar si cabys_code tiene un valor válido
            if record.cabys_code and (
                record.cabys_code == '3569104990000' or
                record.cabys_code.startswith('3562') or
                record.cabys_code.startswith('3563')
            ):
                record.show_fields_based_on_cabys = True
            else:
                record.show_fields_based_on_cabys = False
            _logger.info(f"Registro {record.id}: show_fields_based_on_cabys={record.show_fields_based_on_cabys}")

    @api.onchange('cabys_code')
    def _onchange_code_cabys(self):
        _logger.info(f"Registro {self.id}: code_cabys={self.cabys_code}")
        self._compute_show_fields_based_on_cabys()