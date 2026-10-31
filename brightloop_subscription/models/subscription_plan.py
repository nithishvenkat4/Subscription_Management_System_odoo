# -*- coding: utf-8 -*-
from odoo import models, fields, api

class BrightloopSubscriptionPlan(models.Model):
    _name = "brightloop.subscription.plan"
    _description = "Brightloop Subscription Plan"
    _order = "name asc"

    name = fields.Char(string="Plan Name", required=True)
    description = fields.Text(string="Description")
    recurring_price = fields.Float(string="Recurring Price", required=True, default=0.0)
    
    billing_interval = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], string="Billing Frequency", required=True, default='monthly')

    min_quantity = fields.Integer(string="Minimum Quantity", default=1, required=True)
    available_from = fields.Date(string="Available From")
    available_to = fields.Date(string="Available To")

    # Plan Lifecycle Flags configured by Admin
    auto_close_on_end = fields.Boolean(
        string="Auto-Close When Ended",
        default=False,
        help="If checked, subscriptions under this plan close automatically upon reaching the end date."
    )
    closable_early = fields.Boolean(
        string="Can Be Closed Early",
        default=True,
        help="If checked, customer or staff can terminate the subscription before expiration."
    )
    pausable = fields.Boolean(
        string="Can Be Paused",
        default=True,
        help="If checked, billing can be temporarily suspended."
    )
    renewable = fields.Boolean(
        string="Can Be Renewed",
        default=True,
        help="If checked, subscription can be renewed for subsequent terms."
    )

    active = fields.Boolean(string="Active", default=True)
    subscription_count = fields.Integer(string="Subscriptions", compute="_compute_subscription_count")

    def _compute_subscription_count(self):
        for plan in self:
            plan.subscription_count = self.env['brightloop.subscription'].search_count([('plan_id', '=', plan.id)])
