from .common import TestPosRedisCommon
from odoo.addons.queue_job.job import Job

class TestProductRedis(TestPosRedisCommon):

    @classmethod
    def setUpClass(cls):
        super(TestProductRedis, cls).setUpClass()

        # Define test product values
        cls.product_vals = {
            'name': 'Test Product Template',
            'list_price': 100.0,
            'standard_price': 70.0,
            'type': 'consu',
        }

        # Ensure Redis is cleared before running any tests
        cls.clear_redis_data()

        # Set the test environment context to disable job delays
        cls.env = cls.env(context=dict(
            cls.env.context,
            test_queue_job_no_delay=True,  # No delays for jobs during tests
        ))

    def run_all_pending_jobs(self):
        """Run all pending jobs in the queue."""
        pending_jobs = self.env['queue.job'].search([('state', '!=', 'done')])
        for job in pending_jobs:
            Job.load(self.env, job.uuid).perform()

    def test_product_create_adds_to_redis(self):
        """Test that creating a product adds it to Redis."""
        product = self.create_product(self.product_vals)
        self.run_all_pending_jobs()
        self.assertTrue(self.check_product_in_redis(product.id), "Product not found in Redis after creation.")

    def test_product_write_updates_redis(self):
        """Test that updating a product updates it in Redis."""
        product = self.create_product(self.product_vals)
        product.write({'list_price': 150.0})
        self.run_all_pending_jobs()
        self.assertTrue(self.check_product_in_redis(product.id), "Product not updated in Redis after write.")

    def test_product_unlink_removes_from_redis(self):
        """Test that deleting a product removes it from Redis."""
        product = self.create_product(self.product_vals)
        product_id = product.id
        product.unlink()
        self.run_all_pending_jobs()
        self.assertFalse(self.check_product_in_redis(product_id), "Product still exists in Redis after deletion.")

    def test_product_template_write_updates_related_products_in_redis(self):
        """Test that updating a product template updates related products in Redis."""
        product = self.create_product(self.product_vals)
        product_template = product.product_tmpl_id
        product_template.write({'name': 'Updated Template Name'})
        self.run_all_pending_jobs()
        self.assertTrue(self.check_product_in_redis(product.id), "Related product not updated in Redis after template update.")

    def test_product_template_unlink_removes_related_products_from_redis(self):
        """Test that deleting a product template removes related products from Redis."""
        product = self.create_product(self.product_vals)
        product_template = product.product_tmpl_id
        product_template_id = product_template.id
        product_template.unlink()
        self.run_all_pending_jobs()
        self.assertFalse(self.check_product_in_redis(product.id), "Related product still exists in Redis after template deletion.")
