# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models

DOMAIN = [('sale_ok', '=', True), ('available_in_pos', '=', True)]


class PosSession(models.Model):
    _name = 'pos.session'
    _inherit = ['pos.session', 'pos.redis.mixin']



    def get_products_from_cache(self, limit=1000, offset=0):

        products = self.get_limited_products_from_redis(limit=limit, offset=offset)

        if not products:
            # If products not found in Redis, fetch from DB and update Redis
            self.load_all_products_to_redis()
            products = self.get_products_from_cache()

        return products



    def _get_pos_ui_product_product(self, params):
        """
        If limited_products_loading is active, prefer the native way of loading products.
        Otherwise, replace the way products are loaded.

        """

        if self.config_id.limited_products_loading:
            return super()._get_pos_ui_product_product(params)
        records = self.get_products_from_cache(limit=100)
        self._process_pos_ui_product_product(records)
        return records

    def get_cached_products(self, offset=0):
        records = self.get_products_from_cache(limit=self.BATCH_SIZE, offset=offset)
        self._process_pos_ui_product_product(records)
        return records

    def get_batch_size(self):
        return self.BATCH_SIZE



