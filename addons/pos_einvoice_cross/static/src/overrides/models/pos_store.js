/** @odoo-module */

import {PosStore} from "@point_of_sale/app/services/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    // @Override
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.city_id = loadedData['res.country.state.district.city'];
        this.l10n_latam_identification_type_id = loadedData['l10n_latam.identification.type'];
    },
});
