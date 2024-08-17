from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_redis_integration = fields.Boolean(string="Use Redis Integration")
    redis_host = fields.Char(string="Redis Host", config_parameter='redis.host', default="127.0.0.1")
    redis_port = fields.Integer(string="Redis Port", config_parameter='redis.port', default=6379)
    redis_db = fields.Integer(string="Redis Database", config_parameter='redis.db', default=0)
    redis_password = fields.Char(string="Redis Password", config_parameter='redis.password')