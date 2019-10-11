from odoo import models, fields


class HrEmployee(models.Model):
    """inherit HR Employee"""
    _inherit = "hr.job"

    product_id = fields.Many2one('product.product', string='Product')
