from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _complete_values_from_session(self, session, values):
        # Mantener la funcionalidad original
        result = super()._complete_values_from_session(session, values)

        # Lógica para asignar el partner predeterminado
        if session.config_id.default_partner_id and not result.get("partner_id"):
            result["partner_id"] = session.config_id.default_partner_id.id
            result["to_invoice"] = True

        return result

    def _prepare_invoice_vals(self):
        # Mantener la funcionalidad original
        invoice_vals = super(PosOrder, self)._prepare_invoice_vals()

        # Buscar el método de pago de la orden y tomar solo el primero
        payment_methods = self.mapped('payment_ids.payment_method_id.account_payment_method_id')

        # Si existe al menos un método de pago, añadir el primero a los valores de la factura
        if payment_methods:
            invoice_vals['payment_methods_id'] = payment_methods[0].id

            # Crear la factura
            invoice = self.env['account.move'].create(invoice_vals)

            # Postear la factura inmediatamente
            invoice.action_post()
            
            _logger.info("Factura posteada exitosamente: %s", invoice.name)

        return invoice_vals  # Devolver los valores de la factura como de costumbre
