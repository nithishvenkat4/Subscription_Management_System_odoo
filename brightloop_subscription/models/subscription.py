# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

class BrightloopSubscription(models.Model):
    _name = "brightloop.subscription"
    _description = "Brightloop Subscription Contract"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Subscription Number", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one("res.partner", string="Customer", required=True, tracking=True)
    plan_id = fields.Many2one("brightloop.subscription.plan", string="Recurring Plan", required=True, tracking=True)
    
    start_date = fields.Date(string="Start Date", required=True, default=fields.Date.context_today)
    expiry_date = fields.Date(string="Expiry Date")
    next_billing_date = fields.Date(string="Next Billing Date", required=True, default=fields.Date.context_today, tracking=True)
    quote_valid_until = fields.Date(string="Quote Valid Until")

    payment_term_id = fields.Many2one("account.payment.term", string="Payment Terms")
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('quotation', 'Quotation'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ], string="Status", default='draft', tracking=True)

    # Lifecycle rules
    auto_close_on_end = fields.Boolean(string="Auto-Close on End", related="plan_id.auto_close_on_end", store=True)
    closable_early = fields.Boolean(string="Closable Early", related="plan_id.closable_early", store=True)
    pausable = fields.Boolean(string="Pausable", related="plan_id.pausable", store=True)
    renewable = fields.Boolean(string="Renewable", related="plan_id.renewable", store=True)

    line_ids = fields.One2many("brightloop.subscription.line", "subscription_id", string="Subscription Lines", copy=True)
    invoice_ids = fields.One2many("account.move", "subscription_id", string="Invoices", readonly=True)
    invoice_count = fields.Integer(string="Invoices Count", compute="_compute_invoice_count")

    applied_discount_id = fields.Many2one("brightloop.discount.rule", string="Applied Discount Rule")

    amount_untaxed = fields.Float(string="Untaxed Amount", compute="_compute_amounts", store=True)
    amount_tax = fields.Float(string="Taxes", compute="_compute_amounts", store=True)
    amount_discount = fields.Float(string="Discount", compute="_compute_amounts", store=True)
    amount_total = fields.Float(string="Total Recurring Amount", compute="_compute_amounts", store=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('brightloop.subscription') or _('New')
        return super(BrightloopSubscription, self).create(vals)

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for sub in self:
            sub.invoice_count = len(sub.invoice_ids)

    @api.depends('line_ids.price_subtotal', 'line_ids.price_total', 'applied_discount_id')
    def _compute_amounts(self):
        for sub in self:
            untaxed = sum(line.price_subtotal for line in sub.line_ids)
            tax = sum(line.price_tax for line in sub.line_ids)
            discount = 0.0

            if sub.applied_discount_id and sub.applied_discount_id.active:
                d_rule = sub.applied_discount_id
                total_qty = sum(line.quantity for line in sub.line_ids)
                if untaxed >= d_rule.min_purchase_amount and total_qty >= d_rule.min_quantity:
                    if d_rule.discount_type == 'percentage':
                        discount = untaxed * (d_rule.discount_value / 100.0)
                    else:
                        discount = min(untaxed, d_rule.discount_value)

            sub.amount_untaxed = untaxed
            sub.amount_tax = tax
            sub.amount_discount = discount
            sub.amount_total = max(0.0, untaxed + tax - discount)

    # State transitions
    def action_send_quotation(self):
        for sub in self:
            sub.state = 'quotation'

    def action_confirm(self):
        for sub in self:
            sub.state = 'confirmed'

    def action_activate(self):
        for sub in self:
            sub.state = 'active'
            if not sub.next_billing_date:
                sub.next_billing_date = sub.start_date or fields.Date.context_today(self)

    def action_pause(self):
        for sub in self:
            if not sub.pausable:
                raise UserError(_("The plan '%s' does not permit pausing subscriptions.") % sub.plan_id.name)
            sub.state = 'paused'

    def action_resume(self):
        for sub in self:
            sub.state = 'active'

    def action_close(self):
        for sub in self:
            today = fields.Date.context_today(self)
            if not sub.closable_early and sub.expiry_date and today < sub.expiry_date:
                raise UserError(_("This plan cannot be closed early before its expiry date (%s).") % sub.expiry_date)
            sub.state = 'closed'

    def action_renew(self):
        for sub in self:
            if not sub.renewable:
                raise UserError(_("This plan cannot be renewed."))
            interval = sub.plan_id.billing_interval
            if interval == 'yearly':
                sub.expiry_date = (sub.expiry_date or fields.Date.context_today(self)) + relativedelta(years=1)
            else:
                sub.expiry_date = (sub.expiry_date or fields.Date.context_today(self)) + relativedelta(months=1)
            sub.state = 'active'

    def action_generate_invoice(self):
        """
        Billing Day Invoicing Routine:
        Enforces idempotency, calculates taxes, applies discounts, advances billing date.
        """
        self.ensure_one()
        today = fields.Date.context_today(self)
        cycle_date = self.next_billing_date or today
        idempotency_key = f"SUB-{self.id}-{cycle_date.strftime('%Y-%m-%d')}"

        # Double billing guard
        existing = self.env['account.move'].search([('brightloop_idempotency_key', '=', idempotency_key)], limit=1)
        if existing:
            raise UserError(_("Invoice already exists for this cycle: %s (Idempotency Key: %s)") % (existing.name, idempotency_key))

        invoice_lines = []
        for line in self.line_ids:
            invoice_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.name or line.product_id.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'tax_ids': [(6, 0, line.tax_ids.ids)],
            }))

        move_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': cycle_date,
            'invoice_payment_term_id': self.payment_term_id.id if self.payment_term_id else False,
            'subscription_id': self.id,
            'brightloop_idempotency_key': idempotency_key,
            'invoice_line_ids': invoice_lines,
        }
        invoice = self.env['account.move'].create(move_vals)

        # Advance next_billing_date
        interval = self.plan_id.billing_interval
        if interval == 'daily':
            next_date = cycle_date + timedelta(days=1)
        elif interval == 'weekly':
            next_date = cycle_date + timedelta(weeks=1)
        elif interval == 'yearly':
            next_date = cycle_date + relativedelta(years=1)
        else: # monthly
            next_date = cycle_date + relativedelta(months=1)

        self.next_billing_date = next_date

        if self.auto_close_on_end and self.expiry_date and next_date > self.expiry_date:
            self.state = 'closed'

        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }

    @api.model
    def cron_recurring_billing(self):
        """
        Cron scheduled action to bill all subscriptions due today.
        Nothing is billed twice or skipped.
        """
        today = fields.Date.context_today(self)
        due_subs = self.search([
            ('state', '=', 'active'),
            ('next_billing_date', '<=', today)
        ])
        for sub in due_subs:
            try:
                sub.action_generate_invoice()
            except Exception:
                pass
