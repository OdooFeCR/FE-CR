from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # pos.config fields

    sucursal = fields.Integer(related='pos_config_id.sucursal', readonly=False)
    terminal = fields.Integer(related='pos_config_id.terminal', readonly=False)

    FE_sequence_id = fields.Many2one(related='pos_config_id.FE_sequence_id', readonly=False)
    NC_sequence_id = fields.Many2one(related='pos_config_id.NC_sequence_id', readonly=False)
    TE_sequence_id = fields.Many2one(related='pos_config_id.TE_sequence_id', readonly=False)

    def create_sequences(self):
        if self._context.get('pos_config_id'):
            pos_config_id = self._context['pos_config_id']
            pos_config = self.env['pos.config'].browse(pos_config_id)
            pos_config.create_sequences()
