from odoo.tests.common import TransactionCase
from unittest.mock import patch
from redis import Redis
from rejson import Client

class TestPosRedisCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPosRedisCommon, cls).setUpClass()
        cls.ProductProduct = cls.env['product.product']
        cls.ProductTemplate = cls.env['product.template']
        cls.redis_client = cls.ProductProduct._get_redis_client()

    @classmethod
    def tearDownClass(cls):
        """Ensure Redis test data is cleared after the test suite."""
        cls.clear_redis_data()
        # cls.patcher.stop()  # Stop patching
        super(TestPosRedisCommon, cls).tearDownClass()

    @classmethod
    def _get_test_redis_client(cls):
        """Initialize a Redis client specifically for testing purposes."""
        return Client(
            host='127.0.0.1',
            port=6379,
            db=15,  # Use a separate database for tests
            decode_responses=True
        )

    @classmethod
    def create_product(cls, product_template_vals=None):
        """Helper method to create a product.product record."""
        if product_template_vals is None:
            product_template_vals = {
                'name': 'Test Product Template',
                'list_price': 100.0,
                'standard_price': 70.0,
                'type': 'consu',
            }
        product_template = cls.ProductTemplate.create(product_template_vals)
        return cls.ProductProduct.search([('product_tmpl_id', '=', product_template.id)])

    @classmethod
    def check_product_in_redis(cls, product_id):
        """Helper method to check if a product is stored in Redis."""
        return cls.redis_client.exists(f"products:{product_id}")

    @classmethod
    def clear_redis_data(cls):
        """Helper method to clear Redis data."""
        keys_to_delete = cls.redis_client.keys('products:*')
        if keys_to_delete:
            cls.redis_client.delete(*keys_to_delete)
        cls.redis_client.delete("product_ids")


