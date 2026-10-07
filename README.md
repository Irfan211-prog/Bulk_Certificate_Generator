# Bulk Certificate Generator

A backend API for generating completion certificates in bulk from a single request.

The application accepts a list of recipients, creates a generation job, processes certificates asynchronously using Celery, stores job and certificate metadata in PostgreSQL, and provides APIs to monitor progress and download individual certificates or a ZIP containing all successfully generated certificates.

**GitHub Repository:**
https://github.com/Irfan211-prog/Bulk_Certificate_Generator

---

## Features

* Bulk certificate generation from a single API request
* Request validation using Pydantic
* Asynchronous background processing using Celery and Redis
* PostgreSQL database for jobs and certificate metadata
* PDF certificate generation using ReportLab
* Per-certificate failure handling
* Job status and progress tracking
* Individual certificate retrieval and download
* Bulk ZIP download of successfully generated certificates
* Automated tests using Pytest
* Swagger/OpenAPI documentation through FastAPI

---

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

---

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
│   ├── pytest.ini
│   ├── test_jobs.py
│   ├── test_certificate_generator.py
│   ├── test_job_status.py
│   ├── test_certificate_retrieval.py
│   ├── test_failure_handling.py
│   └── test_zip_download.py
│
├── .gitignore
├── requirements.txt
└── README.md
```

### Runtime-generated files

The following are created locally when the application runs but are intentionally excluded from Git:

* `.env` — contains local environment configuration
* `generated_certificates/` — contains generated PDF and ZIP files
* `venv/` — Python virtual environment

---

## Prerequisites

Install the following:

* Python 3.11+
* PostgreSQL
* Redis
* Git

Docker can be used to run Redis.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Irfan211-prog/Bulk_Certificate_Generator.git
cd Bulk_Certificate_Generator
```

### 2. Create and activate a virtual environment

#### Windows

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

Create a `.env` file in the project root.

```env
DATABASE_URL=postgresql+psycopg2://postgres:<password>@localhost:5432/bulk_certificate_db
```

Replace `<password>` with your local PostgreSQL password.

**Important:** The `.env` file is intentionally excluded from version control and should never be committed to Git.

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

Expected output:

```text
PONG
```

---

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

Swagger/OpenAPI documentation:

```text
http://127.0.0.1:8000/docs
```

### Terminal 2 — Celery Worker

Activate the virtual environment and run:

```powershell
celery -A app.celery_app:celery worker --loglevel=info --pool=solo
```

The Celery worker connects to Redis and processes certificate generation jobs in the background.

---

## API Endpoints

### 1. Create a Bulk Generation Job

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

---

### 2. Get Job Status

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

The `progress` value is calculated from:

```text
(completed + failed) / total × 100
```

Therefore, a `PARTIAL` job can correctly have `100%` progress when all recipients have finished processing but some failed.

---

### 3. Get Certificates for a Job

```http
GET /api/jobs/{job_id}/certificates
```

This returns the status and download URL of each certificate associated with the job.

Example:

```json
{
  "job_id": "generated-job-id",
  "certificates": [
    {
      "certificate_id": "certificate-id-1",
      "recipient_name": "Irfan",
      "recipient_email": "irfan@example.com",
      "status": "COMPLETED",
      "download_url": "/api/certificates/certificate-id-1/download"
    }
  ]
}
```

---

### 4. Download an Individual Certificate

```http
GET /api/certificates/{certificate_id}/download
```

The endpoint returns the generated PDF file.

---

### 5. Download All Successful Certificates as a ZIP

```http
GET /api/jobs/{job_id}/download
```

For a `COMPLETED` job, all successful certificates are included.

For a `PARTIAL` job, only successfully generated certificates are included in the ZIP.

---

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

---

## Validation and Failure Handling

### Request Validation

Recipient data is validated before a generation job is created.

The API validates:

* Recipient name is not empty
* Recipient name length is within the allowed range
* Recipient email is a valid email address
* At least one recipient is provided
* Event name is not empty

Invalid request data returns an appropriate `422 Unprocessable Entity` response.

### Individual Certificate Failure

Once a valid bulk job has been created, certificate generation is handled independently for each recipient.

If one certificate fails during generation:

1. The failure is caught.
2. The certificate is marked as `FAILED`.
3. The error message is stored.
4. The job's failed count is incremented.
5. Processing continues for the remaining certificates.

For example:

```text
Total:       3
Completed:   2
Failed:      1
Progress:    100%
Status:      PARTIAL
```

This ensures that a failure during generation of one certificate does not prevent valid certificates in the same job from being generated.

---

## Why Background Processing?

Certificate generation can become expensive when the recipient list is large.

The API therefore creates the job and returns immediately with `202 Accepted`.

Celery processes the certificates in the background while the client can poll the job status endpoint.

This approach:

* Keeps the API responsive
* Avoids keeping the HTTP request open during generation
* Supports larger recipient lists
* Separates request handling from certificate generation
* Allows generation progress to be tracked

A single Celery task is created for each bulk generation request, and that task processes all certificates belonging to the job.

---

## Database Design

The application uses PostgreSQL with SQLAlchemy.

### GenerationJob

Stores information about a bulk certificate generation request.

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

Stores information about an individual certificate.

Important fields:

* `id`
* `job_id`
* `recipient_name`
* `recipient_email`
* `status`
* `file_path`
* `error_message`
* `created_at`

Relationship:

```text
GenerationJob
      |
      | 1
      |
      |----< many
             |
        Certificate
```

Each certificate belongs to exactly one generation job.

---

## Testing

Run all tests with:

```powershell
pytest tests -v
```

The test suite covers:

* Job creation
* Empty recipient validation
* Invalid email validation
* Certificate PDF generation
* Job status retrieval
* Certificate retrieval
* Individual PDF download
* Individual certificate failure handling
* Bulk ZIP download

### Test Result

The complete test suite currently passes:

```text
9 passed
```

---

## Design Decisions

### FastAPI

FastAPI was selected because it provides:

* Simple API development
* Automatic request validation
* OpenAPI/Swagger documentation
* Clear endpoint definitions
* Good integration with background processing

### PostgreSQL

PostgreSQL is used as the relational database because job and certificate state needs to be persisted reliably.

The database stores both the overall generation job and individual certificate records.

### Celery + Redis

Celery handles background certificate generation, while Redis is used as the message broker and result backend.

A single Celery task is created for each bulk generation job. The task processes the certificates belonging to that job and handles individual failures independently.

### ReportLab

ReportLab is used to generate PDF certificates programmatically from a predefined certificate layout.

The assignment requires only one predefined certificate template, so a template editor or multiple template system was not implemented.

### Local File Storage

Generated PDFs are currently stored in the local `generated_certificates/` directory.

This keeps the initial implementation simple and avoids introducing unnecessary infrastructure for the take-home assignment.

For a production deployment, this can be replaced with object storage such as Amazon S3 or another S3-compatible storage service.

---

## Future Production Improvements

The current implementation focuses on the requirements of the assignment.

For a production deployment, the following improvements could be added:

* Authentication and authorization
* Idempotency keys for job creation
* Object storage for generated certificates
* Alembic database migrations
* Docker Compose deployment
* Rate limiting
* Structured logging
* Metrics and monitoring
* Secure filename sanitization
* Pagination for large certificate lists
* Multiple certificate templates
* Horizontal Celery worker scaling
* More robust retry policies for transient generation failures

---

## Assignment Requirement Coverage

The implementation covers the required functionality:

| Requirement                           | Implementation                             |
| ------------------------------------- | ------------------------------------------ |
| Accept certificate generation request | `POST /api/jobs/`                          |
| Validate recipient data               | Pydantic validation                        |
| Generate certificates                 | ReportLab                                  |
| Single predefined template            | ReportLab certificate layout               |
| Track generation status               | Job status fields                          |
| Track progress                        | `total`, `completed`, `failed`, `progress` |
| Bulk processing                       | Multiple recipients in one request         |
| Background processing                 | Celery + Redis                             |
| Individual failure handling           | Per-certificate exception handling         |
| Retrieve certificates                 | Certificate listing + PDF download         |
| Bulk download                         | ZIP endpoint                               |
| Relational database                   | PostgreSQL                                 |
| Automated testing                     | Pytest                                     |
| API documentation                     | FastAPI Swagger/OpenAPI                    |

---

## Submission Notes

The application supports the complete bulk certificate generation workflow:

1. Submit one bulk certificate generation request.
2. Receive a job ID.
3. Track generation status and progress.
4. Retrieve individual certificate results.
5. Download successful certificates individually.
6. Download all successful certificates as a ZIP.
7. Continue processing valid recipients when an individual certificate generation fails.
8. Run the automated test suite with Pytest.

The project is available on GitHub:

**https://github.com/Irfan211-prog/Bulk_Certificate_Generator**
