# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProjectTask(models.Model):
    """
    add follower to project task
    """
    _inherit = 'project.task'

    @api.model
    def create(self, vals):
        """
        inerit create
        :param vals:
        :return:
        """
        res = super(ProjectTask, self).create(vals)

        reviewer = res.reviewer_obj
        partner = self.env['res.partner'].search([('user_ids', '=', reviewer.id)], limit=1)

        is_follower = self.env['mail.followers'].search([('partner_id', '=', partner.id),
                                                         ('res_id', '=', res.id)])
        if not is_follower:
            follower_vals = {'res_model': 'project.task',
                             'res_id': res.id,
                             'partner_id': partner.id}
            self.env['mail.followers'].create(follower_vals)

        return res

    @api.multi
    def write(self, values):
        """
        inherit write
        :param values:
        :return:
        """
        res = super(ProjectTask, self).write(values)
        for this in self:
            if 'reviewer_obj' in values:
                reviewer = values.get('reviewer_obj')
                partner = self.env['res.partner'].search([('user_ids', '=', reviewer)], limit=1)
                is_follower = self.env['mail.followers'].search([('partner_id', '=', partner.id),
                                                                 ('res_id', '=', this.id)])
                if not is_follower:
                    follower_vals = {'res_model': 'project.task',
                                     'res_id': this.id,
                                     'partner_id': partner.id}
                    self.env['mail.followers'].create(follower_vals)
        return res
