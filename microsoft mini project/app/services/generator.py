import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_certificate_pdf(
    file_path: str,
    recipient_name: str,
    course_name: str,
    issue_date: str,
    issuer_name: str = "Organization Admin",
    certificate_id: str = ""
) -> str:
    """
    Generates a professional PDF certificate for a recipient.
    Returns the file path of the generated PDF.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Certificate dimensions: Landscape Letter (11 x 8.5 inches = 792 x 612 pt)
    width, height = landscape(letter)
    
    c = canvas.Canvas(file_path, pagesize=landscape(letter))
    c.setTitle(f"Certificate - {recipient_name}")

    # Color Palette
    PRIMARY_COLOR = colors.HexColor("#1B365D")   # Deep Navy Blue
    SECONDARY_COLOR = colors.HexColor("#D4AF37") # Elegant Gold
    TEXT_COLOR = colors.HexColor("#2C3E50")      # Dark Slate Text
    LIGHT_BG = colors.HexColor("#FAFAFA")        # Warm Soft Background
    BORDER_DARK = colors.HexColor("#0F2027")     # Border accent dark

    # 1. Background Fill
    c.setFillColor(LIGHT_BG)
    c.rect(0, 0, width, height, fill=True, stroke=False)

    # 2. Outer Decorative Border (Navy)
    c.setStrokeColor(PRIMARY_COLOR)
    c.setLineWidth(4)
    c.rect(20, 20, width - 40, height - 40)

    # Inner Decorative Border (Gold)
    c.setStrokeColor(SECONDARY_COLOR)
    c.setLineWidth(2)
    c.rect(28, 28, width - 56, height - 56)

    # Thin Accent Line
    c.setStrokeColor(PRIMARY_COLOR)
    c.setLineWidth(0.5)
    c.rect(33, 33, width - 66, height - 66)

    # 3. Corner Ornamental Circles/Dots
    corner_radius = 6
    corners = [
        (33, 33), (width - 33, 33),
        (33, height - 33), (width - 33, height - 33)
    ]
    c.setFillColor(SECONDARY_COLOR)
    for cx, cy in corners:
        c.circle(cx, cy, corner_radius, fill=True, stroke=False)

    # 4. Header Badge / Header Title
    c.setFillColor(PRIMARY_COLOR)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(width / 2.0, height - 100, "CERTIFICATE OF ACHIEVEMENT")

    # Gold Line Divider under header
    c.setStrokeColor(SECONDARY_COLOR)
    c.setLineWidth(2)
    c.line(width / 2.0 - 150, height - 115, width / 2.0 + 150, height - 115)

    # 5. Subtitle: "PROUDLY PRESENTED TO"
    c.setFillColor(TEXT_COLOR)
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2.0, height - 165, "THIS IS PROUDLY PRESENTED TO")

    # 6. Recipient Name (Large Bold Accent)
    c.setFillColor(PRIMARY_COLOR)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2.0, height - 220, recipient_name.upper())

    # Name Underline Ribbon (Gold)
    name_width = c.stringWidth(recipient_name.upper(), "Helvetica-Bold", 30)
    line_start = max(width / 2.0 - name_width / 2.0 - 20, 100)
    line_end = min(width / 2.0 + name_width / 2.0 + 20, width - 100)
    c.setStrokeColor(SECONDARY_COLOR)
    c.setLineWidth(1.5)
    c.line(line_start, height - 232, line_end, height - 232)

    # 7. Reason / Completion Body Text
    c.setFillColor(TEXT_COLOR)
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2.0, height - 280, "for successfully completing the course / program")

    # 8. Course Name (Bold Dark Navy)
    c.setFillColor(PRIMARY_COLOR)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2.0, height - 325, f"\"{course_name}\"")

    # 9. Additional Text / Recognition
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(width / 2.0, height - 365, "demonstrating outstanding performance, dedication, and mastery.")

    # 10. Footer Section (Date, Certificate ID, Signature)
    # Left Footer: Date & Certificate ID
    c.setFillColor(TEXT_COLOR)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(70, 110, f"DATE OF ISSUANCE: {issue_date}")
    
    if certificate_id:
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#777777"))
        c.drawString(70, 95, f"Certificate ID: {certificate_id}")
    
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.setLineWidth(1)
    c.line(70, 125, 260, 125)

    # Right Footer: Signature Line
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.setLineWidth(1)
    c.line(width - 260, 125, width - 70, 125)

    c.setFillColor(PRIMARY_COLOR)
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 70, 108, issuer_name)

    c.setFillColor(TEXT_COLOR)
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 70, 93, "Authorized Signature")

    # Center Footer Ribbon Gold Seal Stamp Placeholder
    c.setFillColor(SECONDARY_COLOR)
    c.circle(width / 2.0, 105, 25, fill=True, stroke=False)
    c.setFillColor(PRIMARY_COLOR)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2.0, 102, "OFFICIAL")
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(width / 2.0, 93, "VERIFIED")

    c.showPage()
    c.save()
    
    return file_path
