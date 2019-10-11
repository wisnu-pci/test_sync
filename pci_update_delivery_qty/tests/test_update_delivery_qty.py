# -*- coding: utf-8 -*-
# ©  2015 Salton Massally <smassally@idtlabs.sl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo.tests import common
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError,UserError
_logger = logging.getLogger(__name__)

class TestUpdateDeliveryQty(common.TransactionCase):
    at_install = True
    post_install = True

    def test_page(self):
        self.company_id = self.env.ref('base.main_company')
        self.currency_id = self.env.ref('base.EUR')
        self.pricelist = self.env["product.pricelist"] #pricelist
        self.partner = self.env["res.partner"] #customer
        self.project = self.env["project.project"] #project
        self.task = self.env["project.task"] #task
        self.analytic_line = self.env['account.analytic.line'] #timesheet
        self.order = self.env["sale.order"] #so
        self.order_line = self.env["sale.order.line"]#so line
        self.date = datetime.now().strftime('%Y-%m-%d')
        self.date_now = datetime.strptime(self.date, '%Y-%m-%d')
        self.dt_emp_active = self.env['hr.employee'].search([('active','=',True)], order='id asc', limit=10).ids
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
        vals={'name': 'Ruman 1', 'project_id': self.project_1.id}
        self.task1 = self.task.create(vals)
        vals = {'name': 'Ruman 2', 'project_id': self.project_1.id}
        self.task2 = self.task.create(vals)
        vals = {'name': 'Namur 1', 'project_id': self.project_2.id}
        self.task3 = self.task.create(vals)
        vals = {'name': 'Namur 2', 'project_id': self.project_2.id}
        self.task4 = self.task.create(vals)
        self.account1_id = self.env['account.analytic.account'].search([('name','=',self.partner_1.name)])
        self.account2_id = self.env['account.analytic.account'].search([('name', '=', self.partner_2.name)])
        _logger.info('---{buat sale order}---')
        vals = {'partner_id': self.partner_1.id,
                'analytic_account_id': self.account1_id.id,
                'start_date': self.date_now,
                'date_close': self.date_now + timedelta(days=320),}
        self.so1 = self.order.create(vals)
        vals = {'partner_id': self.partner_2.id,
                'start_date': self.date_now + timedelta(days=-120),
                'date_close': self.date_now + timedelta(days=120), }
        self.so2 = self.order.create(vals)
        self.so1.action_confirm()
        _logger.info('---{testing langsung update delivery qty dengan so1 [blm ada timesheet]}---')
        self.update_qty_deliver = self.env['update.delivery.qty.sale']
        vals = {
            'date_to': self.date_now,
        }
        self.qty_update = self.update_qty_deliver.with_context(active_id=self.so1.id).create(vals)
        with self.assertRaises(UserError):
            self.qty_update.action_update_delivery_qty_sale()
        _logger.info('---{insert timesheet }---')
        vals = {'date': self.date_now,
                'name': 'task pertama',
                'project_id': self.project_1.id,
                'task_id': self.task1.id,
                'employee_id': self.dt_emp_active[0],
                'unit_amount': 4.99}
        self.timesheet1 = self.analytic_line.create(vals)
        vals = {
            'date_to': self.date_now + timedelta(days=1),
        }
        self.qty_update = self.update_qty_deliver.with_context(active_id=self.so1.id).create(vals)
        self.qty_update.action_update_delivery_qty_sale()
        _logger.info('---{insert timesheet }---')
        vals = {'date': self.date_now,
                'name': 'keterangan kedua',
                'project_id': self.project_1.id,
                'task_id': self.task1.id,
                'employee_id': self.dt_emp_active[7],
                'unit_amount': 4.59}
        self.timesheet1 = self.analytic_line.create(vals)
        vals = {'date': self.date_now,
                'name': 'keterangan ketiga',
                'project_id': self.project_1.id,
                'task_id': self.task1.id,
                'employee_id': self.dt_emp_active[9],
                'unit_amount': 0.58}
        self.timesheet1 = self.analytic_line.create(vals)
        vals = {'date': self.date_now,
               'name': 'task dua',
               'project_id': self.project_1.id,
               'employee_id': self.dt_emp_active[1],
               'task_id': self.task2.id,
               'unit_amount': 2.5}
        self.timesheet2 = self.analytic_line.create(vals)
        vals = {'date': self.date_now,
                'name': 'task empat',
                'project_id': self.project_2.id,
                'employee_id': self.dt_emp_active[3],
                'task_id': self.task4.id,
                'unit_amount': 8}
        self.timesheet4 = self.analytic_line.create(vals)
        vals = {
            'date_to': self.date_now + timedelta(days=1),
        }
        self.qty_update2 = self.update_qty_deliver.with_context(active_id=self.so2.id).create(vals)
        with self.assertRaises(UserError):
            self.qty_update2.action_update_delivery_qty_sale()
        self.so2.write({'analytic_account_id': self.account2_id.id})
        self.so2.action_confirm()
