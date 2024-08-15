# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models

DOMAIN = [('sale_ok', '=', True), ('available_in_pos', '=', True)]


class PosSession(models.Model):
    _inherit = 'pos.session'

    def get_products_from_cache(self,limit=1000,offset=0):
        cache = self.env['pos.redis']
        products = cache.get_limited_products_from_redis(limit=limit, offset=offset)

        if not products:
            # If products not found in Redis, fetch from DB and update Redis
            cache.load_all_products_to_redis()
            products = self.get_products_from_cache()

        return products



    def _get_pos_ui_product_product(self, params):
        """
        If limited_products_loading is active, prefer the native way of loading products.
        Otherwise, replace the way products are loaded.
            First, we only load the first 100000 products.
            Then, the UI will make further requests of the remaining products.
        """
        if self.config_id.limited_products_loading:
            return super()._get_pos_ui_product_product(params)
        records = self.get_products_from_cache(limit=1000)
        self._process_pos_ui_product_product(records)
        return records

    def get_cached_products(self, offset=0):
        records = self.get_products_from_cache(limit=1000, offset=offset)
        self._process_pos_ui_product_product(records)
        return records

    def get_total_products_count(self):
        Product = self.env['product.product']
        product_ids = Product.search(DOMAIN).ids
        return len(product_ids)
