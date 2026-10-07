from datetime import datetime

from app.celery_app import celery
from app.database import SessionLocal
from app.models.job import GenerationJob
from app.models.certificate import Certificate
from app.services.certificate_generator import generate_certificate


@celery.task
def process_certificate_job(job_id: str):

    db = SessionLocal()

    try:
        job = db.query(GenerationJob).filter(
            GenerationJob.id == job_id
        ).first()

        if job is None:
            return "Job not found"

        job.status = "PROCESSING"
        db.commit()

        certificates = db.query(Certificate).filter(
            Certificate.job_id == job_id
        ).all()

        for certificate in certificates:

            try:
                file_path = generate_certificate(
                    recipient_name=certificate.recipient_name,
                    event_name=job.event_name,
                    certificate_id=certificate.id
                )

                certificate.status = "COMPLETED"
                certificate.file_path = file_path
                certificate.error_message = None

                job.completed += 1

            except Exception as error:

                certificate.status = "FAILED"
                certificate.error_message = str(error)

                job.failed += 1

            db.commit()

        if job.failed == 0:
            job.status = "COMPLETED"

        elif job.completed == 0:
            job.status = "FAILED"

        else:
            job.status = "PARTIAL"

        job.completed_at = datetime.utcnow()

        db.commit()

        return {
            "job_id": job_id,
            "status": job.status,
            "completed": job.completed,
            "failed": job.failed
        }

    finally:
        db.close()