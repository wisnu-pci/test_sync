import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class TimesheetReminderFriday(models.Model):
    """ Model for Timesheet Reminder """
    _inherit = 'timesheet.warning'

    @api.model
    def send_reminder_email_friday(self, employee_id, date):
        """ Send timesheet reminder email for Friday. """
        employee = self.env['hr.employee'].browse(employee_id)
        mail_obj = self.env['timesheet.mail']
        mail = mail_obj.search([('name', '=', 'Timesheet Reminder Friday')])
        if mail:
            try:
                email = [employee.user_id.email]
                email_to = ','.join(email)
                content = """%s""" % mail.email_template
                body_email = content % employee.user_id.name
                email = self.env.ref('pci_hr_timesheet_warning.template_reminder_message_friday')
                email.write({
                    'subject': 'Friday Timesheet Reminder : ' + employee.name + ' - ' + date,
                    'email_to': email_to,
                    'email_cc': '',
                    'body_html': body_email})
                email.send_mail(employee.id, force_send=True)

            except Exception as error:
                _logger.error(error, exc_info=True)

    @api.model
    def check_timesheet_reminder_for_friday(self):
        """ Check and create timesheet reminder for Friday. """
        _logger.info('======== Starting Friday Timesheet Reminder ========')
        date = self.get_today()
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
        timesheet_warning = 'holiday_status_id.check_timesheet_warning'
        if date.strftime('%A') == 'Friday':
            for emp in empl.search([(line1, '!=', False), (line2, '=', True),
                                    (line3, '=', False), (line4, '!=', holiday_country)]):
                leave = self.env['hr.holidays'].search([('employee_id', '=', emp.id),
                                                        ('date_from', '<=', date_check),
                                                        ('date_to', '>=', date_check),
                                                        ('state', '=', 'validate'),
                                                        (timesheet_warning, '=', False)])
                domain = [('date', '=', date_check), ('employee_id', '=', emp.id),
                          ('state', 'in', ('open', 'approve'))]
                res = line.read_group(domain=domain,
                                      fields=['employee_id', 'unit_amount', 'amount', 'id'],
                                      groupby=['employee_id'])

                if len(leave) == 0:
                    if not res:
                        _logger.info(res)
                        self.send_reminder_email_friday(emp.id, date.strftime('%d-%m-%Y'))
                    else:
                        if res[0]['unit_amount'] < 8:
                            _logger.info(res)
                            self.send_reminder_email_friday(emp.id, date.strftime('%d-%m-%Y'))
