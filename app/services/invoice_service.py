from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from app.models.order import Order
from app.models.user import User
from app.utils.currency import get_currency_from_phone_code, get_currency_symbol

class InvoiceService:
    @staticmethod
    def generate_invoice_pdf(order: Order, user: User) -> BytesIO:
        """
        Generate a PDF invoice for the given order.
        Returns a BytesIO buffer containing the PDF.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = styles["Heading1"]
        title_style.alignment = 1  # Center
        normal_style = styles["Normal"]
        
        # --- Header ---
        elements.append(Paragraph("INVOICE", title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # --- Invoice Details ---
        # Left: Company Info, Right: Order Info
        company_info = [
            "VoucherGalaxy Inc.",
            "123 Coupon St, Savings City",
            "support@vouchergalaxy.com",
            "www.vouchergalaxy.com"
        ]
        
        order_info = [
            f"Invoice #: INV-{str(order.id)[:8].upper()}",
            f"Date: {order.created_at.strftime('%Y-%m-%d')}",
            f"Status: {order.status.upper()}",
            f"Payment: {order.payment_method or 'N/A'}"
        ]

        # Customer Info
        customer_info = [
            f"Bill To:",
            f"{user.full_name or 'Valued Customer'}",
            f"{user.email}",
            f"{user.phone_number}"
        ]

        # Organize header data into a table
        header_data = [
            [Paragraph("<br/>".join(company_info), normal_style), 
             Paragraph("<br/>".join(order_info), normal_style)]
        ]
        header_table = Table(header_data, colWidths=[3.5 * inch, 3.5 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(Paragraph("<b>Bill To:</b>", normal_style))
        elements.append(Paragraph("<br/>".join(customer_info[1:]), normal_style))
        elements.append(Spacer(1, 0.3 * inch))

        # Determine currency
        currency_code = getattr(user, "context_currency", None) or get_currency_from_phone_code(user.phone_number)
        currency_symbol = get_currency_symbol(currency_code)

        # --- Items Table ---
        data = [["Item Description", "Qty", "Price", "Total"]]
        
        total_calculated = 0.0
        for item in order.items:
            # Coupon details
            coupon_title = item.coupon.title if item.coupon else "Unknown Item"
            coupon_code = item.coupon.code if item.coupon else "N/A"
            desc = f"{coupon_title} ({coupon_code})"
            
            line_total = item.price * item.quantity
            total_calculated += line_total
            
            data.append([
                desc,
                str(item.quantity),
                f"{currency_symbol}{item.price:.2f}",
                f"{currency_symbol}{line_total:.2f}"
            ])

        # Add total row
        data.append(["", "", "Total", f"{currency_symbol}{order.total_amount:.2f}"])

        # Table Style
        table = Table(data, colWidths=[4 * inch, 0.8 * inch, 1.0 * inch, 1.2 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Left align description
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -2), 1, colors.black),
            # Total row style
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (-2, -1), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.5 * inch))

        # --- Footer ---
        footer_text = "Thank you for your business!"
        elements.append(Paragraph(footer_text, styles["Italic"]))

        doc.build(elements)
        buffer.seek(0)
        return buffer
