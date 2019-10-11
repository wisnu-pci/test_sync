import datetime
import logging
# from datetime import date, datetime
from odoo import api, models, fields, _
from odoo.exceptions import Warning, UserError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """ inherit sale order """
    _inherit = "sale.order"

    # type = fields.Selection([('man_days', 'Man Days'),
    #                          ('package', 'Package'),
    #                          ('leasing', 'Leasing')], required=True)
    # date_from = fields.Date(string='Date From', default=_set_def_date_from)
    date_from = fields.Date(string='Date From')

    def _set_def_date_from(self):
        """ :param date_from get from 1st timesheet """
        prod_id = self.analytic_account_id.id
        tanggal = []
        if not prod_id:
            return tanggal
        elif prod_id:
            self._cr.execute('''select date from account_analytic_line
                                    where account_id = %s order by date ASC''', (prod_id,))
            data = self._cr.fetchone()
            if data:
                tanggal = data[0]
            else:
                _logger.warn(' !!! Warning Appear here : The date of timesheet is not found !!!')
                raise Warning(_('Warning!'
                                ' can not find first date for account %s' % self.analytic_account_id.name))
            return tanggal

    def get_dt_invoiceable(self, so, date_from, date_to, task_ids = False):
        if task_ids:
            self._cr.execute('''
                select
                    distinct(user_id),
                    sum(unit_amount)
                from
                    account_analytic_line
                where
                    account_id = %s
                    and invoiceable_analytic_line = 't'
                    and date >= %s
                    and date <= %s
                    and project_id is not null
                    and task_id in %s
                group by
                    user_id''', (so.analytic_account_id.id, date_from,
                                 date_to, tuple(task_ids.ids)))
            return self._cr.fetchall()
        else:
            self._cr.execute('''select
                                        distinct(user_id),
                                        sum(unit_amount)
                                    from
                                        account_analytic_line
                                    where
                                        account_id = %s
                                        and invoiceable_analytic_line = 't'
                                        and date >= %s
                                        and date <= %s
                                        and project_id is not null
                                    group by
                                        user_id
                                    ''', (so.analytic_account_id.id, date_from, date_to,))
            return self._cr.fetchall()

    def get_dt_employee(self, user_id):
        self._cr.execute('''
                  select
                      employee.id as employee_id,
                      partner.name as employee,
                      job.id as position_id,
                      job.name as position,
                      product_tmpl.list_price as list_price,
                      product.id as product_id,
                      product_tmpl.id as product_tmpl_id,
                      users.id as user_id,
                      product_tmpl.uom_id as uom_id,
                      partner.lang as lang,
                      partner.id as partner_id,
                      product_tmpl.name as product_name
                  from
                      hr_employee as employee
                            inner join
                            resource_resource as resource on (resource.id = employee.resource_id)
                                inner join
                            res_users as users on (resource.user_id = users.id)
                                inner join
                            res_partner as partner on (users.partner_id = partner.id)
                                inner join
                            hr_job as job on (employee.job_id = job.id)
                                inner join
                            product_product as product on (product.id = job.product_id)
                                inner join
                            product_template as product_tmpl on (product.product_tmpl_id = product_tmpl.id)
                  where
                      users.id = '%d';
                          ''' % (user_id,))
        return self._cr.dictfetchall()[0]

    def get_update_delivery_qty(self, so_line, employee_id, employee_name, product_id, product_name, uom_id, temp_time, vals, so , section, so_line_obj):
        if so_line and (so_line.product_uom_qty > 0):
            so_line.write({
                'product_uom_qty': 0,
            })
            #continue
        if so_line and so_line.product_id.id != product_id:
            so_line.write({
                'product_id': product_id,
                'qty_delivered': temp_time / 8,
                'name': product_name + ': ' + employee_name,
                'product_uom': uom_id,
                'price_unit': vals,
            })
            #continue
        if so_line and so_line.product_id.id == product_id:
            so_line.write({
                'qty_delivered': temp_time / 8,
            })
            #continue
        else:
            value = {
                    'order_id': so.id,
                    'employee_id': employee_id,
                    'product_id': product_id,
                    'qty_delivered': temp_time / 8,
                    'name': product_name + ': ' + employee_name,
                    'product_uom_qty': 0,  # 1 awalnya
                    'product_uom': uom_id,
                    'price_unit': vals,
                }
            if section:
                value['layout_category_id'] = section.id
            so_line = so_line_obj.create(value)
            so_line.product_id_change()
        return

    def get_employee(self, section, so, euser, vals, emp_obj):
        temp_time = euser[1]
        if not emp_obj.job_id.product_id:
            raise Warning(_('Warning!'
                            'Please Define Product of Job %s' % emp_obj.job_id.name))
        if temp_time > 0:
            so_line_obj = self.env['sale.order.line']
            domain_line = [('order_id', '=', so.id),
                ('employee_id', '=', emp_obj.id)]
            if section:
                domain_line.append(('layout_category_id', '=', section.id))
            so_line = so_line_obj.search(domain_line)

            if len(so_line) > 1:
                raise Warning(_('Warning'
                                'There are can not more than '
                                'one line for same Employee %s' % emp_obj.name))

            if so.pricelist_id and so.partner_id:
                product = emp_obj.job_id.product_id.with_context(
                    lang=so.partner_id.lang,
                    partner=so.partner_id.id,
                    quantity=1,
                    date=so.date_order,
                    pricelist=so.pricelist_id.id,
                    uom=emp_obj.job_id.product_id.uom_id.id
                )
                vals = self.env['account.tax']._fix_tax_included_price(
                    product.price, product.taxes_id, so_line_obj.tax_id)
            else:
                vals = emp_obj.job_id.product_id.list_price

            # update the price unit
            # because of conversion multi currency
            if so_line and (so_line.price_unit != vals) and (so_line.price_unit == 0):
                _logger.info('# update price unit only', )
                so_line.write({'price_unit': vals, })
            id_emp = emp_obj.id
            nm_emp = emp_obj.name
            id_prd = emp_obj.job_id.product_id.id
            nm_prd = emp_obj.job_id.product_id.name
            id_uom = emp_obj.job_id.product_id.uom_id.id
            update_delivey_qty = self.get_update_delivery_qty(so_line, id_emp, nm_emp,
                                id_prd, nm_prd, id_uom, temp_time,
                                vals, so ,section, so_line_obj)
        return

    def get_non_employee(self,section, so, euser, vals):
        employee_data = self.get_dt_employee(euser[0])
        temp_time = euser[1]
        if not employee_data['product_id']:
            raise UserError(
                _('Please Define Product of Job for %s' % employee_data['employee']))
        if temp_time > 0:
            so_line_obj = self.env['sale.order.line']
            domain_line = [('order_id', '=', so.id),
                ('employee_id', '=', employee_data['employee_id'])]
            if section:
                domain_line.append(('layout_category_id', '=', section.id))
            so_line = so_line_obj.search(domain_line)
            # for data_line in so_line:
            if so_line.product_id.id != employee_data['position_id']:
                _logger.info('# [n] ada yang beda di so line untuk productnya')

            if len(so_line) > 1:
                raise UserError(
                    _('There are can not more than one line for same Employee %s' %
                    employee_data['employee']))

            if so.pricelist_id and so.partner_id:
                product = self.env['product.product'].search(
                    [('id', '=', employee_data['product_id'])])
                vals = self.env['account.tax']._fix_tax_included_price(product.price,
                                                                    product.taxes_id,
                                                                    so_line_obj.tax_id)
            else:
                vals = employee_data['list_price']
            # flow update delivery qty >>>>>>>>>>>>>>>>>>>>
            id_emp = employee_data['employee_id']
            nm_emp = employee_data['employee']
            id_prd = employee_data['product_id']
            nm_prd = employee_data['product_name']
            id_uom = employee_data['uom_id']
            update_delivey_qty = self.get_update_delivery_qty(so_line, id_emp, nm_emp,
                                id_prd, nm_prd, id_uom, temp_time,
                                vals, so ,section, so_line_obj)
        return

    def get_non_section(self, date_from, date_to, so):
        task_order_obj = self.get_dt_invoiceable(so, date_from, date_to, task_ids=False)
        if not task_order_obj:
            _logger.info(' the record is empty ')
        user_id = [item[0] for item in task_order_obj]
        temp_time = 0
        vals = {}
        for euser in task_order_obj:
            # note : emp_obj hanya mencari employee yg berstatus masih aktif saja,
            emp_obj = self.env['hr.employee'].search([('user_id', '=', euser[0])])
            section = False
            if not emp_obj:
                not_emp = self.get_non_employee(section, so, euser, vals)
            emp = self.get_employee(section, so, euser, vals, emp_obj)
        return

    def get_section(self, date_from, date_to, so):
        for section in so.analytic_account_id.section_ids:
            okr = section.task_id
            project_task_obj = self.env['project.task']
            task_ids = project_task_obj.search([
                ('parent_task_id', 'child_of', okr.id),
                ('active', '=', True)
            ], order='id asc')
            task_order_obj = self.get_dt_invoiceable(so, date_from, date_to, task_ids)
            if not task_order_obj:
                _logger.info(' the record is empty ')
            user_id = [item[0] for item in task_order_obj]
            temp_time = 0
            vals = {}
            for euser in task_order_obj:
                emp_obj = self.env['hr.employee'].search([('user_id', '=', euser[0])])
                if not emp_obj:
                    not_emp = self.get_non_employee(section, so, euser, vals)
                emp = self.get_employee(self, emp_obj,so, vals, section)
            _logger.info(' # SO correction ')
            cek_update = self.get_cek_update(so)
        return

    def get_cek_update (self, so):
        total_all = 0
        total_employe_price = 0
        total_orderline = 0  # not include employee
        has_a_corection_orderline = False
        wrong_phase = False
        so_line = self.env['sale.order.line'].search([('order_id', '=', so.id),
                                                    ('employee_id', '=', False)])
        product_correction = self.env['product.product'].search(
            [("name", "ilike", "SO correction / adjustment")])
        for each in so.order_line:
            if not each.employee_id:
                # check dulu di SO line itu ada product yg Engineer apa engga
                # kalo ada berarti ubah status 'wrong_phase' ke True
                if each.product_id.default_code:
                    wrong_phase = True
                    # else:
                    #     wrong_phase = False
                    #     print 'ini mungkin bukan engineer dan benar'

            if each.employee_id:
                total_employe_price += each.price_subtotal
            else:
                total_orderline += each.price_subtotal

            if wrong_phase:
                if each.product_id.id == product_correction.id:
                    has_a_corection_orderline = True
                    # else:
                    #     has_a_corection_orderline = False
                    #     wrong_phase = False
                    #     print '## SO Correction tidak ditemukan'

            total_all += each.price_subtotal
        so_correct = self.env['sale.order.line'].search(
            [('order_id', '=', so.id), ('product_id', '=', product_correction.id)])
        if so_correct:
            so_correct.write({'product_uom_qty': 0, })
        elif wrong_phase and has_a_corection_orderline:
            so_correct.write({'price_unit': (-1 * total_employe_price)})
        elif wrong_phase and not has_a_corection_orderline:
            so_line.create({
                'order_id': so.id,
                'product_id': product_correction.id,
                'name': product_correction.name,
                'product_uom_qty': 0,
                'product_uom': product_correction.uom_id.id,
                'price_unit': (-1 * total_employe_price),
            })
        else:
            _logger.info('====================== OEF CEK UPDATE ++++++++++++++++++++++++')
        return

    @api.multi
    def qty_update(self, so, date_to):
        """ :param so the sale order active
        :param date_to the limit date check timesheet """
        _logger.info('# SO Deliverd Qty Update check START')

        project_task_obj = self.env['project.task']
        date_from = self.date_from
        if not date_from:
            date_from = self._set_def_date_from()

        # 50 ~ 316 dikomen, 317 ~ 572 masukin inden
        if so.analytic_account_id.section_ids:
            self.get_section(date_from, date_to,so)
        else:
            self.get_non_section(date_from, date_to, so)

    @api.model
    def action_update_delivery_qty_scheduler(self):
        """function called from scheduler action"""
        _logger.info(' #### START PROCESS ####')
        sale = self.env['sale.order'].search([('state', '=', 'sale'), ('analytic_account_id', '!=', False)])

        te_to = datetime.date.today()
        idx = (te_to.weekday() + 1) % 7
        date_to = te_to - datetime.timedelta(idx)

        for so in sale:
            _logger.info('# SO Number\t: %s', so.name)
            try:
                so.qty_update(so, date_to)
            except Warning:
                _logger.warn(' !!! Warning Appear here : Some warning is appear !!!')
                continue
            except TypeError:
                _logger.warn(' !!! TypeError Appear here : Some warning is appear !!!')
                continue
            else:
                if so.analytic_account_id.auto_invoice:
                    try:
                        so.action_invoice_create(final=True)
                    except UserError:
                        _logger.warn(' !!! Log for User Error : No Invoicable Line !!!')
                        continue
                    else:
                        for ice in so.invoice_ids:
                            if not ice.date_invoice:
                                ice.write({'date_invoice': date_to})
            _logger.info('# OEF Process for SO Number\t: %s', so.name)
        _logger.info(' #### EOF PROCESS ####')

    #     @api.multi
    #     def action_invoice_create(self, grouped=False, final=False):
    #         res = super(SaleOrder, self).action_invoice_create(grouped, final)
    #         for order in self:
    #             order.message_post(body=_("New Invoice created"))
    #         return res

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        for order in self:
            group_key = order.id if grouped \
                else (order.partner_invoice_id.id, order.currency_id.id)
            for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                elif group_key in invoices:
                    vals = {}
                    if order.name not in invoices[group_key].origin.split(', '):
                        vals['origin'] = invoices[group_key].origin + ', ' + order.name
                    if order.client_order_ref and order.client_order_ref \
                            not in invoices[group_key].name.split(', '):
                        vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
                    invoices[group_key].write(vals)
                if line.qty_to_invoice > 0:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                elif line.qty_to_invoice < 0 and final:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoice] = references[invoice] | order
        if not invoices:
            raise UserError(_('There is no invoicable line.'))

        for invoice in invoices.values():
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoicable line.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_untaxed < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            order.message_post(body=_("New Invoice created"))
            invoice.message_post_with_view('mail.message_origin_link',
                                           values={'self': invoice, 'origin': references[invoice]},
                                           subtype_id=self.env.ref('mail.mt_note').id)
        return [inv.id for inv in invoices.values()]

    # @api.multi
    # def action_inter_invoice_create(self, grouped=False, final=False):
    #     """
    #     Create the invoice associated to the SO.
    #     :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
    #                     (partner_invoice_id, currency)
    #     :param final: if True, refunds will be generated if necessary
    #     :returns: list of created invoices
    #     """
    #     inv_obj = self.env['account.invoice']
    #     precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #     invoices = {}
    #     references = {}
    #     for order in self:
    #         group_key = order.id if grouped \
    #             else (order.partner_invoice_id.id, order.currency_id.id)
    #         for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
    #             if float_is_zero(line.qty_to_invoice, precision_digits=precision):
    #                 continue
    #             if group_key not in invoices:
    #                 inv_data = order._prepare_invoice()
    #                 invoice = inv_obj.sudo().create(inv_data)
    #                 references[invoice] = order
    #                 invoices[group_key] = invoice
    #             elif group_key in invoices:
    #                 vals = {}
    #                 if order.name not in invoices[group_key].origin.split(', '):
    #                     vals['origin'] = invoices[group_key].origin + ', ' + order.name
    #                 if order.client_order_ref and order.client_order_ref \
    #                         not in invoices[group_key].name.split(', '):
    #                     vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
    #                 invoices[group_key].write(vals)
    #             if line.qty_to_invoice > 0:
    #                 line.sudo().invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
    #             elif line.qty_to_invoice < 0 and final:
    #                 line.sudo().invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

    #         if references.get(invoices.get(group_key)):
    #             if order not in references[invoices[group_key]]:
    #                 references[invoice] = references[invoice] | order
    #     if not invoices:
    #         raise UserError(_('There is no invoicable line.'))

    #     for invoice in invoices.values():
    #         if not invoice.invoice_line_ids:
    #             raise UserError(_('There is no invoicable line.'))
    #         # If invoice is negative, do a refund invoice instead
    #         if invoice.amount_untaxed < 0:
    #             invoice.type = 'out_refund'
    #             for line in invoice.invoice_line_ids:
    #                 line.quantity = -line.quantity
    #         # Use additional field helper function (for account extensions)
    #         for line in invoice.invoice_line_ids:
    #             line.sudo()._set_additional_fields(invoice)
    #         # Necessary to force computation of taxes. In account_invoice, they are triggered
    #         # by onchanges, which are not triggered when doing a create.
    #         invoice.sudo().compute_taxes()
    #         order.sudo().message_post(body=_("New Invoice created"))
    #         invoice.sudo().message_post_with_view('mail.message_origin_link',
    #                                        values={'self': invoice, 'origin': references[invoice]},
    #                                        subtype_id=self.env.ref('mail.mt_note').id)
    #     return [inv.id for inv in invoices.values()]


class SaleOrderLine(models.Model):
    """ inherit sale order line
     to add employee_id in the line,
     """
    _inherit = "sale.order.line"

    employee_id = fields.Many2one('hr.employee', string='Employee')

    # log message when order line is added
    @api.model
    def create(self, values):
        line = super(SaleOrderLine, self).create(values)
        co_src = self.env['sale.order'].search([('id', '=', values['order_id'])])
        prod_src = self.env['product.product'].search([('id', '=', values['product_id'])])
        co_src.message_post(body=_("Line added, product %s (%s), qty %s, price %s") % (
            prod_src.default_code, values['name'], values['product_uom_qty'],
            values.get('price_unit', 0)))
        return line

    @api.onchange('employee_id')
    def employee_id_change(self):
        if not self.employee_id:
            return {'domain': {'product_id': []}}

        if not self.employee_id.job_id.product_id:
            raise Warning(_('Warning!, Employee %s does not have a Product,\n '
                            'Please define it first' % self.employee_id.name))
        vals = {}
        domain = {'product_id': []}
        if self.employee_id:
            vals['product_id'] = self.employee_id.job_id.product_id.id
        self.update(vals)
        return {'domain': domain}

    @api.onchange('employee_id', 'product_id')
    def product_id_change(self):
        """ name employee and job in the desc """
        original_price = self.price_unit
        res = super(SaleOrderLine, self).product_id_change()
        vals = {}
        if self.employee_id:
            vals['name'] = self.employee_id.job_id.product_id.name + ": " + self.employee_id.name
            vals['price_unit'] = original_price
        self.update(vals)
        return res


class AnalyticAccount(models.Model):
    """ inherit to acount analytic line
     add bollean field named auto invoice
     as parameter to update auto or not"""
    _inherit = "account.analytic.account"

    auto_invoice = fields.Boolean('Auto Invoice', default=True)


class ResCurrency(models.Model):
    """inherit res currency"""
    _inherit = "res.currency"

    # fix issue multi company in sale order, invoice
    # add condition if to currency not USD, then convert from currency into USD first
    # @api.model
    # def _get_conversion_rate(self, from_currency, to_currency):
    #     """inherit get conversion rate for
    #     multi currency"""
    #     usd_curr = self.env['res.currency'].search([('name', '=', 'USD')])
    #     eur_curr = self.env['res.currency'].search([('name', '=', 'EUR')])
    #     if to_currency.id != usd_curr.id:
    #         temp = from_currency
    #         from_currency = usd_curr.with_env(self.env)
    #         if to_currency.id == eur_curr.id:
    #             from_currency = temp
    #     res = super(ResCurrency, self)._get_conversion_rate(from_currency, to_currency)
    #     return res

    @api.multi
    def compute(self, from_amount, to_currency, round=True):
        """ Convert `from_amount` from currency `self` to `to_currency`. """
        self, to_currency = self or to_currency, to_currency or self
        assert self, "compute from unknown currency"
        assert to_currency, "compute to unknown currency"
        # apply conversion rate
        myr_curr = self.env['res.currency'].search([('name', '=', 'MYR')])
        if self == to_currency:
            to_amount = from_amount
        elif (to_currency.id == myr_curr.id) and self.name == 'IDR':
            to_amount = from_amount
        else:
            to_amount = from_amount * self._get_conversion_rate(self, to_currency)
        # apply rounding
        return to_currency.round(to_amount) if round else to_amount
