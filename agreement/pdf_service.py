"""
PDF generation for agreements.

Generates a printable "Agreement Summary" document containing the signer's
details, the agreement template info, the current status and the captured
signature image. Uses ReportLab (pure Python, no system dependencies).
"""
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader

BRAND_DARK = HexColor('#1a237e')
BRAND_ACCENT = HexColor('#3949ab')
LIGHT_ROW = HexColor('#f4f6fb')


def generate_agreement_pdf(agreement) -> bytes:
    """Return the generated agreement summary PDF as bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title=f'Agreement Summary — {agreement.your_name}',
        author='Digital Agreement Signing Platform',
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'BrandTitle', parent=styles['Title'], textColor=BRAND_DARK, fontSize=20, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'BrandSubtitle', parent=styles['Normal'], textColor=BRAND_ACCENT,
        alignment=TA_CENTER, fontSize=11
    )
    label_style = ParagraphStyle(
        'FieldLabel', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5,
        textColor=HexColor('#444444')
    )
    value_style = ParagraphStyle('FieldValue', parent=styles['Normal'], fontSize=10)

    story = [
        Paragraph('Digital Agreement Signing', title_style),
        Paragraph('Official Agreement Summary Document', subtitle_style),
        Spacer(1, 0.5 * cm),
    ]

    gender_display = agreement.get_gender_display()
    status_display = agreement.get_status_display()
    template_name = agreement.pdf_agreement_name or (
        agreement.pdf_agreement.type_of_agreement if agreement.pdf_agreement else '—'
    )

    rows = [
        ('Agreement type', template_name),
        ('Full name', agreement.your_name),
        ("Father's name", agreement.father_name),
        ("Grand father's name", agreement.grand_father_name),
        ('Gender', gender_display),
        ('Address', agreement.address),
        ('City', agreement.city),
        ('Nationality', agreement.nationality),
        ('Phone number', agreement.phone_number),
        ('Email', agreement.email_account or '—'),
        ('Submitted on', agreement.submited_date.strftime('%Y-%m-%d %H:%M UTC') if agreement.submited_date else '—'),
        ('Status', status_display.upper()),
    ]

    table_data = [[Paragraph(label, label_style), Paragraph(str(value or '—'), value_style)]
                  for label, value in rows]
    detail_table = Table(table_data, colWidths=[5.5 * cm, 11 * cm])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_ROW),
        ('GRID', (0, 0), (-1, -1), 0.4, HexColor('#c5cae9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 1 * cm))

    # --- Signature block ---
    story.append(Paragraph('Signature', label_style))
    story.append(Spacer(1, 0.2 * cm))
    signature_added = False
    try:
        if agreement.signature and agreement.signature.storage.exists(agreement.signature.name):
            with agreement.signature.open('rb') as sig_file:
                sig_img = RLImage(ImageReader(sig_file), width=6 * cm, height=2.6 * cm,
                                  preserveAspectRatio=True, anchor='w')
            signature_block = Table([[sig_img]], colWidths=[7 * cm], rowHeights=[3 * cm])
            signature_block.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.6, HexColor('#9fa8da')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(signature_block)
            signature_added = True
    except Exception:
        signature_added = False

    if not signature_added:
        story.append(Paragraph('(signature not available)', styles['Italic']))
        story.append(Spacer(1, 1 * cm))

    story.append(Spacer(1, 0.8 * cm))
    footer = ParagraphStyle(
        'Footer', parent=styles['Normal'], fontSize=8, textColor=HexColor('#888888'),
        alignment=TA_CENTER
    )
    story.append(Paragraph(
        f'Generated automatically on {datetime.utcnow():%Y-%m-%d %H:%M} · '
        f'Digital Agreement Signing Platform', footer
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
