import os
import tempfile
from app.services.generator import generate_certificate_pdf

def test_generate_certificate_pdf_creates_file():
    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = os.path.join(tmp_dir, "test_certificate.pdf")
        
        result_path = generate_certificate_pdf(
            file_path=pdf_path,
            recipient_name="Jane Doe",
            course_name="Machine Learning Engineering",
            issue_date="2026-10-08",
            issuer_name="AI Institute",
            certificate_id="CERT-12345"
        )
        
        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 0
        
        # Verify PDF header magic bytes
        with open(result_path, "rb") as f:
            header = f.read(4)
            assert header == b"%PDF"
