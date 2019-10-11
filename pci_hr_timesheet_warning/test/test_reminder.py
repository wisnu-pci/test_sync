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
        self.holiday = self.env['hr.holidays']
        self.holiday = self.env['hr.holidays.status']
        self.pricelist = self.env["product.pricelist"]  # pricelist
        self.partner = self.env["res.partner"]  # customer
        self.project = self.env["project.project"]  # project
        self.task = self.env["project.task"]  # task
        self.analytic_line = self.env['account.analytic.line']  # timesheet
        self.order = self.env["sale.order"]  # so
        self.order_line = self.env["sale.order.line"]  # so line
        self.date = datetime.now().strftime('%Y-%m-%d')
        self.date_now = datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S')
        self.tgl_now = datetime.strptime(self.date, '%Y-%m-%d')
        self.dt_emp_active = self.env['hr.employee'].search([('active', '=', True)], order='id asc', limit=100).ids
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
        self.emp_selected = self.env['hr.emplyee'].browse(self.dt_emp_active[50])
        vals = {'name': 'liburan 1',
                'holiday_type':'employee',
                'employee_id': self.emp_selected.id,
                'holiday_status_id': self.unpaid,
                'date_from': self.date_now+timedelta(day=-1),
                'date_to': self.date_now+timedelta(hours=8),
                'number_of_days_temp':2,
                'state':'validate'}
        self.created_leave = self.holiday.create(vals)
        self.emp_selected = self.env['hr.emplyee'].browse(self.dt_emp_active[80])
        vals = {'name': 'liburan 2',
                'holiday_type': 'employee',
                'employee_id': self.emp_selected.id,
                'holiday_status_id': self.sick_leave,
                'date_from': self.date_now + timedelta(day=-2),
                'date_to': self.date_now + timedelta(hours=9),
                'number_of_days_temp': 3,
                'state':'validate'}
        self.created_leave = self.holiday.create(vals)
        self.emp_selected = self.env['hr.emplyee'].browse(self.dt_emp_active[70])
        vals = {'name': 'liburan 3',
                'holiday_type': 'employee',
                'employee_id': self.emp_selected.id,
                'holiday_status_id': self.sick_leave,
                'date_from': self.date_now + timedelta(day=-1),
                'date_to': self.date_now + timedelta(hours=9),
                'number_of_days_temp': 2,
                'state': 'validate'}
        self.created_leave = self.holiday.create(vals)
        self.emp_selected = self.env['hr.emplyee'].browse(self.dt_emp_active[60])
        vals = {'name': 'liburan 4',
                'holiday_type': 'employee',
                'employee_id': self.emp_selected.id,
                'holiday_status_id': self.sick_leave,
                'date_from': self.date_now + timedelta(day=-3),
                'date_to': self.date_now + timedelta(hours=9),
                'number_of_days_temp': 4,
                'state': 'confirm'}
        self.created_leave = self.holiday.create(vals)
        self.emp_selected = self.env['hr.emplyee'].browse(self.dt_emp_active[40])
        vals = {'name': 'liburan 5',
                'holiday_type': 'employee',
                'employee_id': self.emp_selected.id,
                'holiday_status_id': self.sick_leave,
                'date_from': self.date_now + timedelta(day=-2),
                'date_to': self.date_now + timedelta(hours=9),
                'number_of_days_temp': 3,
                'state': 'confirm'}
        self.created_leave = self.holiday.create(vals)
        _logger.info('mulai isi timesheet semua udah di approve')
        dt_emp ={'emp': 55, 'amount': 7.99},{'emp': 65, 'amount': 7.67},{'emp': 75, 'amount': 7.87},
                {'emp': 85, 'amount': 8.1},{'emp': 95, 'amount': 7.99},{'emp': 70, 'amount': 8.0},
                {'emp': 80, 'amount': 7.59},{'emp': 99, 'amount': 7.4},{'emp': 45, 'amount': 7.3},
                {'emp': 83, 'amount': 7.2},{'emp': 73, 'amount': 7.0}]
        for this in dt_emp:
            vals = {'date': self.tgl_now+timedelta(days=-1),
                    'name': 'task rame',
                    'project_id': self.project_2.id,
                    'employee_id': this.get('emp'),
                    'task_id': self.task4.id,
                    'unit_amount': this.get('amount')}
            self.timesheet4 = self.analytic_line.create(vals)
        for this in dt_emp:
            vals = {'date': self.tgl_now,
                    'name': 'task rame',
                    'project_id': self.project_2.id,
                    'employee_id': this.get('emp'),
                    'task_id': self.task4.id,
                    'unit_amount': this.get('amount'),
                    'state':'approve'}
            print('one more time, one more changes ',vals)
            self.dt_timesheet = self.analytic_line.create(vals)
        self.env['timesheet.warning'].check_timesheet_reminder()
        _logger.inf('selesai..................')
