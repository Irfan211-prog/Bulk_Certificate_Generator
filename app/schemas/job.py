from pydantic import BaseModel, EmailStr, Field, field_validator


class Recipient(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=200
    )

    email: EmailStr

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty")

        return value


class CreateJobRequest(BaseModel):

    event_name: str = Field(
        min_length=1,
        max_length=200
    )

    recipients: list[Recipient] = Field(
        min_length=1
    )

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError("Event name cannot be empty")

        return value