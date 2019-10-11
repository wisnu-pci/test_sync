{
    'name': 'Timesheet Warning and Reminder',
    'version': '1.0',
    'depends': ['base',
                'hr_timesheet',
                'hr',
                'hr_attendance',
                'analytic',
                'hr_holidays',
                'hr_public_holidays'],
    'author': 'Port Cities',
    'description': """
Timesheet Warning and Reminder
==================================
In Menu Timesheets, create new tab Timesheet Warning

There are 3 sub menu in tab Timesheet Warning :\n
    - Warnings\n
    - Quarters\n
    - Email Template\n

Create template email for :\n
    - Email Timesheet Reminder\n
    - Email Timesheet Warning\n

Create Scheduler for :\n
    - Timesheet Reminder\n
    - Timesheet Warning\n

Create datas for :\n
    - Timesheet Quarter Data\n
    - Subtype Data on Timesheet Warning\n

Create group and access right for Timesheet Warning\n
        Contributor : Irwinda & Nisfa
    """,
    'website': 'http://portcities.net',
    'category': 'HR Timesheet',
    'sequence': 1,
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/template_reminder.xml',
        'data/template_reminder_friday.xml',
        'data/template_warning.xml',
        'data/timesheet_quarter.xml',
        'data/ir_cron_data.xml',
        'data/timesheet_warning_data.xml',
        'data/reminder_cp.xml',
        'views/hr_employee_view.xml',
        'views/timesheet_warning_view.xml',
        'views/hr_holidays_status_view.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
