from app.services.processor import process_generation_job

def test_create_generation_job(client):
    payload = {
        "title": "Full Stack Web Dev Bootcamp",
        "recipients": [
            {
                "recipient_name": "Charlie Brown",
                "recipient_email": "charlie@example.com",
                "course_name": "Full Stack Web Dev",
                "issue_date": "2026-10-08",
                "issuer_name": "Tech Academy"
            }
        ]
    }
    
    response = client.post("/api/v1/certificates/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert data["title"] == "Full Stack Web Dev Bootcamp"
    assert data["total_count"] == 1
    assert len(data["certificates"]) == 1
    assert data["certificates"][0]["recipient_name"] == "Charlie Brown"

def test_job_processing_and_status(client, db_session):
    payload = {
        "title": "Data Analytics 2026",
        "recipients": [
            {
                "recipient_name": "Diana Prince",
                "recipient_email": "diana@example.com",
                "course_name": "Data Analytics",
                "issue_date": "2026-10-08"
            },
            {
                "recipient_name": "Bruce Wayne",
                "recipient_email": "bruce@example.com",
                "course_name": "Data Analytics",
                "issue_date": "2026-10-08"
            }
        ]
    }
    
    res = client.post("/api/v1/certificates/jobs", json=payload)
    assert res.status_code == 202
    job_id = res.json()["id"]

    # Trigger background worker directly passing test db_session
    process_generation_job(job_id, db=db_session)

    # Fetch updated job status via API
    status_res = client.get(f"/api/v1/certificates/jobs/{job_id}")
    assert status_res.status_code == 200
    job_data = status_res.json()
    
    assert job_data["status"] == "COMPLETED"
    assert job_data["success_count"] == 2
    assert job_data["failure_count"] == 0
    assert len(job_data["certificates"]) == 2
    for cert in job_data["certificates"]:
        assert cert["status"] == "SUCCESS"
        assert cert["download_url"] is not None

def test_partial_failure_handling(client, db_session):
    # Job containing 1 valid recipient and 1 invalid recipient (invalid email format)
    payload = {
        "title": "Mixed Batch Event",
        "recipients": [
            {
                "recipient_name": "Eve Adams",
                "recipient_email": "eve@example.com",
                "course_name": "Cybersecurity",
                "issue_date": "2026-10-08"
            },
            {
                "recipient_name": "Frank Castle",
                "recipient_email": "bad-email-no-at-sign",  # Invalid email format!
                "course_name": "Cybersecurity",
                "issue_date": "2026-10-08"
            }
        ]
    }
    
    res = client.post("/api/v1/certificates/jobs", json=payload)
    assert res.status_code == 202
    job_id = res.json()["id"]

    # Run worker logic
    process_generation_job(job_id, db=db_session)

    status_res = client.get(f"/api/v1/certificates/jobs/{job_id}")
    assert status_res.status_code == 200
    job_data = status_res.json()

    assert job_data["status"] == "PARTIALLY_COMPLETED"
    assert job_data["success_count"] == 1
    assert job_data["failure_count"] == 1

    # Verify individual item status
    certs = job_data["certificates"]
    success_item = next(c for c in certs if c["recipient_name"] == "Eve Adams")
    failed_item = next(c for c in certs if c["recipient_name"] == "Frank Castle")

    assert success_item["status"] == "SUCCESS"
    assert success_item["download_url"] is not None

    assert failed_item["status"] == "FAILED"
    assert "Validation Error" in failed_item["error_message"]
    assert failed_item["download_url"] is None
