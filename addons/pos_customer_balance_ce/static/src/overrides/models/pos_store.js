/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.original_pricelist_id = this.original_pricelist_id || false;
    },
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.original_pricelist_id = json.original_pricelist_id;
    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.original_pricelist_id = this.original_pricelist_id;
        return json;
    },
    add_paymentline(payment_method) {
        if (payment_method.pricelist_id) {
            let pricelists = [];
            if (this.pos.pricelists) {
                pricelists = this.pos.pricelists;
            } else if (this.pos.models && this.pos.models['product.pricelist']) {
                pricelists = this.pos.models['product.pricelist'].getAll ? this.pos.models['product.pricelist'].getAll() : this.pos.models['product.pricelist'];
            }
            
            const pricelist = pricelists.find(p => p.id === payment_method.pricelist_id[0]);
            
            if (pricelist) {
                // Save original pricelist to revert if needed
                if (!this.original_pricelist_id) {
                    this.original_pricelist_id = this.pricelist ? this.pricelist.id : (this.pos.default_pricelist ? this.pos.default_pricelist.id : false);
                }
                this.set_pricelist(pricelist);
            }
        }
        return super.add_paymentline(payment_method);
    },
    remove_paymentline(line) {
        const payment_method = line ? line.payment_method : null;
        const res = super.remove_paymentline(line);
        
        if (payment_method && payment_method.pricelist_id) {
            // Revert pricelist if there are no other payment lines using this pricelist
            const remaining_paymentlines = this.get_paymentlines();
            const has_pricelist_method = remaining_paymentlines.some(l => l.payment_method.pricelist_id && l.payment_method.pricelist_id[0] === payment_method.pricelist_id[0]);
            
            if (!has_pricelist_method && this.original_pricelist_id) {
                let pricelists = [];
                if (this.pos.pricelists) {
                    pricelists = this.pos.pricelists;
                } else if (this.pos.models && this.pos.models['product.pricelist']) {
                    pricelists = this.pos.models['product.pricelist'].getAll ? this.pos.models['product.pricelist'].getAll() : this.pos.models['product.pricelist'];
                }
                
                const original_pricelist = pricelists.find(p => p.id === this.original_pricelist_id);
                if (original_pricelist) {
                    this.set_pricelist(original_pricelist);
                }
                this.original_pricelist_id = false;
            }
        }
        return res;
    }
});
