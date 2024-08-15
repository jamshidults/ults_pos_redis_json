odoo.define('pos_cache.chrome', function (require) {
    'use strict';

const Chrome = require('point_of_sale.Chrome');
const Registries = require('point_of_sale.Registries');
const {
        onError,
        onMounted,
        onWillDestroy,
        useExternalListener,
        useRef,
        useState,
        useSubEnv,
        reactive,
    } = owl;

function roundUpDiv(y, x) {
    const remainder = y % x;
    return (y - remainder) / x + (remainder > 0 ? 1 : 0);
}

const PosCacheChrome = (Chrome) => class PosCacheChrome extends Chrome {
    _runBackgroundTasks() {
        super._runBackgroundTasks();
        if (!this.env.pos.config.limited_products_loading) {
         reactive(this)._loadRemainingProducts().then(() => {
                    this.render(true);
                });

        }
    }
    async _loadRemainingProducts() {
        const nInitiallyLoaded = Object.keys(this.env.pos.db.product_by_id).length;
        const totalProductsCount = await this.env.pos._getTotalProductsCount();
        const nRemaining = totalProductsCount - nInitiallyLoaded;
        if (!(nRemaining > 0)) return;
        const multiple = 1000;
        let offset = nInitiallyLoaded;
        while (offset < totalProductsCount) {
            const end = Math.min(offset + multiple, totalProductsCount);
            console.log(`Loading products ${offset + 1} to ${end}`);
            await this.env.pos._loadCachedProducts(offset);
            offset = end;
            }

        this.showNotification(this.env._t('All products are loaded.'), 5000);
    }
};
Registries.Component.extend(Chrome, PosCacheChrome);
});
