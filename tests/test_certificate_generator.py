from pathlib import Path

from app.services.certificate_generator import generate_certificate


def test_generate_certificate():

    certificate_id = "pytest-test-certificate"

    file_path = generate_certificate(
        recipient_name="Irfan",
        event_name="AEREO Internship Completion",
        certificate_id=certificate_id
    )

    path = Path(file_path)

    assert path.exists()
    assert path.suffix == ".pdf"
    assert path.stat().st_size > 0

    path.unlink()