from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from app.models.order import Order
from app.models.user import User
from app.utils.currency import get_currency_from_phone_code

class InvoiceService:
    @staticmethod
    def generate_invoice_pdf(order: Order, user: User) -> BytesIO:
        """
        Generate a PDF invoice for the given order.
        Returns a BytesIO buffer containing the PDF.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                               topMargin=0.5*inch, bottomMargin=0.75*inch)
        elements = []
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        normal_style = styles["Normal"]
        small_style = ParagraphStyle(
            'Small',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666')
        )
        
        # --- Header ---
        elements.append(Paragraph("INVOICE", title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # --- Company Info (Left) and Invoice Details (Right) ---
        company_info = [
            "<b>Mobile Reklame GmbH</b>",
            "Augustenstrasse 48",
            "80333 Munich, Germany",
            "",
            "Phone: +49 171 3104916",
            "Email: info@mobilereklame.de",
            "WhatsApp: +49 171 3104916"
        ]
        
        order_info = [
            f"<b>Invoice #:</b> INV-{str(order.id)[:8].upper()}",
            f"<b>Date:</b> {order.created_at.strftime('%Y-%m-%d')}",
            f"<b>Status:</b> {order.status.upper()}",
            f"<b>Payment:</b> {order.payment_method or 'N/A'}"
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

        # Customer Info
        customer_info = [
            f"<b>Bill To:</b>",
            f"{user.full_name or 'Valued Customer'}",
            f"{user.email}",
            f"{user.phone_number}"
        ]
        
        elements.append(Paragraph("<br/>".join(customer_info), normal_style))
        elements.append(Spacer(1, 0.3 * inch))

        # Determine currency from order (if available) or fallback to user's phone
        currency_code = getattr(order, "currency", None) or getattr(user, "context_currency", None) or get_currency_from_phone_code(user.phone_number)

        # --- Items Table ---
        data = [["Item Description", "Qty", "Price", "Total"]]
        
        total_calculated = 0.0
        for item in order.items:
            # Coupon or Package details
            if item.coupon:
                desc = f"{item.coupon.title} ({item.coupon.code})"
            elif item.package:
                desc = f"{item.package.name} (Package)"
            else:
                desc = "Unknown Item"
            
            line_total = item.price * item.quantity
            total_calculated += line_total
            
            data.append([
                desc,
                str(int(item.quantity)),
                f"{item.price:.2f} {currency_code}",
                f"{line_total:.2f} {currency_code}"
            ])

        # Add total row (without HTML tags - use table styling instead)
        data.append(["", "", "Total", f"{order.total_amount:.2f} {currency_code}"])

        # Table Style
        table = Table(data, colWidths=[4 * inch, 0.8 * inch, 1.0 * inch, 1.2 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Left align description
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#f9f9f9')),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            # Total row style
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (-2, -1), (-1, -1), 11),
            ('LINEABOVE', (-2, -1), (-1, -1), 2, colors.black),
            ('BACKGROUND', (-2, -1), (-1, -1), colors.HexColor('#e8e8e8')),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.5 * inch))

        # --- Footer / Thank You ---
        footer_text = "<b>Thank you for your business!</b>"
        elements.append(Paragraph(footer_text, normal_style))
        elements.append(Spacer(1, 0.3 * inch))
        
        # --- Company Imprint (Legal Information) ---
        imprint_title = ParagraphStyle(
            'ImprintTitle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6
        )
        
        imprint_data = [
            "<b>IMPRINT (IMPRESSUM)</b>",
            "",
            "<b>Mobile Reklame GmbH</b>",
            "Augustenstrasse 48",
            "80333 Munich, Germany",
            "",
            "<b>Represented by:</b>",
            "Managing Director Ralph Clemens Martin",
            "",
            "<b>Contact:</b>",
            "Phone: +49 171 3104916",
            "Email: info@mobilereklame.de",
            "WhatsApp: +49 171 3104916",
            "",
            "<b>Commercial Register:</b>",
            "Registered in: Handelsregister B (Commercial Register)",
            "Register Court: Amtsgericht München",
            "Registration Number: HRB 172423",
            "",
            "<b>VAT Identification Number (Ust-IdNr.):</b>",
            "DE25 8628 411"
        ]
        
        elements.append(Paragraph("<br/>".join(imprint_data), small_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer
