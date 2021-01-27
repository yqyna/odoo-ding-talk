# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api, SUPERUSER_ID
from odoo.exceptions import UserError
from ..tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


class HrDepartment(models.Model):
    _inherit = 'hr.department'
    _name = 'hr.department'

    ding_id = fields.Char(string='钉钉Id', index=True)