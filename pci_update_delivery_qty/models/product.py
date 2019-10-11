from odoo import models, fields, api


class ProductTemplate(models.Model):
    """inherit product template"""
    _inherit = "product.template"
    #
    # job_position_line = fields.One2many('job.position.line', 'product_tmpl_id',
    #                                     string='Job Position Line')
    #


class JobPositionLine(models.Model):
    """ create class job position line
    to add a job line in the hr job in the product
    template
    """
    _name = 'job.position.line'

    job_id = fields.Many2one('hr.job', string='Job Title')
    product_tmpl_id = fields.Many2one('product.template', string='Products')

    @api.onchange('employee_id')
    def _onchange_job_id(self):
        """ onchange job id by employee id  """
        self.job_id = self.employee_id.job_id
