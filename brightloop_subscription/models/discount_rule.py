# -*- coding: utf-8 -*-
from odoo import models, fields, api

class BrightloopDiscountRule(models.Model):
    _name = "brightloop.discount.rule"
    _description = "Brightloop Discount Rule"
    _order = "name asc"

    name = fields.Char(string="Discount Name", required=True)
    discount_type = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('fixed_amount', 'Fixed Amount ($)'),
    ], string="Type", default="percentage", required=True)

    discount_value = fields.Float(string="Discount Value", required=True, default=0.0)
    min_purchase_amount = fields.Float(string="Minimum Purchase Amount", default=0.0)
    min_quantity = fields.Integer(string="Minimum Quantity / Seats", default=0)

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    max_uses = fields.Integer(string="Maximum Uses Limit", help="Ceiling on global applications. Leave 0 for unlimited.")
    used_count = fields.Integer(string="Times Used", default=0, readonly=True)

    scope = fields.Selection([
        ('whole_subscription', 'Whole Subscription'),
        ('specific_products', 'Specific Products'),
    ], string="Application Scope", default="whole_subscription", required=True)

    product_id = fields.Many2one("product.product", string="Target Product", help="Applicable product if scope is specific products.")
    active = fields.Boolean(string="Active", default=True)
