import pytest
from app.schemas import RecipientInput
from pydantic import ValidationError

def test_valid_recipient_schema():
    recipient = RecipientInput(
        recipient_name="Alice Smith",
        recipient_email="alice@example.com",
        course_name="Python & FastAPI Masterclass",
        issue_date="2026-10-08"
    )
    assert recipient.recipient_name == "Alice Smith"
    assert recipient.recipient_email == "alice@example.com"

def test_invalid_email_schema():
    with pytest.raises(ValidationError) as exc_info:
        RecipientInput(
            recipient_name="Bob",
            recipient_email="not-an-email",
            course_name="Data Science",
            issue_date="2026-10-08"
        )
    assert "recipient_email" in str(exc_info.value)

def test_empty_recipient_name_schema():
    with pytest.raises(ValidationError) as exc_info:
        RecipientInput(
            recipient_name="   ",
            recipient_email="bob@example.com",
            course_name="Data Science",
            issue_date="2026-10-08"
        )
    assert "recipient_name" in str(exc_info.value)

def test_api_empty_recipients_list(client):
    response = client.post("/api/v1/certificates/jobs", json={"recipients": []})
    assert response.status_code in [400, 422]
