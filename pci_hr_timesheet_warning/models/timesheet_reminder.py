import logging
from datetime import timedelta

from odoo import api, models

_logger = logging.getLogger(__name__)


class TimesheetReminder(models.Model):
    """ Model for Timesheet Reminder """
    _inherit = 'timesheet.warning'

    @api.model
    def send_reminder_email(self, employee_id, date):
        """ Send timesheet reminder email. """
        employee = self.env['hr.employee'].browse(employee_id)
        mail = self.env.ref('pci_hr_timesheet_warning.new_reminder_message')
        if mail:
            try:
                emails = [employee.user_id.email]
                if employee.coach_id and employee.coach_id.user_id:
                    emails.append(employee.coach_id.user_id.email)
                email_to = ','.join(emails)

                content = """%s""" % mail.email_template
                body_email = content % employee.user_id.name
                email = self.env.ref('pci_hr_timesheet_warning.template_reminder_message')
                email.write({'subject': 'Timesheet Reminder : ' + employee.name + ' - ' + date,
                             'email_to': email_to,
                             'email_cc': '',
                             'body_html': body_email})
                email.send_mail(employee.id, force_send=True)

            except Exception as error:
                _logger.error(error, exc_info=True)

    @api.model
    def check_timesheet_reminder(self, check_prev_day=None):
        """ Check and create timesheet reminder. """
        _logger.info('========= Starting Timesheet Reminder =========')
        date = self.get_today()
        date_check = date.strftime('%Y-%m-%d')
        if check_prev_day:
            date = date - timedelta(days=1)
            date_check = date.strftime('%Y-%m-%d')

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
        if date.strftime('%A') not in ('Saturday', 'Sunday'):
            for emp in empl.search([(line1, '!=', False), (line2, '=', True),
                                    (line3, '=', False), (line4, '!=', holiday_country)]):
                holidays = self.env['hr.holidays'].search([('employee_id', '=', emp.id),
                                                           ('date_from', '<=', date_check),
                                                           ('date_to', '>=', date_check),
                                                           ('state', '=', 'validate'),
                                                           (check_warning, '=', False)])
                domain = [('date', '=', date_check), ('employee_id', '=', emp.id),
                          ('state', 'in', ('open', 'approve'))]
                res = line.read_group(domain=domain,
                                      fields=['employee_id', 'unit_amount', 'amount', 'id'],
                                      groupby=['employee_id'])

                if len(holidays) == 0:
                    if not res:
                        _logger.info(res)
                        self.send_reminder_email(emp.id, date.strftime('%d-%m-%Y'))
                    else:
                        if res[0]['unit_amount'] < 8:
                            _logger.info(res)
                            self.send_reminder_email(emp.id, date.strftime('%d-%m-%Y'))
