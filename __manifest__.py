# -*- coding: utf-8 -*-
{
    'name': "Odoo钉钉",
    'summary': """Odoo钉钉模块""",
    'description': """Odoo钉钉模块""",
    'category': 'dingtalk',
    'version': '14.0',
    'depends': ['base', 'hr', 'mail', 'auth_oauth', 'hr_attendance'],
    'external_dependencies': {
        'python': ['pypinyin', 'pycryptodome', 'dingtalk-sdk'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/auth_oauth_data.xml',
        'views/dingtalk_menus.xml',
        'views/dingtalk_config.xml',
        'views/dingtalk_login_template.xml',
        'views/dingtalk_message_log.xml',
        'data/default_message_config.xml',
        'views/dingtalk_msg_config.xml',

        'wizard/synchronous.xml',
    ],
    'qweb': [
        'static/xml/*.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    'license': 'AGPL-3',
}
