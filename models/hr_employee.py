# -*- coding: utf-8 -*-
import base64
import logging
import requests
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from ..tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


# 员工补充钉钉相关字段
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    OfficeStatus = [
        ('2', '试用期'), ('3', '正式'), ('5', '待离职'), ('-1', '无状态')
    ]

    ding_id = fields.Char(string='钉钉Id', index=True)
    din_unionid = fields.Char(string='Union标识', index=True)
    din_jobnumber = fields.Char(string='员工工号')
    ding_avatar = fields.Html('钉钉头像', compute='_compute_ding_avatar')
    ding_avatar_url = fields.Char('头像url')
    din_hiredDate = fields.Date(string='入职时间')
    din_isAdmin = fields.Boolean("是管理员", default=False)
    din_isBoss = fields.Boolean("是老板", default=False)
    din_isLeader = fields.Boolean("是部门主管", default=False)
    din_isHide = fields.Boolean("隐藏手机号", default=False)
    din_isSenior = fields.Boolean("高管模式", default=False)
    din_active = fields.Boolean("是否激活", default=True)
    din_orderInDepts = fields.Char("所在部门序位")
    din_isLeaderInDepts = fields.Char("是否为部门主管")
    work_status = fields.Selection(string=u'入职状态', selection=[('1', '待入职'), ('2', '在职'), ('3', '离职')], default='2')
    office_status = fields.Selection(string=u'在职子状态', selection=OfficeStatus, default='-1')
    department_ids = fields.Many2many('hr.department', 'emp_dept_dingtalk_rel', string='所属部门')


