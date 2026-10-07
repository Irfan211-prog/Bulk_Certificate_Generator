from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pathlib import Path


OUTPUT_DIR = Path("generated_certificates")

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def generate_certificate(
    recipient_name: str,
    event_name: str,
    certificate_id: str
) -> str:
    
    if recipient_name == "FAIL_TEST":
        raise Exception("Intentional test failure")
    
    file_path = OUTPUT_DIR / f"{certificate_id}.pdf"

    pdf = canvas.Canvas(
        str(file_path),
        pagesize=A4
    )

    width, height = A4

    # Title
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(
        width / 2,
        height - 150,
        "CERTIFICATE OF COMPLETION"
    )

    # Recipient name
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(
        width / 2,
        height - 250,
        recipient_name
    )

    # Description
    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(
        width / 2,
        height - 310,
        "has successfully completed"
    )

    # Event name
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(
        width / 2,
        height - 360,
        event_name
    )

    # Finish PDF
    pdf.save()

    return str(file_path)