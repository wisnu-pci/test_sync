# -*- coding: utf-8 -*-
import datetime
import logging
# from datetime import datetime, date
from odoo import models, fields, api, _
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)


class UpdateDeliveryQtySale(models.TransientModel):
    _name = "update.delivery.qty.sale"

    def _set_default_days(self):
        """ get default days """
        hari = datetime.date.today()
        idx = (hari.weekday() + 1) % 7
        sun = hari - datetime.timedelta(idx)
        return sun

    date_to = fields.Date(string='Date to', required=True, default=_set_default_days)

    @api.multi
    def action_update_delivery_qty_sale(self):
        """ update the delivered qty and create invoice draft"""
        active_id = self._context.get('active_id', False)
        sale = self.env['sale.order'].browse(active_id)
        if not sale.analytic_account_id:
            raise Warning(_('Please Define the Analytic Account'))

        date_to = self.date_to
        for so in sale:
            so.qty_update(so, date_to)
            so.action_invoice_create(final=True)
            for ice in so.invoice_ids:
                if not ice.date_invoice:
                    ice.write({'date_invoice': date_to})

        # purchase = sale.inter_purchase_id
        # if purchase and purchase.state=='purchase':
        #     inter_sale = purchase.inter_sale_id
        #     if not purchase.analytic_account_id:
        #         raise Warning(_('Please Define the Analytic Account'))

        #     for po in purchase:
        #         _logger.info('================= UPDATE DELIVERY QTY FOR PO =================')
        #         po.qty_update(po, date_to)
        #         po.action_invoice_create(final=True)
        #         for ice in po.invoice_ids:
        #             if not ice.date_invoice:
        #                 ice.write({'date_invoice': date_to})

        #         _logger.info('================= UPDATE DELIVERY QTY FOR SO INTERCOMPANY =================')
        #         inter_sale.qty_update_inter(inter_sale, date_to)
        #         inter_sale.action_inter_invoice_create(final=True)
        #         for ice in inter_sale.invoice_ids:
        #             if not ice.date_invoice:
        #                 ice.sudo().write({'date_invoice': date_to})
