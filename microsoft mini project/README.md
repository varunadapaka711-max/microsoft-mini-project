# Bulk Certificate Generator API

A FastAPI backend for processing bulk certificate generation requests. The API validates recipient records, renders PDF certificates asynchronously using ReportLab, tracks job status, handles individual failures gracefully, and provides endpoints to download single certificates or batch ZIP archives.

## Features

- **Bulk Certificate Generation**: Submit recipient lists in a single request.
- **Background Processing**: PDF generation runs asynchronously via FastAPI background tasks.
- **Failure Resilience**: Invalid data or rendering issues mark individual certificates as failed without interrupting the rest of the batch.
- **Status & Progress Tracking**: Real-time status updates (`PENDING`, `PROCESSING`, `COMPLETED`, `PARTIALLY_COMPLETED`, `FAILED`).
- **Retrieval Options**: Download single PDF certificates or a ZIP archive containing all generated certificates for a job.

## Tech Stack

- **Python 3.12**
- **FastAPI** & **Pydantic v2**
- **SQLAlchemy** & **SQLite**
- **ReportLab** (PDF generation)
- **Pytest** & **HTTPX** (Test suite)

## Project Structure

```
.
├── app/
│   ├── main.py               # Application entrypoint
│   ├── config.py             # App configuration & paths
│   ├── database.py           # Database session setup
│   ├── models.py             # SQLAlchemy models (Job, CertificateItem)
│   ├── schemas.py            # Pydantic schemas
│   ├── services/
│   │   ├── generator.py      # PDF rendering service
│   │   └── processor.py      # Background worker logic
│   └── routers/
│       └── certificates.py   # API endpoints
├── storage/
│   └── certificates/         # Generated PDF output directory
├── tests/                    # Pytest test suite
├── sample_data.json          # Example request payload
├── requirements.txt
└── README.md
```

## Setup & Running

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository_url>
cd "microsoft mini project"

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

Access the interactive API documentation at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 3. Run Tests

```bash
pytest -v
```

---

## API Usage

### Create a Bulk Generation Job

`POST /api/v1/certificates/jobs`

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/certificates/jobs" \
     -H "Content-Type: application/json" \
     -d @sample_data.json
```

**Response (202 Accepted)**:
```json
{
  "id": "7c6cb21e-5384-423d-aeb0-aff796c4233f",
  "title": "Annual Developer Certification 2026",
  "status": "PENDING",
  "total_count": 4,
  "success_count": 0,
  "failure_count": 0,
  "created_at": "2026-10-08T16:55:00Z",
  "updated_at": "2026-10-08T16:55:00Z",
  "certificates": [ ... ]
}
```

### Check Job Progress

`GET /api/v1/certificates/jobs/{job_id}`

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/certificates/jobs/<JOB_ID>"
```

### Download Single PDF Certificate

`GET /api/v1/certificates/{certificate_id}`

```bash
curl -O -J "http://127.0.0.1:8000/api/v1/certificates/<CERTIFICATE_ID>"
```

### Download All Certificates as ZIP

`GET /api/v1/certificates/jobs/{job_id}/zip`

```bash
curl -O -J "http://127.0.0.1:8000/api/v1/certificates/jobs/<JOB_ID>/zip"
```

---

## Design Decisions

- **Background Workers**: Generation is handled asynchronously via FastAPI `BackgroundTasks` to prevent HTTP request timeouts on large batches. The database schema separates job metadata from certificate items, allowing easy migration to Celery/Redis if required.
- **Fault Handling**: Recipient validation and rendering errors are isolated per item. Failed items store an error message while allowing valid items in the batch to complete.
- **PDF Generation**: ReportLab was selected over HTML-to-PDF rendering engines to eliminate system-level binary dependencies (like wkhtmltopdf) while ensuring fast, consistent rendering.
