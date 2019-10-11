import logging
from odoo.tests import common
from datetime import datetime, timedelta
_logger = logging.getLogger(__name__)

class TestReminder(common.TransactionCase):
    at_install = True
    post_install = True

    def test_reminder(self):
        _logger.info('membuat master data >>>')
        self.company_id = self.env.ref('base.main_company')
        self.currency_id = self.env.ref('base.EUR')
        self.sick_leave = self.env.ref('hr_holidays.holiday_status_sl')
        self.unpaid = self.env.ref('hr_holidays.holiday_status_unpaid')

        self.master_employee = self.env['hr.employee']
        self.warning = self.env['timesheet.warning']
        self.holiday = self.env['hr.holidays']
        self.mail = self.env['mail.mail']
        self.holiday = self.env['hr.holidays.status']
        self.pricelist = self.env["product.pricelist"]  # pricelist
        self.partner = self.env["res.partner"]  # customer
        self.project = self.env["project.project"]  # project
        self.task = self.env["project.task"]  # task
        self.analytic_line = self.env['account.analytic.line']  # timesheet
        self.order = self.env["sale.order"]  # so
        self.order_line = self.env["sale.order.line"]  # so line
        self.date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.date_now = datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S')
        self.tgl_date = datetime.now().strftime('%Y-%m-%d')
        self.tgl_now = datetime.strptime(self.tgl_date, '%Y-%m-%d')
        self.dt_emp_active = self.master_employee.search([('active', '=', True)], order='id asc', limit=100).ids
        _logger.info('---{buat pricelist }---')
        vals = {'name': 'Eur',
                'currency_id': self.currency_id.id,
                'selectable': True,
                'company_id': self.company_id.id}
        self.eur_pricelist = self.pricelist.create(vals)
        _logger.info('---{buat partner }---')
        vals = {'company_type': 'person',
                'name': 'Ruman',
                'street': 'jalan kemana saja',
                'phone': '082313774850',
                'email': 'ruman@gmail.com'}
        self.partner_1 = self.partner.create(vals)
        vals = {'company_type': 'person',
                'name': 'Namur',
                'street': 'jalan kemana saja yang penting sampai',
                'phone': '082313774123',
                'email': 'ruman@gmail.com'}
        self.partner_2 = self.partner.create(vals)
        _logger.info('---{buat project}---')
        vals = {'name': 'Ruman',
                'alias_name': 'Ruman',
                'allows_timesheets': True}
        self.project_1 = self.project.create(vals)
        vals = {'name': 'Namur',
                'alias_name': 'Namur',
                'allows_timesheets': True}
        self.project_2 = self.project.create(vals)
        _logger.info('---{buat task}---')
        vals = {'name': 'Ruman 1', 'project_id': self.project_1.id}
        self.task1 = self.task.create(vals)
        vals = {'name': 'Ruman 2', 'project_id': self.project_1.id}
        self.task2 = self.task.create(vals)
        vals = {'name': 'Namur 1', 'project_id': self.project_2.id}
        self.task3 = self.task.create(vals)
        vals = {'name': 'Namur 2', 'project_id': self.project_2.id}
        self.task4 = self.task.create(vals)
        self.account1_id = self.env['account.analytic.account'].search([('name', '=', self.partner_1.name)])
        self.account2_id = self.env['account.analytic.account'].search([('name', '=', self.partner_2.name)])
        _logger.info('membuat cuti dengan 3 approved dan 2 approve')
        # [50, 60, 70, 80, 40]
        self.emp_selected = self.master_employee.browse(self.dt_emp_active[50])
        vals = {'name': 'liburan 1',
                'holiday_type':'employee',
                'employee_id': self.emp_selected.id,
                'holiday_status_id': self.unpaid,
                'date_from': self.date_now+timedelta(days=-1),
                'date_to': self.date_now+timedelta(hours=8),
                'number_of_days_temp':2,
                'state':'validate'}
        self.created_leave = self.holiday.create(vals)
        self.emp_selected = self.master_employee.browse(self.dt_emp_active[80])
        vals = {'name': 'liburan 2',
                'holiday_type': 'employee',
                'employee_id': self.emp_selected.id,
                'holiday_status_id': self.sick_leave,
                'date_from': self.date_now + timedelta(days=-2),
                'date_to': self.date_now + timedelta(hours=9),
                'number_of_days_temp': 3,
                'state':'validate'}
        self.created_leave = self.holiday.create(vals)
        self.emp_selected = self.master_employee.browse(self.dt_emp_active[70])
        vals = {'name': 'liburan 3',
                'holiday_type': 'employee',
                'employee_id': self.emp_selected.id,
                'holiday_status_id': self.sick_leave,
                'date_from': self.date_now + timedelta(days=-1),
                'date_to': self.date_now + timedelta(hours=9),
                'number_of_days_temp': 2,
                'state': 'validate'}
        self.created_leave = self.holiday.create(vals)
        self.emp_selected = self.master_employee.browse(self.dt_emp_active[60])
        vals = {'name': 'liburan 4',
                'holiday_type': 'employee',
                'employee_id': self.emp_selected.id,
                'holiday_status_id': self.sick_leave,
                'date_from': self.date_now + timedelta(days=-3),
                'date_to': self.date_now + timedelta(hours=9),
                'number_of_days_temp': 4,
                'state': 'confirm'}
        self.created_leave = self.holiday.create(vals)
        self.emp_selected = self.master_employee.browse(self.dt_emp_active[40])
        vals = {'name': 'liburan 5',
                'holiday_type': 'employee',
                'employee_id': self.emp_selected.id,
                'holiday_status_id': self.sick_leave,
                'date_from': self.date_now + timedelta(days=-2),
                'date_to': self.date_now + timedelta(hours=9),
                'number_of_days_temp': 3,
                'state': 'confirm'}
        self.created_leave = self.holiday.create(vals)
        _logger.info('mulai isi timesheet semua udah di approve')

        dt_emp =[{'emp': 54, 'amount': 7.99},{'emp': 69, 'amount': 8.67},{'emp': 75, 'amount': 7.87},
        {'emp': 85, 'amount': 8.1},{'emp': 96, 'amount': 7.99},{'emp': 70, 'amount': 8.0},
        {'emp': 80, 'amount': 7.59},{'emp': 97, 'amount': 7.4},{'emp': 47, 'amount': 7.3},
        {'emp': 88, 'amount': 7.2},{'emp': 79, 'amount': 7.0},{'emp': 50, 'amount': 0},
        {'emp': 60, 'amount': 0},{'emp': 40, 'amount': 0}]
        for this in dt_emp:
            vals = {'date': self.tgl_now+timedelta(days=-1),
                    'name': 'task rame',
                    'project_id': self.project_2.id,
                    'employee_id': this.get('emp'),
                    'task_id': self.task4.id,
                    'unit_amount': this.get('amount')}
            self.timesheet4 = self.analytic_line.create(vals)
            vals = {'date': self.date_now,
                    'name': 'task empat',
                    'project_id': self.project_2.id,
                    'employee_id': self.dt_emp_active[3],
                    'task_id': self.task4.id,
                    'unit_amount': 8}
            self.timesheet4 = self.analytic_line.create(vals)
        for this in dt_emp:
            vals = {'date': self.tgl_now,
                    'name': 'task rame',
                    'project_id': self.project_2.id,
                    'employee_id': this.get('emp'),
                    'task_id': self.task4.id,
                    'unit_amount': this.get('amount'),
                    'state':'approve'}
            self.timesheet4 = self.analytic_line.create(vals)
        _logger.info('mulai..................remaindernya')
        self.env['timesheet.warning'].check_timesheet_reminder()
        _logger.info('pengecekan reminder email yang terkirim siapa saja : ')
        for this in dt_emp:
            emp = self.master_employee.browse(this.get('emp'))
            mail = self.mail.search([('email_to','ilike',emp.work_email),
                                     ('date','>',self.tgl_date+' 00:00:00')],
                                    order='id desc', limit=10)
            self.domain = [('date', '=', self.tgl_date), ('employee_id', '=', emp.id),
                      ('state', 'in', ('open', 'approve'))]
            self.line_timesheet = self.analytic_line.read_group(domain=self.domain,
                       fields=['employee_id', 'unit_amount', 'amount', 'id'],
                       groupby=['employee_id'])
            for email in mail:
                if email.email_to.find(emp.work_email) == 0:
                    _logger.info('terkirim atas id %s dengan nama %s dan total jam %s', emp.id, emp.name,self.line_timesheet[0]['unit_amount'])
        _logger.info('selesai..................remaindernya')
        _logger.info('mulai..................warningnya')
        self.env['timesheet.warning'].check_timesheet_warning()
        _logger.info('pengecekan email warning yang terkirim siapa saja : ')
        for this in dt_emp:
            emp = self.master_employee.browse(this.get('emp'))
            mail = self.mail.search([('email_to', 'ilike', emp.work_email),
                                     ('date', '>', self.tgl_date + ' 00:00:00')],
                                    order='id desc', limit=10)
            self.domain = [('date', '=', self.tgl_date), ('employee_id', '=', emp.id),
                           ('state', 'in', ('open', 'approve'))]
            self.line_timesheet = self.analytic_line.read_group(domain=self.domain,
                                                                fields=['employee_id', 'unit_amount', 'amount', 'id'],
                                                                groupby=['employee_id'])
            for email in mail:
                if email.email_to.find(emp.work_email) == 0:
                    _logger.info('terkirim atas id %s dengan nama %s dan total jam %s', emp.id, emp.name,
                                 self.line_timesheet[0]['unit_amount'])
        _logger.info('selesai..................warningnya')
