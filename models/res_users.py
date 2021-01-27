# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, SUPERUSER_ID


_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = ['res.users']

    ding_user_phone = fields.Char(string='钉钉登录手机', index=True)
    ding_user_id = fields.Char(string='钉钉访问令牌', index=True)