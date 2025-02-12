/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

patch(PaymentScreen.prototype, {
    toggleIsToInvoice() {
        // Call original function
        super.toggleIsToInvoice(...arguments);

        // Get the selected order
        const order = this.pos.get_order();
        if (order) {
            // Assign tipo_documento when toggling invoice option
            order.set_tipo_documento(order.is_to_invoice() ? "FE" : "TE")
        }
    },

    async validateOrder(isForceValidate) {
         // Get the selected order
        const order = this.pos.get_order();
        if (order){
            const sucursal = this.pos.config.sucursal;
            const terminal = this.pos.config.terminal;
            const tipo_documento = order.get_tipo_documento();
            const seq_id = order.get_tipo_documento() === "FE" ? this.pos.config.FE_sequence_id[0] : this.pos.config.TE_sequence_id[0];
            const electronic_number = await order.generate_number_electronic(seq_id,sucursal,terminal,tipo_documento);
            order.set_number_electronic(electronic_number)   
        }
        await super.validateOrder(...arguments);
    }
});
