import redis
from rejson import Client, Path
from odoo import models, api
import orjson
import json
import logging
from odoo.tools import date_utils
import zlib
import time  # Import the time module

_logger = logging.getLogger(__name__)

DOMAIN = [('sale_ok', '=', True), ('available_in_pos', '=', True)]
FIELD_LIST = [
    'display_name', 'lst_price', 'standard_price', 'categ_id', 'pos_categ_id',
    'taxes_id', 'barcode', 'default_code', 'to_weight', 'uom_id',
    'description_sale', 'description', 'product_tmpl_id', 'tracking',
    'available_in_pos', 'attribute_line_ids', 'active', '__last_update',
    'image_128', 'id', 'available_lot_for_pos_ids'
]

class PosRedisMixin(models.AbstractModel):
    _name = 'pos.redis.mixin'
    _description = 'Point of Sale Cache Mixin'

    def _get_redis_client(self):
        """Initialize RedisJSON client using system parameters."""
        ICPSudo = self.env['ir.config_parameter'].sudo()
        if ICPSudo.get_param('redis.host'):
            return Client(
                host=ICPSudo.get_param('redis.host', '127.0.0.1'),
                port=int(ICPSudo.get_param('redis.port', 6379)),
                db=int(ICPSudo.get_param('redis.db', 0)),
                password=ICPSudo.get_param('redis.password') or None,
                decode_responses=False
            )
        return None

    def get_products_from_database(self, limit=1000, offset=0):
        """Fetch products from database in batches for efficiency."""
        start_time = time.time()  # Start timing
        Product = self.env['product.product']
        products = Product.with_user(self.env.ref('base.user_admin').id).with_context(display_default_code=False)
        result = products.search_read(DOMAIN, FIELD_LIST, limit=limit, offset=offset, order='sequence,default_code,name')
        duration = time.time() - start_time  # Calculate duration
        _logger.info(f"Fetched products from database in {duration:.4f} seconds.")
        return result

    def clear_existing_redis_data(self):
        """Clear existing product data from Redis."""
        redis_client = self._get_redis_client()
        if not redis_client:
            _logger.error("Redis client could not be initialized.")
            return

        start_time = time.time()  # Start timing

        try:
            keys_to_delete = redis_client.keys('products:*')
            if keys_to_delete:
                redis_client.delete(*keys_to_delete)
                _logger.info(f"Deleted {len(keys_to_delete)} existing product keys from Redis.")
            redis_client.delete("product_ids")
            _logger.info("Cleared existing product_ids list from Redis.")
        except redis.exceptions.RedisError as e:
            _logger.error(f"Failed to clear existing data in Redis: {str(e)}")
            return

        duration = time.time() - start_time  # Calculate duration
        _logger.info(f"Cleared existing Redis data in {duration:.4f} seconds.")

    @api.model
    def load_all_products_to_redis(self):
        """Load all products into Redis, serialized and compressed as JSON, and store product IDs separately."""
        self.clear_existing_redis_data()
        redis_client = self._get_redis_client()
        pipeline = redis_client.pipeline()

        offset = 0
        product_ids = []

        start_time = time.time()  # Start timing for the entire load operation

        while True:
            products = self.get_products_from_database(limit=1000, offset=offset)
            if not products:
                break

            for product_data in products:
                try:
                    json_product = orjson.dumps(product_data, default=date_utils.json_default)
                    compressed_product = zlib.compress(json_product)  # Compress JSON data
                    product_id = product_data['id']
                    pipeline.set(f"products:{product_id}", compressed_product)
                    product_ids.append(product_id)
                except Exception as e:
                    _logger.error(f"Error serializing product {product_data['id']}: {str(e)}")

            try:
                pipeline.execute()  # Execute the pipeline to save the batch
            except redis.exceptions.RedisError as e:
                _logger.error(f"Failed to execute pipeline: {str(e)}")

            offset += 1000
            _logger.info(f"Processed batch up to offset {offset} with {len(products)} products.")

        # Store the product IDs as a list in Redis
        redis_client.rpush("product_ids", *product_ids)

        total_duration = time.time() - start_time  # Calculate total duration
        _logger.info(f"Loaded all products to Redis in {total_duration:.4f} seconds.")

    @api.model
    def get_limited_products_from_redis(self, limit=1000, offset=0):
        """Retrieve limited products from Redis using pagination on the cached product IDs."""
        redis_client = self._get_redis_client()
        if not redis_client:
            _logger.error("Redis client could not be initialized.")
            return []

        start_time = time.time()  # Start timing

        try:
            product_ids = redis_client.lrange("product_ids", offset, offset + limit - 1)
            product_ids = [x.decode('utf-8') for x in product_ids]
        except redis.exceptions.RedisError as e:
            _logger.error(f"Failed to retrieve product IDs from Redis: {str(e)}")
            return []

        if not product_ids:
            return []

        pipeline = redis_client.pipeline()
        for product_id in product_ids:
            pipeline.get(f"products:{product_id}")  # Use get for compressed data

        try:
            compressed_products = pipeline.execute()
        except redis.exceptions.RedisError as e:
            _logger.error(f"Failed to retrieve products from Redis: {str(e)}")
            return []

        products = [
            json.loads(zlib.decompress(compressed_product).decode('utf-8'))
            for compressed_product in compressed_products if compressed_product
        ]

        duration = time.time() - start_time  # Calculate duration
        _logger.info(f"Retrieved and decompressed products from Redis in {duration:.4f} seconds.")

        return products

    def get_total_products_count(self):
        """Get the total number of products in Redis."""
        redis_client = self._get_redis_client()

        start_time = time.time()  # Start timing

        try:
            total_products = redis_client.llen("product_ids")
        except redis.exceptions.RedisError as e:
            _logger.error(f"Failed to retrieve total products from Redis: {str(e)}")
            return 0

        duration = time.time() - start_time  # Calculate duration
        _logger.info(f"Retrieved total product count from Redis in {duration:.4f} seconds.")

        return total_products

    def _update_redis_cache(self, product):
        """Update the Redis cache for a specific product."""
        redis_client = self._get_redis_client()
        if redis_client:
            start_time = time.time()  # Start timing
            try:
                product_data = product.read(FIELD_LIST)[0]
                json_product = orjson.dumps(product_data, default=date_utils.json_default)
                compressed_product = zlib.compress(json_product)  # Compress JSON data
                redis_client.set(f"products:{product.id}", compressed_product)
                _logger.info(f"Product {product.id} updated in Redis cache.")
            except Exception as e:
                _logger.error(f"Error updating product {product.id} in Redis cache: {str(e)}")

            duration = time.time() - start_time  # Calculate duration
            _logger.info(f"Updated product {product.id} in Redis cache in {duration:.4f} seconds.")

    def _remove_from_redis_cache(self, product):
        """Remove the product from Redis cache."""
        redis_client = self._get_redis_client()
        if redis_client:
            start_time = time.time()  # Start timing
            try:
                redis_client.delete(f"products:{product.id}")
                redis_client.lrem("product_ids", 0, product.id)
                _logger.info(f"Product {product.id} removed from Redis cache.")
            except Exception as e:
                _logger.error(f"Error removing product {product.id} from Redis cache: {str(e)}")

            duration = time.time() - start_time  # Calculate duration
            _logger.info(f"Removed product {product.id} from Redis cache in {duration:.4f} seconds.")
