import redis
from rejson import Client, Path
from odoo import models, api
import json
import logging
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)

DOMAIN = [('sale_ok', '=', True), ('available_in_pos', '=', True)]
FIELD_LIST = [
    'display_name', 'lst_price', 'standard_price', 'categ_id', 'pos_categ_id',
    'taxes_id', 'barcode', 'default_code', 'to_weight', 'uom_id',
    'description_sale', 'description', 'product_tmpl_id', 'tracking',
    'available_in_pos', 'attribute_line_ids', 'active', '__last_update',
    'image_128', 'id'
]


class PosRedis(models.Model):
    _name = 'pos.redis'
    _description = 'Point of Sale Cache'

    def _get_redis_client(self):
        """Initialize RedisJSON client."""
        return Client(host='localhost', port=6379, decode_responses=True)

    def get_products_from_database(self, limit=1000, offset=0):
        """Fetch products from database in batches for efficiency."""
        Product = self.env['product.product']
        products = Product.with_user(self.env.ref('base.user_admin').id).with_context(display_default_code=False)
        return products.search_read(DOMAIN, FIELD_LIST, limit=limit, offset=offset, order='sequence,default_code,name')

    @api.model
    def load_all_products_to_redis(self):
        """Load all products into Redis, serialized as JSON."""
        redis_client = self._get_redis_client()
        pipeline = redis_client.pipeline()

        offset = 0
        while True:
            products = self.get_products_from_database(limit=1000, offset=offset)
            if not products:
                break

            for product_data in products:
                try:
                    json_product = json.dumps(product_data, default=date_utils.json_default)
                    pipeline.jsonset(f"products:{product_data['id']}", Path.rootPath(), json_product)
                except Exception as e:
                    _logger.error(f"Error serializing product {product_data['id']}: {str(e)}")

            try:
                pipeline.execute()  # Execute the pipeline to save the batch
            except redis.exceptions.RedisError as e:
                _logger.error(f"Failed to execute pipeline: {str(e)}")

            offset += 1000
            _logger.info(f"Processed batch up to offset {offset} with {len(products)} products.")

    @api.model
    def get_limited_products_from_redis(self, limit=1000, offset=0):
        """Retrieve limited products from Redis."""
        redis_client = self._get_redis_client()

        Product = self.env['product.product']
        product_ids = Product.search(DOMAIN, limit=limit, offset=offset).ids

        # Use pipeline for efficient retrieval
        pipeline = redis_client.pipeline()
        for product_id in product_ids:
            pipeline.jsonget(f"products:{product_id}", Path.rootPath())

        try:
            json_products = pipeline.execute()
        except redis.exceptions.RedisError as e:
            _logger.error(f"Failed to retrieve products from Redis: {str(e)}")
            return []

        products = [json.loads(json_product) for json_product in json_products if json_product]

        return products

    @api.model
    def get_products_from_redis(self):
        """Retrieve all products from Redis."""
        redis_client = self._get_redis_client()

        Product = self.env['product.product']
        product_ids = Product.search(DOMAIN).ids

        # Use pipeline for efficient retrieval
        pipeline = redis_client.pipeline()
        for product_id in product_ids:
            pipeline.jsonget(f"products:{product_id}", Path.rootPath())

        try:
            json_products = pipeline.execute()
        except redis.exceptions.RedisError as e:
            _logger.error(f"Failed to retrieve products from Redis: {str(e)}")
            return []

        products = [json.loads(json_product) for json_product in json_products if json_product]

        return products
