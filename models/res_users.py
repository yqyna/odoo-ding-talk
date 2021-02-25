# -*- coding: utf-8 -*-
import logging
import threading
from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import AccessDenied


_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = ['res.users']

    ding_user_phone = fields.Char(string='钉钉登录手机', index=True)
    ding_user_id = fields.Char(string='钉钉访问令牌', index=True)

    @api.model
    def create(self, values):
        user = super(ResUsers, self).create(values)
        config = self.env['dingtalk.message.config'].is_new_user_send_msg()
        if config and user.employee:
            employee = None
            for emp in user.employee_ids:
                if emp.ding_id:
                    employee = emp
                    break
            if employee:
                msg_body = config.msg_body
                ding_id = employee.ding_id
                message_tool = self.env['dingtalk.message.tool']
                threading.Thread(target=message_tool.send_create_user_message,
                                 args=(employee.company_id, ding_id, msg_body, user.id)).start()
        return user

    @api.model
    def auth_oauth(self, provider, params):
        if provider == 'dingtalk':
            user = self.search([('ding_user_id', '=', params)], limit=1)
            if not user:
                _logger.info(">>>员工关联的用户不正确或则未关联成功.")
                return False
            return (self.env.cr.dbname, user[0].login, params)
        else:
            return super(ResUsers, self).auth_oauth(provider, params)

    @api.model
    def _check_credentials(self, password, env):
        try:
            return super(ResUsers, self)._check_credentials(password, env)
        except AccessDenied:
            res = self.with_user(SUPERUSER_ID).search([('id', '=', self.env.uid), ('ding_user_id', '=', password)])
            if not res:
                raise

