# -*- coding: utf-8 -*-
from odoo import models, fields, api

class BrightloopSubscriptionLine(models.Model):
    _name = "brightloop.subscription.line"
    _description = "Brightloop Subscription Line"

    subscription_id = fields.Many2one("brightloop.subscription", string="Subscription", required=True, ondelete="CASCADE")
    product_id = fields.Many2one("product.product", string="Product / Addon", required=True)
    name = fields.Char(string="Description", required=True)
    quantity = fields.Float(string="Quantity", default=1.0, required=True)
    price_unit = fields.Float(string="Unit Price", required=True, default=0.0)
    tax_ids = fields.Many2many("account.tax", string="Taxes")

    price_subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)
    price_tax = fields.Float(string="Tax Amount", compute="_compute_subtotal", store=True)
    price_total = fields.Float(string="Total", compute="_compute_subtotal", store=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.price_unit = self.product_id.lst_price
            if self.product_id.taxes_id:
                self.tax_ids = self.product_id.taxes_id

    @api.depends('quantity', 'price_unit', 'tax_ids')
    def _compute_subtotal(self):
        for line in self:
            subtotal = line.quantity * line.price_unit
            tax_amount = 0.0
            if line.tax_ids:
                taxes = line.tax_ids.compute_all(line.price_unit, quantity=line.quantity, product=line.product_id)
                tax_amount = taxes['total_included'] - taxes['total_excluded']
                subtotal = taxes['total_excluded']

            line.price_subtotal = subtotal
            line.price_tax = tax_amount
            line.price_total = subtotal + tax_amount
