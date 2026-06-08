/** @odoo-module **/

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
