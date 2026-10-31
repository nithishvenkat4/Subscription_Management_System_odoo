# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountMove(models.Model):
    _inherit = "account.move"

    subscription_id = fields.Many2one("brightloop.subscription", string="Originating Subscription", ondelete="SET NULL")
    brightloop_idempotency_key = fields.Char(string="Billing Idempotency Key", index=True, copy=False, help="Guarantees no duplicate billing for the same subscription cycle.")
