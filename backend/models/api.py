"""HTTP API request and response models."""

from pydantic import Field

from backend.models.cv import CVBaseModel


class CreateOrderRequest(CVBaseModel):
    """Customer input required to create a CV order."""

    customer_id: str = Field(min_length=1, max_length=100)
    target_job_title: str = Field(min_length=1, max_length=150)
    target_industry: str | None = Field(default=None, max_length=150)
    job_description: str | None = Field(default=None, max_length=20_000)
    additional_customer_information: str | None = Field(
        default=None,
        max_length=20_000,
    )


class CreateUploadTargetRequest(CVBaseModel):
    """Request for a temporary source-CV upload target."""

    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=150)
