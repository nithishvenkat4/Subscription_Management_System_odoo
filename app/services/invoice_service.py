from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.invoice import Invoice
from app.models.user import User
from app.core.config import settings

class InvoiceService:

    @staticmethod
    def confirm_invoice(db: Session, invoice_id: int, user: User) -> Invoice:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        # Customer cannot confirm invoices, only admin/staff
        if user.role == "customer":
            raise HTTPException(status_code=403, detail="Customers cannot confirm invoices.")

        if invoice.status != "draft":
            raise HTTPException(status_code=400, detail=f"Cannot confirm invoice in '{invoice.status}' state.")

        invoice.status = "confirmed"
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def cancel_invoice(db: Session, invoice_id: int, user: User) -> Invoice:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        if user.role == "customer":
            raise HTTPException(status_code=403, detail="Customers cannot cancel invoices.")

        if invoice.status == "paid":
            raise HTTPException(status_code=400, detail="Cannot cancel an invoice that has already been paid.")

        invoice.status = "cancelled"
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def send_invoice(db: Session, invoice_id: int, user: User) -> Dict[str, Any]:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        if user.role == "customer":
            raise HTTPException(status_code=403, detail="Permission denied.")

        invoice.sent_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(invoice)

        return {
            "success": True,
            "message": f"Invoice {invoice.invoice_number} successfully dispatched to {invoice.customer.email}.",
            "recipient": invoice.customer.email,
            "invoice_number": invoice.invoice_number,
            "sent_at": invoice.sent_at.isoformat()
        }

    @staticmethod
    def generate_html_invoice(invoice: Invoice) -> str:
        """
        Generates an enterprise-grade, printable HTML invoice template.
        """
        company_name = settings.COMPANY_NAME
        company_addr = settings.COMPANY_ADDRESS
        company_email = settings.COMPANY_EMAIL

        lines_html = ""
        for line in invoice.lines:
            lines_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #1e293b;">
                    <strong>{line.description}</strong>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-size: 14px; text-align: center; color: #475569;">
                    {line.quantity}
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-size: 14px; text-align: right; color: #475569;">
                    ${line.unit_price:,.2f}
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-size: 14px; text-align: right; color: #475569;">
                    {line.tax_rate}% (${line.tax_amount:,.2f})
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; font-size: 14px; text-align: right; font-weight: 600; color: #1e293b;">
                    ${line.total_amount:,.2f}
                </td>
            </tr>
            """

        status_color = {
            "draft": "#64748b",
            "confirmed": "#2563eb",
            "paid": "#16a34a",
            "cancelled": "#dc2626"
        }.get(invoice.status, "#64748b")

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Invoice {invoice.invoice_number}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 40px; color: #0f172a; background: #fff; }}
        .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #714b67; padding-bottom: 20px; margin-bottom: 30px; }}
        .brand {{ font-size: 26px; font-weight: 800; color: #714b67; letter-spacing: -0.5px; }}
        .badge {{ display: inline-block; padding: 6px 14px; border-radius: 9999px; color: #fff; font-weight: 700; font-size: 12px; text-transform: uppercase; background-color: {status_color}; }}
        .details-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 40px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
        th {{ background: #f8fafc; padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; border-bottom: 2px solid #cbd5e1; }}
        .totals-table {{ width: 320px; margin-left: auto; }}
        .totals-table td {{ padding: 8px 12px; }}
        @media print {{ body {{ padding: 0; }} .no-print {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 20px; text-align: right;">
        <button onclick="window.print()" style="background: #714b67; color: #fff; border: none; padding: 10px 20px; border-radius: 6px; font-weight: 600; cursor: pointer;">
            🖨️ Print / Save PDF
        </button>
    </div>

    <div class="header">
        <div>
            <div class="brand">BRIGHTLOOP SOFTWARE</div>
            <div style="color: #64748b; font-size: 14px; margin-top: 4px;">{company_name}</div>
            <div style="color: #64748b; font-size: 14px;">{company_addr}</div>
            <div style="color: #64748b; font-size: 14px;">{company_email}</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 24px; font-weight: 800; color: #0f172a;">{invoice.invoice_number}</div>
            <div style="margin-top: 8px;"><span class="badge">{invoice.status}</span></div>
        </div>
    </div>

    <div class="details-grid">
        <div>
            <div style="font-size: 12px; text-transform: uppercase; color: #94a3b8; font-weight: 700; margin-bottom: 6px;">Billed To</div>
            <div style="font-size: 16px; font-weight: 700; color: #1e293b;">{invoice.customer.full_name}</div>
            <div style="font-size: 14px; color: #475569;">{invoice.customer.company_name or ''}</div>
            <div style="font-size: 14px; color: #475569;">{invoice.customer.email}</div>
            <div style="font-size: 14px; color: #475569;">{invoice.customer.phone or ''}</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 14px; color: #475569; margin-bottom: 4px;"><strong>Issue Date:</strong> {invoice.issue_date}</div>
            <div style="font-size: 14px; color: #475569; margin-bottom: 4px;"><strong>Due Date:</strong> {invoice.due_date}</div>
            <div style="font-size: 14px; color: #475569; margin-bottom: 4px;"><strong>Payment Terms:</strong> {invoice.payment_terms}</div>
            {f'<div style="font-size: 14px; color: #475569;"><strong>Subscription:</strong> {invoice.subscription.subscription_number}</div>' if invoice.subscription else ''}
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Description</th>
                <th style="text-align: center;">Qty</th>
                <th style="text-align: right;">Unit Price</th>
                <th style="text-align: right;">Taxes</th>
                <th style="text-align: right;">Amount</th>
            </tr>
        </thead>
        <tbody>
            {lines_html}
        </tbody>
    </table>

    <table class="totals-table">
        <tr>
            <td style="color: #64748b; font-size: 14px;">Subtotal:</td>
            <td style="text-align: right; font-size: 14px; font-weight: 600;">${invoice.subtotal:,.2f}</td>
        </tr>
        <tr>
            <td style="color: #64748b; font-size: 14px;">Taxes:</td>
            <td style="text-align: right; font-size: 14px; font-weight: 600;">+${invoice.tax_amount:,.2f}</td>
        </tr>
        {f'<tr><td style="color: #16a34a; font-size: 14px;">Discount:</td><td style="text-align: right; font-size: 14px; font-weight: 600; color: #16a34a;">-${invoice.discount_amount:,.2f}</td></tr>' if invoice.discount_amount > 0 else ''}
        <tr style="border-top: 2px solid #cbd5e1;">
            <td style="font-size: 16px; font-weight: 800; color: #0f172a; padding-top: 10px;">Total Amount:</td>
            <td style="text-align: right; font-size: 18px; font-weight: 800; color: #714b67; padding-top: 10px;">${invoice.total_amount:,.2f}</td>
        </tr>
        <tr>
            <td style="color: #16a34a; font-size: 14px;">Amount Paid:</td>
            <td style="text-align: right; font-size: 14px; font-weight: 600; color: #16a34a;">${invoice.amount_paid:,.2f}</td>
        </tr>
        <tr style="border-top: 1px dashed #cbd5e1;">
            <td style="font-size: 15px; font-weight: 700; color: {'#dc2626' if invoice.outstanding_amount > 0 else '#16a34a'};">Outstanding Balance:</td>
            <td style="text-align: right; font-size: 15px; font-weight: 700; color: {'#dc2626' if invoice.outstanding_amount > 0 else '#16a34a'};">${invoice.outstanding_amount:,.2f}</td>
        </tr>
    </table>

    <div style="margin-top: 50px; border-top: 1px solid #e2e8f0; padding-top: 20px; text-align: center; color: #94a3b8; font-size: 12px;">
        Thank you for choosing Brightloop Software! For billing inquiries, contact {company_email}.
    </div>
</body>
</html>
"""
