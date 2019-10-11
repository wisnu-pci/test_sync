import logging
import re
from datetime import datetime, timedelta

import pytz

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class TimesheetWarning(models.Model):
    """ Model for Timesheet Warning """
    _name = 'timesheet.warning'
    _description = 'Timesheet Warning'
    _inherit = ['mail.thread']

    name = fields.Many2one('hr.employee', string='Employee')
    quarter_id = fields.Many2one('timesheet.warning.quarter', string='Quarter')
    n_warning = fields.Char(string='Warning Number', compute='_compute_number_warning')
    date = fields.Datetime()
    state = fields.Selection([('draft', 'Draft'), ('applied', 'Applied'), ('excused', 'Excused'), \
                              ('system_mistake', 'System Mistake'), ], string='Status', \
                             index=True, track_visibility="onchange", default='draft')

    def get_today(self):
        """ Obtain today's date based on user local timezone. """
        user = self.env.user
        timezone = pytz.timezone(user.tz)
        now = pytz.utc.localize(datetime.now()).astimezone(timezone)
        return now

    @api.onchange('date')
    def onchange_date(self):
        """ Set the quarter period whenever the date is changed. """
        if self.date:
            quarter = self.env['timesheet.warning.quarter']
            date = self.date
            s_date = 'start_date'
            e_date = 'end_date'
            quarter = quarter.search([(s_date, '<=', date), (e_date, '>=', date)], limit=1)
            if quarter:
                self.quarter_id = quarter.id

    @api.multi
    @api.depends('state', 'date', 'quarter_id')
    def _compute_number_warning(self):
        """ Obtain the amount of warnings during this quarter. """
        for this in self:
            this.n_warning = '/'
            if this.state == 'applied':
                warnings = self.search([('name', '=', this.name.id),
                                        ('quarter_id', '=', this.quarter_id.id),
                                        ('date', '<=', this.date), ('state', '=', 'applied')])
                number = len(warnings)
                suffixes = ['th', 'st', 'nd', 'rd', ] + ['th'] * 17 + ['st', 'nd', 'rd', ] + ['th'] * 7
                this.n_warning = str(number) + suffixes[number % 100] + ' warning'

    @api.model
    def create(self, vals):
        """ Add followers during timesheet warning creation. """
        res = super(TimesheetWarning, self).create(vals)
        followers = []
        employee_vals = vals.get('name')
        if employee_vals:
            employee_id = self.env['hr.employee'].browse(employee_vals)
            if employee_id.coach_id and employee_id.coach_id.user_id:
                coach_id = employee_id.coach_id.user_id.partner_id.id
                followers.append(coach_id)
            group_warning = 'pci_hr_timesheet_warning.pci_group_timesheet_warning'
            group_timesheet = self.env['ir.model.data'].xmlid_to_res_id(group_warning)
            group_id = self.env['res.groups'].search([('id', '=', group_timesheet)])
            for user in group_id.users:
                res_partner = user.partner_id.id
                if res_partner not in followers:
                    followers.append(res_partner)
            if followers:
                res.message_subscribe(followers)
        return res

    @api.multi
    def write(self, vals):
        """ Send email during timesheet warning update. """
        res = super(TimesheetWarning, self).write(vals)
        admin_uid = self.env.ref('base.user_root').id
        for this in self:
            if vals.get('state') == 'applied':
                n_warning = self.n_warning
                if re.search(r'\d+', self.n_warning) is not None:
                    regex = int(re.search(r'\d+', n_warning).group())
                    this.sudo(admin_uid).send_email_warning(regex, this.name.id)
        return res

    @api.multi
    def send_email_warning(self, n_warning, employee_id, date=None):
        if date is None:
            now = self.get_today()
            date = now - timedelta(days=1)

        employee = self.env['hr.employee'].browse(employee_id)
        mail_obj = self.env['timesheet.mail']
        seq = 'sequence asc'
        mails = mail_obj.search([('type', '=', 'warning')], limit=n_warning, order=seq)
        mail = False
        for msg in mails:
            mail = msg

        if mail:
            try:
                email_hr = 'hr@portcities.net'
                email_cc = ''
                email_l = [email_hr]
                if employee.coach_id and employee.coach_id.user_id:
                    email_l.append(employee.coach_id.user_id.email)
                email_cc = ','.join(email_l)

                content = """%s""" % mail.email_template
                suffixes = ['th', 'st', 'nd', 'rd', ] + ['th'] * 17 + ['st', 'nd', 'rd', ] + ['th'] * 7
                n_warning_str = '%d%s' % (n_warning, suffixes[n_warning % 100]) + ' warning'
                body_email = content % (employee.user_id.name, n_warning_str)
                email = self.env.ref('pci_hr_timesheet_warning.template_warning_timesheet')
                subject1 = employee.name + ' - ' + date.strftime('%d-%m-%Y')
                email.write({'subject': 'Timesheet Warning : ' + subject1,
                             'email_to': employee.user_id.email,
                             'email_cc': email_cc,
                             'body_html': body_email})
                email.send_mail(self.id, force_send=True)

            except Exception as error:
                _logger.error(error, exc_info=True)

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'excused':
            return 'pci_hr_timesheet_warning.timesheet_warning_excused'
        elif 'state' in init_values and self.state == 'system_mistake':
            return 'pci_hr_timesheet_warning.timesheet_warning_system_mistake'
        return super(TimesheetWarning, self)._track_subtype(init_values)

    @api.model
    def create_timesheet_warning(self, employee_id, date):
        """ Generate timesheet warning for the specified employee. """
        employee = self.env['hr.employee'].browse(employee_id)
        date = date.strftime('%Y-%m-%d')
        quarter_obj = self.env['timesheet.warning.quarter']
        quarter = quarter_obj.search([('start_date', '<=', date), ('end_date', '>=', date)], limit=1)
        new_warning = self.env['timesheet.warning'].create({'name': employee.id,
                                                            'quarter_id': quarter.id,
                                                            'date': date})
        new_warning.write({'state': 'applied'})

    @api.model
    def check_timesheet_warning(self):
        """ Check and generate timesheet warning based on yesterday's data. """
        _logger.info('===== Checking Timesheet Warning =====')
        now = self.get_today()
        yesterday = now - timedelta(days=1)
        date_check = yesterday.strftime('%Y-%m-%d')

        holiday_line = self.env['hr.holidays.public.line']
        holiday_src = holiday_line.search([('date', '=', date_check)])
        holiday_country = holiday_src.year_id.country_id.name
        empl = self.env['hr.employee']
        line = self.env['account.analytic.line']
        line1 = 'user_id'
        line2 = 'active'
        line3 = 'timesheet_exception'
        line4 = 'address_id.country_id.name'
        check_warning = 'holiday_status_id.check_timesheet_warning'
        if yesterday.strftime('%A') not in ('Saturday', 'Sunday'):
            for emp in empl.search([(line1, '!=', False), (line2, '=', True),
                                    (line3, '=', False), (line4, '!=', holiday_country)]):
                _logger.info('- %s', emp.name)
                holidays = self.env['hr.holidays'].search([('employee_id', '=', emp.id),
                                                           ('date_from', '<=', date_check),
                                                           ('date_to', '>=', date_check),
                                                           ('state', '=', 'validate'),
                                                           ('type', '=', 'remove'),
                                                           (check_warning, '=', False)])
                domain = [('date', '=', date_check), ('employee_id', '=', emp.id),
                          ('state', 'in', ('open', 'approve'))]
                res = line.read_group(domain=domain,
                                      fields=['employee_id', 'unit_amount', 'amount', 'id'],
                                      groupby=['employee_id'])

                if len(holidays) == 0:
                    if not res:
                        _logger.info(res)
                        self.create_timesheet_warning(emp.id, yesterday)
                    else:
                        if res[0]['unit_amount'] < 8:
                            _logger.info(res)
                            self.create_timesheet_warning(emp.id, yesterday)


class TimesheetWarningQuarter(models.Model):
    """ Model for Timesheet Warning Quarter """
    _name = 'timesheet.warning.quarter'
    _description = 'Timesheet Warning Quarter'

    name = fields.Char()
    start_date = fields.Date(default=fields.Date.context_today)
    end_date = fields.Date(default=fields.Date.context_today)


class TimesheetMail(models.Model):
    """ Model for Timesheet Mail """
    _name = 'timesheet.mail'
    _order = 'type asc, sequence asc'
    _description = 'Timesheet Mail Configuration'

    name = fields.Char(required=True)
    email_template = fields.Html(string='Email Content')
    type = fields.Selection([('warning', 'Warning'), ('reminder', 'Reminder')], default='warning')
    sequence = fields.Integer()
