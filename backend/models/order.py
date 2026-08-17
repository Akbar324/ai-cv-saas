"""Order domain models for the AI CV SaaS."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from backend.models.cv import CVBaseModel


class OrderStatus(StrEnum):
    """Customer-facing business workflow state."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    HUMAN_REVIEW = "human_review"
    REVISION_REQUIRED = "revision_required"
    APPROVED = "approved"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class ProcessingStatus(StrEnum):
    """Technical processing state for the CV workflow."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PaymentStatus(StrEnum):
    """Payment state for an order."""

    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class OrderDocumentReferences(CVBaseModel):
    """S3 object references associated with an order."""

    source_s3_key: str | None = Field(default=None, max_length=1024)
    current_cv_s3_key: str | None = Field(default=None, max_length=1024)
    preview_s3_key: str | None = Field(default=None, max_length=1024)
    final_pdf_s3_key: str | None = Field(default=None, max_length=1024)
    final_docx_s3_key: str | None = Field(default=None, max_length=1024)


class Order(CVBaseModel):
    """Persistent order metadata and workflow state."""

    order_id: str = Field(min_length=1, max_length=100)
    customer_id: str = Field(min_length=1, max_length=100)

    order_status: OrderStatus = OrderStatus.DRAFT
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING

    target_job_title: str = Field(min_length=1, max_length=150)
    target_industry: str | None = Field(default=None, max_length=150)

    selected_template: str | None = Field(default=None, max_length=100)

    ai_provider: str | None = Field(default=None, max_length=100)
    ai_model: str | None = Field(default=None, max_length=150)

    current_cv_version: int = Field(default=0, ge=0)

    documents: OrderDocumentReferences = Field(default_factory=OrderDocumentReferences)

    created_at: datetime
    updated_at: datetime
