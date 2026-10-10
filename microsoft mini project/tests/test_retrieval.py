import zipfile
import io
from app.services.processor import process_generation_job

def test_retrieve_single_certificate_pdf(client, db_session):
    payload = {
        "title": "Retrieval Test Job",
        "recipients": [
            {
                "recipient_name": "Grace Hopper",
                "recipient_email": "grace@example.com",
                "course_name": "Computer Architecture",
                "issue_date": "2026-10-08"
            }
        ]
    }
    res = client.post("/api/v1/certificates/jobs", json=payload)
    job_id = res.json()["id"]
    process_generation_job(job_id, db=db_session)

    # Get certificate details
    status_res = client.get(f"/api/v1/certificates/jobs/{job_id}")
    cert_id = status_res.json()["certificates"][0]["id"]

    # Download PDF
    dl_res = client.get(f"/api/v1/certificates/{cert_id}")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"
    assert dl_res.content.startswith(b"%PDF")

def test_retrieve_job_zip_archive(client, db_session):
    payload = {
        "title": "ZIP Retrieval Job",
        "recipients": [
            {
                "recipient_name": "Hank Pym",
                "recipient_email": "hank@example.com",
                "course_name": "Quantum Mechanics",
                "issue_date": "2026-10-08"
            },
            {
                "recipient_name": "Janet Van Dyne",
                "recipient_email": "janet@example.com",
                "course_name": "Quantum Mechanics",
                "issue_date": "2026-10-08"
            }
        ]
    }
    res = client.post("/api/v1/certificates/jobs", json=payload)
    job_id = res.json()["id"]
    process_generation_job(job_id, db=db_session)

    # Download ZIP archive
    zip_res = client.get(f"/api/v1/certificates/jobs/{job_id}/zip")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"

    # Verify contents of returned ZIP
    with zipfile.ZipFile(io.BytesIO(zip_res.content)) as z:
        namelist = z.namelist()
        assert len(namelist) == 2
        for name in namelist:
            assert name.endswith(".pdf")
            assert "Certificate_" in name

def test_retrieve_non_existent_certificate(client):
    res = client.get("/api/v1/certificates/non-existent-id")
    assert res.status_code == 404
