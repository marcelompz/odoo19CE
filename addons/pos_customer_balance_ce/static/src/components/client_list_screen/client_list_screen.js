/** @odoo-module **/
// Cache bust: 2
import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";
import { onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(PartnerList.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        onWillStart(async () => {
            const partners = this.pos.models["res.partner"];
            if (partners && partners.length > 0) {
                const partnerIds = partners.map(p => p.id);
                try {
                    // Odoo 19 uses the ORM service directly
                    const result = await this.orm.read("res.partner", partnerIds, ["outstanding_debt"]);

                    if (result && Array.isArray(result)) {
                        for (const row of result) {
                            const partner = this.pos.models["res.partner"].find(p => p.id === row.id);
                            if (partner) {
                                // Update the reactive record in the PoS store
                                partner.outstanding_debt = row.outstanding_debt;
                            }
                        }
                    }
                } catch (e) {
                    console.error("Error refreshing customer balances:", e);
                }
            }
        });
    },
    get isBalanceDisplayed() {
        return true;
    },


});
import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";

patch(PartnerLine.prototype, {
    async settleCustomerAccount() {
        const partner = this.props.partner;
        if (!partner) return;
        
        const debt = partner.outstanding_debt || 0;
        if (debt >= 0) {
            console.warn("Este cliente no tiene deuda pendiente para saldar.");
            return;
        }

        let amountToPay = Math.abs(debt);

        // Show a popup to allow the user to enter a specific amount
        const payload = await makeAwaitable(this.env.services.dialog, NumberPopup, {
            title: "Monto a Pagar",
            startingValue: amountToPay,
        });

        if (!payload) {
            return; // cancelled
        }

        const inputAmount = parseFloat(payload);
        if (isNaN(inputAmount) || inputAmount <= 0) {
            console.warn("Monto inválido");
            return;
        }

        amountToPay = inputAmount;

        const product = this.pos.models['product.product'].find(p => p.display_name === 'Abono de Cuenta' || p.name === 'Abono de Cuenta');
        if (!product) {
            console.error("Producto de Settle Due ('Abono de Cuenta') no está cargado en el TPV.");
            return;
        }

        let order = this.pos.get_order();
        if (!order || order.get_orderlines().length > 0) {
            this.pos.add_new_order();
            order = this.pos.get_order();
        }

        order.set_partner(partner);

        await this.pos.addLineToCurrentOrder({
            product_id: product,
            price_unit: amountToPay,
            qty: 1,
            merge: false,
        });

        this.pos.showScreen('PaymentScreen');
        // Also close the partner list dialog if it's open
        if (this.props.close) {
            this.props.close();
        }
    }
});
