from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.job import GenerationJob


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True
    )

    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generation_jobs.id"),
        nullable=False
    )

    recipient_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    recipient_email: Mapped[str] = mapped_column(
        String(320),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING"
    )

    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    error_message: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    job: Mapped["GenerationJob"] = relationship(
        "GenerationJob",
        back_populates="certificates"
    )