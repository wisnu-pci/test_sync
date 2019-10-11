# -*- coding: utf-8 -*-
"""timesheet warning"""
from odoo import models, fields


class HrHolidaysStatus(models.Model):
    """HrHolidaysStatus"""
    _inherit = "hr.holidays.status"

    check_timesheet_warning = fields.Boolean('Check Timesheet Warnings', \
                                             help='If this field is checked, it means that the user\
											  	   who input leave of this type will be still \
											  	   checked for their timesheet. If the user forget \
											  	   to submit timesheet, he/she should be got \
											  	   warning')
