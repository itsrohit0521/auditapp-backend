from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from datetime import datetime
from io import BytesIO


def generate_pdf(framework_name, total_risk, risk_percentage, risk_level, details):

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    elements = []
    styles = getSampleStyleSheet()

    # -----------------------------
    # Report Title
    # -----------------------------

    elements.append(
        Paragraph(f"{framework_name} Compliance Report", styles['Heading1'])
    )

    elements.append(Spacer(1, 0.3 * inch))

    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    elements.append(
        Paragraph(f"Generated on: {current_date}", styles['Normal'])
    )

    elements.append(Spacer(1, 0.3 * inch))

    # -----------------------------
    # Risk Summary
    # -----------------------------

    elements.append(
        Paragraph(f"Total Risk Score: {total_risk}", styles['Normal'])
    )

    elements.append(
        Paragraph(f"Risk Percentage: {risk_percentage:.2f}%", styles['Normal'])
    )

    elements.append(
        Paragraph(f"Overall Risk Level: {risk_level}", styles['Normal'])
    )

    elements.append(Spacer(1, 0.5 * inch))

    # -----------------------------
    # Compliance Issues
    # -----------------------------

    if details:

        elements.append(
            Paragraph("Compliance Issues Identified:", styles['Heading2'])
        )

        elements.append(Spacer(1, 0.2 * inch))

        issue_list = []

        for item in details:

            issue_text = (
                f"{item['control']} - {item['description']} "
                f"(Recommended: {item['recommendation']})"
            )

            issue_list.append(
                ListItem(Paragraph(issue_text, styles['Normal']))
            )

        elements.append(ListFlowable(issue_list))

    else:

        elements.append(
            Paragraph("No major compliance issues detected.", styles['Normal'])
        )

    # -----------------------------
    # Build PDF
    # -----------------------------

    doc.build(elements)

    buffer.seek(0)

    # Return raw bytes for API download
    return buffer.getvalue()