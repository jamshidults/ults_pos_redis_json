# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "ults_pos_redis_json",

    'summary': "Enable a cache on products for a lower POS loading time.",

    'description': """
This creates a product cache per POS config. It drastically lowers the
time it takes to load a POS session with a lot of products.
    """,

    'category': 'Sales/Point of Sale',
    'version': '1.0',
    'depends': ['point_of_sale'],
    'data': [
        'data/pos_cache_data.xml',
        'views/res_config_settings_views.xml',


        ],
    'assets': {
        'point_of_sale.assets': [
            'ults_pos_redis_json/static/**/*',
        ],
    },
    'license': 'LGPL-3',

}
