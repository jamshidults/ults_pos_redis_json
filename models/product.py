from odoo import models, api
class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'pos.redis.mixin']

    def create(self, vals):
        product = super(ProductProduct, self).create(vals)
        self.with_delay()._queue_add_product_redis_cache(product)
        return product

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        for product in self:
            self.with_delay()._update_redis_cache(product)
        return res

    def unlink(self):
        for product in self:
            self.with_delay()._remove_from_redis_cache(product)
        return super(ProductProduct, self).unlink()


    def _queue_add_product_redis_cache(self, product):
        self._update_redis_cache(product)
        redis_client = self._get_redis_client()
        redis_client.rpush("product_ids", product.id)

    def _queue_update_product_redis_cache(self, product):
        self._update_redis_cache(product)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        # Trigger update on related product.product records
        related_products = self.env['product.product'].search([('product_tmpl_id', 'in', self.ids)])
        for product in related_products:
            product._update_redis_cache(product)
        return res

    def unlink(self):
        related_products = self.env['product.product'].search([('product_tmpl_id', 'in', self.ids)])
        for product in related_products:
            product._remove_from_redis_cache(product)
        return super(ProductTemplate, self).unlink()


