# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_subscription_product = fields.Boolean(
        string="Is Subscription Offering",
        default=False,
        help="Check this if this product can be billed as a subscription or add-on."
    )
    cost_price = fields.Float(string="Internal Cost Price", default=0.0)
    brand_variant_surcharge = fields.Float(
        string="Brand Variant Extra Price",
        default=0.0,
        help="Extra surcharge added when specific brand variants (e.g. Odoo brand +560) are selected."
    )
