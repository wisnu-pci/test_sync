"""
Report Timehseet Wizard
"""
from datetime import datetime
from io import BytesIO
import base64
import xlsxwriter
import datetime
from odoo import api, fields, models, _


class ReportTimehseetWizard(models.TransientModel):
    """
    Report Timehseet Wizard
    """
    _name = 'report.timesheet.wizard'

    def _set_default_start_date(self):
        """ get default start date """
        hari = datetime.date.today()
        idx = (hari.weekday() + 1) % 7
        sun = hari - datetime.timedelta(idx)
        sun = sun - datetime.timedelta(6)
        return sun

    def _set_default_end_date(self):
        """ get default end date """
        hari = datetime.date.today()
        idx = (hari.weekday() + 1) % 7
        sun = hari - datetime.timedelta(idx)
        return sun

    start_date = fields.Date(string='Start Date', default=_set_default_start_date)
    end_date = fields.Date(string='End Date', default=_set_default_end_date)

    state_x = fields.Selection([('choose', 'Choose'),
                                ('get', 'Get')], default='choose')
    data_x = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)

    @api.multi
    def report_timesheet_button(self):
        """
        report timesheet button and template
        """
        start_date = self.start_date or False
        end_date = self.end_date or False
        context = dict(self._context)
        data = self.read([])[0]
        context.update({'start_date': data['start_date'],
                        'end_date': data['end_date']})
        sale_order_obj = self.env['sale.order']. \
            search([('id', '=', context['active_id'])], limit=1)
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        filename = 'report_timesheet_' + sale_order_obj.name + '.xlsx'

        # STYLE
        #################################################################################
        header_top = workbook.add_format({'bold': 0, 'align': 'center', })
        header_top.set_bg_color('#2b8aff')
        header_top.set_font_name('Calibri')
        header_top.set_font_size('11')
        header_top.set_font_color('white')

        #### value normal font
        normal_font = workbook.add_format({'bold': 0, 'align': 'left', 'valign': 'vcenter'})
        normal_font.set_font_name('Calibri')
        normal_font.set_font_size('11')

        #### value normal font right
        normal_font_right = workbook.add_format({'bold': 0, 'align': 'right', 'valign': 'vcenter'})
        normal_font_right.set_font_name('Calibri')
        normal_font_right.set_font_size('11')

        # WORKSHEET
        #################################################################################
        worksheet = workbook.add_worksheet("Report Timesheet")
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 17)
        worksheet.set_column('C:C', 37)
        worksheet.set_column('D:D', 23)
        worksheet.set_column('E:E', 13)
        worksheet.set_column('F:F', 51)
        worksheet.set_column('G:G', 8)

        worksheet.write('A1', 'Date', header_top)
        worksheet.write('B1', 'Customer', header_top)
        worksheet.write('C1', 'Project', header_top)
        worksheet.write('D1', 'Employee', header_top)
        worksheet.write('E1', 'Task', header_top)
        worksheet.write('F1', 'Description', header_top)
        worksheet.write('G1', 'ManHours', header_top)

        account_analytic_line_obj = self.env['account.analytic.line']. \
            search([('date', '>=', context['start_date']),
                    ('date', '<=', context['end_date']),
                    ('invoiceable_analytic_line', '=', True),
                    ('project_id.name', '=', sale_order_obj. \
                     analytic_account_id.name)], order='date asc')

        row = 1
        col = 1
        for line in account_analytic_line_obj:
            worksheet.write(row, 0, line.date, normal_font)
            worksheet.write(row, 1, line.project_id.partner_id.name, normal_font)
            worksheet.write(row, 2, line.project_id.name, normal_font)
            worksheet.write(row, 3, line.user_id.name, normal_font)
            worksheet.write(row, 4, line.task_id.name, normal_font)
            worksheet.write(row, 5, line.name, normal_font)
            worksheet.write(row, 6, line.unit_amount, normal_font_right)
            row += 1

        workbook.close()
        out = base64.encodestring(fp.getvalue())
        self.write({'state_x': 'get', 'data_x': out, 'name': filename})
        ir_model_data = self.env['ir.model.data']
        fp.close()
        form_res = ir_model_data.get_object_reference('pci_update_delivery_qty',
                                                      'report_timesheet_view_wizard')
        form_id = form_res and form_res[1] or False
        # remove file image
        return {
            'name': _('Timesheet Report'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'report.timesheet.wizard',
            'res_id': self.ids[0],
            'view_id': False,
            #             'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
