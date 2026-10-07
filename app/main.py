import uuid
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.database import engine, Base, SessionLocal
from app.models.job import GenerationJob
from app.models.certificate import Certificate
from app.schemas.job import CreateJobRequest
# from app.services.certificate_generator import generate_certificate
from app.tasks import process_certificate_job
from fastapi.responses import FileResponse


Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "Bulk Certificate Generator API"
    }


@app.get("/db-test")
def database_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        return {
            "database": result.scalar()
        }


@app.post("/api/jobs/", status_code=202)
def create_job(request: CreateJobRequest):

    db = SessionLocal()

    try:
        job_id = str(uuid.uuid4())

        job = GenerationJob(
            id=job_id,
            event_name=request.event_name,
            status="PENDING",
            total=len(request.recipients),
            completed=0,
            failed=0
        )

        db.add(job)

        for recipient in request.recipients:

            certificate_id = str(uuid.uuid4())

            certificate = Certificate(
                id=certificate_id,
                job_id=job_id,
                recipient_name=recipient.name,
                recipient_email=recipient.email,
                status="PENDING"
            )

            db.add(certificate)

        db.commit()

        process_certificate_job.delay(job_id)

        return {
            "job_id": job_id,
            "status": "PENDING",
            "total": len(request.recipients),
            "completed": 0,
            "failed": 0
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    db = SessionLocal()

    try:
        job = db.query(GenerationJob).filter(
            GenerationJob.id == job_id
        ).first()

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        processed = job.completed + job.failed

        progress = round(
            (processed / job.total) * 100,
            2
        ) if job.total > 0 else 0

        return {
            "job_id": job.id,
            "event_name": job.event_name,
            "status": job.status,
            "total": job.total,
            "completed": job.completed,
            "failed": job.failed,
            "progress": progress,
            "completed_at": job.completed_at
        }

    finally:
        db.close()

# @app.get("/test-certificate/")
# def test_certificate():

#     file_path = generate_certificate(
#         recipient_name="Irfan",
#         event_name="AEREO Internship Completion",
#         certificate_id="test-certificate-001"
#     )

#     return {
#         "message": "Certificate generated successfully",
#         "file_path": file_path
#     }

@app.get("/api/certificates/{certificate_id}/download")
def download_certificate(certificate_id: str):

    db = SessionLocal()

    try:
        certificate = db.query(Certificate).filter(
            Certificate.id == certificate_id
        ).first()

        if certificate is None:
            raise HTTPException(
                status_code=404,
                detail="Certificate not found"
            )

        if certificate.status != "COMPLETED":
            raise HTTPException(
                status_code=409,
                detail="Certificate is not available"
            )

        file_path = certificate.file_path

        if file_path is None:
            raise HTTPException(
                status_code=404,
                detail="Certificate file not found"
            )

        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=f"{certificate.recipient_name}_certificate.pdf"
        )

    finally:
        db.close()

@app.get("/api/jobs/{job_id}/certificates")
def get_job_certificates(job_id: str):
    db = SessionLocal()

    try:
        job = db.query(GenerationJob).filter(
            GenerationJob.id == job_id
        ).first()

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        certificates = db.query(Certificate).filter(
            Certificate.job_id == job_id
        ).all()

        return {
            "job_id": job_id,
            "certificates": [
                {
                    "certificate_id": certificate.id,
                    "recipient_name": certificate.recipient_name,
                    "recipient_email": certificate.recipient_email,
                    "status": certificate.status,
                    "download_url": (
                        f"/api/certificates/{certificate.id}/download"
                        if certificate.status == "COMPLETED"
                        else None
                    )
                }
                for certificate in certificates
            ]
        }

    finally:
        db.close()

@app.get("/api/jobs/{job_id}/download")
def download_job_certificates(job_id: str):
    db = SessionLocal()

    try:
        job = db.query(GenerationJob).filter(
            GenerationJob.id == job_id
        ).first()

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        if job.status not in ["COMPLETED", "PARTIAL"]:
            raise HTTPException(
                status_code=409,
                detail="Job processing is not finished"
            )

        certificates = db.query(Certificate).filter(
            Certificate.job_id == job_id,
            Certificate.status == "COMPLETED"
        ).all()

        if not certificates:
            raise HTTPException(
                status_code=404,
                detail="No completed certificates available"
            )

        zip_path = Path("generated_certificates") / f"{job_id}.zip"

        with zipfile.ZipFile(
            zip_path,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zip_file:

            for certificate in certificates:

                if certificate.file_path is None:
                    continue

                file_path = Path(certificate.file_path)

                if not file_path.exists():
                    continue

                zip_file.write(
                    file_path,
                    arcname=f"{certificate.recipient_name}_certificate.pdf"
                )

        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename=f"{job.event_name}_certificates.zip"
        )

    finally:
        db.close()