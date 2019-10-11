# -*- coding: utf-8 -*-
"""hr employee"""
from odoo import models, fields


class HrEmployee(models.Model):
    """hr employee"""
    _inherit = "hr.employee"

    timesheet_exception = fields.Boolean('Timesheet Warnings Exception',
                                         help='If this field is checked it means that the user \
										 	   will not receive timesheet warning automatically, \
										 	   to send him warnings it should be only manual')
