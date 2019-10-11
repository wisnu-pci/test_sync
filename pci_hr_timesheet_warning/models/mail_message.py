# -*- coding: utf-8 -*-
"""mail messageg"""
from odoo import models, api


class MalilMessage(models.Model):
    """MalilMessage"""
    _import = 'mail.message'

    @api.model
    def _get_record_name(self, values):
        """ Return the related document name, using name_get. It is done using
            SUPERUSER_ID, to be sure to have the record name correctly stored. """
        model = values.get('model', self.env.context.get('default_model'))
        res_id = values.get('res_id', self.env.context.get('default_res_id'))
        if not model or not res_id or model not in self.env:
            return False
        id_model = self.env[model].sudo().browse(res_id)
        if model == 'timesheet.warning':
            return id_model.name
        return self.env[model].sudo().browse(res_id).name_get()[0][1]
