# -*- coding: utf-8 -*-
import logging
import threading
from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError
from ..tools import dingtalk_tool as dt

_logger = logging.getLogger(__name__)


# 获取钉钉部门和员工信息
class DingTalkMcSynchronous(models.TransientModel):
    _name = 'dingtalk.mc.synchronous'
    _description = "组织结构同步"
    _rec_name = 'employee'

    RepeatType = [('name', '以名称判断'), ('id', '以钉钉ID')]

    company_ids = fields.Many2many('res.company', 'dingtalk_mc_companys_rel', string="要同步的公司", required=True,
                                   default=lambda self: [(6, 0, [self.env.user.company_id.id])])
    department = fields.Boolean(string=u'钉钉部门', default=True)

    repeat_type = fields.Selection(string=u'判断唯一', selection=RepeatType, default='name')
    employee = fields.Boolean(string=u'钉钉员工', default=True)

    #  同步数据(department,employee, dept_detail)开始
    def start_synchronous_data(self):
        """
        基础数据同步
        :return:
        """
        self.ensure_one()
        try:
            if self.department:
                self.synchronous_dingtalk_department(self.repeat_type)
            if self.employee:
                self.synchronous_dingtalk_employee(self.repeat_type)
        except Exception as e:
            raise UserError(e)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    # 同步department(员工的部门)
    def synchronous_dingtalk_department(self, repeat_type=None):
        """
        同步钉钉部门
        :return:
        """
        for company in self.company_ids:
            client = dt.get_client(self, dt.get_dingtalk_config(self, company))
            result = client.department.list(fetch_child=True)
            for res in result:
                data = {
                    'company_id': company.id,
                    'name': res.get('name'),
                    'ding_id': res.get('id'),
                }
                if repeat_type == 'name':
                    domain = [('name', '=', res.get('name')), ('company_id', '=', company.id)]
                else:
                    domain = [('ding_id', '=', res.get('id')), ('company_id', '=', company.id)]
                # 依赖hr_attendance模块,创建钉钉部门
                h_department = self.env['hr.department'].with_user(SUPERUSER_ID).search(domain)
                if h_department:
                    h_department.with_user(SUPERUSER_ID).write(data)
                else:
                    self.env['hr.department'].with_user(SUPERUSER_ID).create(data)
            self.env.cr.commit()
        return True

    # 同步获取employee(部门的员工)信息
    def synchronous_dingtalk_employee(self, repeat_type=None):
        """
        同步钉钉部门员工列表
        :return:
        """
        for company in self.company_ids:
            departments = self.env['hr.department'].with_user(SUPERUSER_ID).search([('ding_id', '!=', ''), ('company_id', '=', company.id)])
            client = dt.get_client(self, dt.get_dingtalk_config(self, company))
            for dept in departments:
                emp_offset = 0
                emp_size = 100
                while True:
                    _logger.info(">>>开始获取%s部门的员工", dept.name)
                    result_state = self.get_dingtalk_employees(client, dept, emp_offset, emp_size, company, repeat_type)
                    if result_state:
                        emp_offset = emp_offset + 1
                    else:
                        break
            self.env.cr.commit()
        return True

    # 根据获取的部门员工信息更新至odoo员工数据库中
    def get_dingtalk_employees(self, client, dept, offset, size, company, repeat_type=None):
        """
        获取部门成员（详情）
        :param client:
        :param dept:
        :param offset:
        :param size:
        :param company:
        :param repeat_type:
        :return:
        """
        try:
            result = client.user.list(dept.ding_id, offset, size, order='custom')
            for user in result.get('userlist'):
                data = {
                    'name': user.get('name'),  # 员工名称
                    'ding_id': user.get('userid'),  # 钉钉用户Id
                    'din_unionid': user.get('unionid'),  # 钉钉唯一标识
                    'mobile_phone': user.get('mobile'),  # 手机号
                    'work_phone': user.get('tel'),  # 分机号
                    'work_location': user.get('workPlace'),  # 办公地址
                    'notes': user.get('remark'),  # 备注
                    'job_title': user.get('position'),  # 职位
                    'work_email': user.get('email'),  # email
                    'din_jobnumber': user.get('jobnumber'),  # 工号
                    'department_id': dept.id,  # 部门
                    'ding_avatar_url': user.get('avatar') if user.get('avatar') else '',  # 钉钉头像url
                    'din_isSenior': user.get('isSenior'),  # 高管模式
                    'din_isAdmin': user.get('isAdmin'),  # 是管理员
                    'din_isBoss': user.get('isBoss'),  # 是老板
                    'din_isLeader': user.get('isLeader'),  # 是部门主管
                    'din_isHide': user.get('isHide'),  # 隐藏手机号
                    'din_active': user.get('active'),  # 是否激活
                    'din_isLeaderInDepts': user.get('isLeaderInDepts'),  # 是否为部门主管
                    'din_orderInDepts': user.get('orderInDepts'),  # 所在部门序位
                    'company_id': company.id
                }
                # 支持显示国际手机号
                if user.get('stateCode') != '86':
                    data.update({'mobile_phone': '+{}-{}'.format(user.get('stateCode'), user.get('mobile'))})
                if user.get('hiredDate'):
                    time_stamp = dt.timestamp_to_local_date(user.get('hiredDate'), self)
                    data.update({'din_hiredDate': time_stamp})
                if user.get('department'):
                    dep_din_ids = user.get('department')
                    dep_list = self.env['hr.department'].with_user(SUPERUSER_ID).search([('ding_id', 'in', dep_din_ids), ('company_id', '=', company.id)])
                    data.update({'department_ids': [(6, 0, dep_list.ids)]})
                if repeat_type == 'name':
                    domain = [('name', '=', user.get('name')), ('company_id', '=', company.id)]
                else:
                    domain = [('ding_id', '=', user.get('userid')), ('company_id', '=', company.id)]
                employee = self.env['hr.employee'].with_user(SUPERUSER_ID).search(domain)
                if employee:
                    employee.with_user(SUPERUSER_ID).write(data)
                else:
                    self.env['hr.employee'].with_user(SUPERUSER_ID).create(data)
            return result.get('hasMore')
        except Exception as e:
            raise UserError(e)


# 针对系统已存在的系统用户，将员工的相关系统用户以名字进行匹配后关联
class EmployeeToUser(models.TransientModel):
    _name = 'dingtalk.emp.related.users'
    _description = '批量关联用户'

    company_id = fields.Many2one(comodel_name='res.company', string="选择公司", required=True,
                                 default=lambda self: self.env.user.company_id)

    def related_user(self):
        """
        自动将没有关联用户的员工通过名称进行关联
        1.获取所有相关用户（user_id）为空的员工
        2.逐个将员工名称到系统用户（res.users）中匹配
            1.若存在，则将user的id写入到员工的相关用户（user_id）中
            2.若不存在，则跳过
        :return:
        """
        self.ensure_one()
        related = self.env['dingtalk.emp.related.users']
        company_id = self.company_id
        t = threading.Thread(target=related.start_related_user, args=(company_id))
        t.start()
        return True

    @api.model
    def start_related_user(self, company):
        with api.Environment.manage():
            with self.pool.cursor() as new_cr:
                new_cr.autocommit(True)
                self = self.with_env(self.env(cr=new_cr))
                # 查找未绑定系统用户的钉钉员工
                employees = self.env['hr.employee'].search([('user_id', '=', False), ('company_id', '=', company.id)])
                for emp in employees:
                    # 根据以名称来匹配系统用户
                    user = self.env['res.users'].with_user(SUPERUSER_ID).search([('name', '=', emp.name)], limit=1)
                    if user:
                        emp.write({'user_id': user.id})
