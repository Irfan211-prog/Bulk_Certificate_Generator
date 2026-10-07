# Bulk Certificate Generator

A backend API for generating completion certificates in bulk from a single request.

The application accepts a list of recipients, creates a generation job, processes certificates asynchronously using Celery, stores job and certificate metadata in PostgreSQL, and provides APIs to monitor progress and download individual certificates or a ZIP containing all successfully generated certificates.

## Features

* Bulk certificate generation from a single API request
* Request validation using Pydantic
* Asynchronous background processing using Celery and Redis
* PostgreSQL database for jobs and certificate metadata
* PDF certificate generation using ReportLab
* Per-certificate failure handling
* Job progress tracking
* Individual certificate download
* Bulk ZIP download
* Automated tests using Pytest
* Swagger/OpenAPI documentation through FastAPI

## Tech Stack

* Python 3.11
* FastAPI
* PostgreSQL
* SQLAlchemy
* Celery
* Redis
* ReportLab
* Pydantic
* Pytest

## Project Structure

```text
Bulk_Certificate_Generator/
│
├── app/
│   ├── main.py
│   ├── database.py
│   ├── celery_app.py
│   ├── tasks.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── job.py
│   │   └── certificate.py
│   │
│   ├── schemas/
│   │   └── job.py
│   │
│   └── services/
│       └── certificate_generator.py
│
├── tests/
│   ├── test_jobs.py
│   ├── test_certificate_generator.py
│   ├── test_job_status.py
│   ├── test_certificate_retrieval.py
│   ├── test_failure_handling.py
│   └── test_zip_download.py
│
├── generated_certificates/
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Prerequisites

Install the following:

* Python 3.11+
* PostgreSQL
* Redis
* Git

Docker can be used to run Redis.

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd Bulk_Certificate_Generator
```

### 2. Create and activate a virtual environment

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Create the PostgreSQL database

Create a PostgreSQL database named:

```text
bulk_certificate_db
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```text
DATABASE_URL=postgresql://postgres:<password>@localhost:5432/bulk_certificate_db
```

Replace `<password>` with the PostgreSQL password.

### 6. Start Redis

If Redis is running through Docker:

```powershell
docker run -d --name redis -p 6379:6379 redis
```

If the container already exists:

```powershell
docker start redis
```

Verify Redis:

```powershell
docker exec -it redis redis-cli ping
```

Expected:

```text
PONG
```

## Running the Application

The application requires two processes:

### Terminal 1 — FastAPI

Activate the virtual environment and run:

```powershell
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

### Terminal 2 — Celery Worker

Activate the virtual environment and run:

```powershell
celery -A app.celery_app:celery worker --loglevel=info --pool=solo
```

The Celery worker connects to Redis and processes certificate generation jobs in the background.

## API Endpoints

### Create a bulk generation job

```http
POST /api/jobs/
```

Example request:

```json
{
  "event_name": "AEREO Internship Completion",
  "recipients": [
    {
      "name": "Irfan",
      "email": "irfan@example.com"
    },
    {
      "name": "Rahul",
      "email": "rahul@example.com"
    }
  ]
}
```

Example response:

```json
{
  "job_id": "generated-job-id",
  "status": "PENDING",
  "total": 2,
  "completed": 0,
  "failed": 0
}
```

The endpoint returns `202 Accepted` because certificate generation is performed asynchronously.

### Get job status

```http
GET /api/jobs/{job_id}
```

Example response:

```json
{
  "job_id": "generated-job-id",
  "event_name": "AEREO Internship Completion",
  "status": "PROCESSING",
  "total": 2,
  "completed": 1,
  "failed": 0,
  "progress": 50,
  "completed_at": null
}
```

Possible job statuses:

* `PENDING`
* `PROCESSING`
* `COMPLETED`
* `PARTIAL`
* `FAILED`

### Get certificates for a job

```http
GET /api/jobs/{job_id}/certificates
```

This returns the status and download URL of each certificate.

### Download an individual certificate

```http
GET /api/certificates/{certificate_id}/download
```

The endpoint returns the generated PDF file.

### Download all successful certificates as a ZIP

```http
GET /api/jobs/{job_id}/download
```

For a `PARTIAL` job, only successfully generated certificates are included in the ZIP.

## Certificate Generation Flow

```text
Client
  |
  | POST /api/jobs/
  v
FastAPI
  |
  | Validate request
  v
PostgreSQL
  |
  | Create job + certificate records
  v
Celery Task
  |
  v
Redis
  |
  v
Certificate Generation
  |
  +--> Recipient 1 --> PDF --> COMPLETED
  |
  +--> Recipient 2 --> PDF --> COMPLETED
  |
  +--> Recipient 3 --> Error --> FAILED
  |
  v
Update Job Status
  |
  v
COMPLETED / PARTIAL / FAILED
```

## Failure Handling

Certificate generation is handled independently for each recipient.

If one certificate fails, the exception is caught and recorded against that certificate. Processing continues for the remaining recipients.

For example:

```text
Total:     3
Completed: 2
Failed:    1
Progress:  100%
Status:    PARTIAL
```

This ensures that a failure during generation of one certificate does not prevent valid certificates in the same job from being generated.

## Why Background Processing?

Certificate generation can become expensive when the recipient list is large.

The API therefore creates the job and returns immediately with `202 Accepted`. Celery processes the certificates in the background while the client can poll the job status endpoint.

This keeps the API responsive and separates request handling from certificate generation.

## Database Design

### GenerationJob

Stores information about a bulk generation request.

Important fields:

* `id`
* `event_name`
* `status`
* `total`
* `completed`
* `failed`
* `created_at`
* `completed_at`

### Certificate

Stores information about an individual recipient certificate.

Important fields:

* `id`
* `job_id`
* `recipient_name`
* `recipient_email`
* `status`
* `file_path`
* `error_message`
* `created_at`

Each certificate belongs to one generation job.

## Testing

Run all tests with:

```powershell
pytest tests -v
```

Current test suite covers:

* Job creation
* Empty recipient validation
* Invalid email validation
* Certificate PDF generation
* Job status retrieval
* Certificate retrieval
* Individual PDF download
* Individual certificate failure
* Bulk ZIP download

Expected result:

```text
9 passed
```

## Design Decisions

### FastAPI

FastAPI was selected because it provides:

* Simple API development
* Automatic request validation
* OpenAPI/Swagger documentation
* Good support for asynchronous/background architectures

### PostgreSQL

PostgreSQL is used as the relational database because job and certificate state needs to be persisted reliably.

### Celery + Redis

Celery handles background certificate generation, while Redis is used as the message broker and result backend.

A single Celery task is created for each bulk generation job. The task processes the certificates belonging to that job and handles failures independently.

### ReportLab

ReportLab is used to generate PDF certificates programmatically from a predefined certificate layout.

### Local File Storage

Generated PDFs are currently stored in the local `generated_certificates/` directory.

This keeps the initial implementation simple. In a production deployment, this can be replaced with object storage such as Amazon S3 or another compatible storage service.

## Future Production Improvements

For a production deployment, the following improvements could be added:

* Authentication and authorization
* Idempotency keys for job creation
* Object storage for generated certificates
* Alembic database migrations
* Docker Compose deployment
* Rate limiting
* More detailed structured logging
* Metrics and monitoring
* Secure filename sanitization
* Pagination for large certificate lists
* Multiple certificate templates
* Horizontal Celery worker scaling

## Submission Notes

The application currently supports the complete bulk certificate generation workflow:

1. Submit one bulk request.
2. Receive a job ID.
3. Track generation status and progress.
4. Retrieve individual certificate results.
5. Download successful certificates individually.
6. Download all successful certificates as a ZIP.
7. Continue processing valid recipients even when an individual certificate fails.
8. Run the automated test suite with Pytest.
