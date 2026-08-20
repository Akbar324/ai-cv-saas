"""AWS runtime configuration models."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AWSSettings(BaseSettings):
    """AWS resources used by the application runtime."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    region: str = Field(
        default="me-central-1",
        validation_alias="AWS_REGION",
        min_length=1,
    )
    profile: str | None = Field(
        default=None,
        validation_alias="AWS_PROFILE",
        min_length=1,
    )
    documents_bucket_name: str = Field(
        validation_alias="DOCUMENTS_BUCKET_NAME",
        min_length=3,
    )
    orders_table_name: str = Field(
        validation_alias="ORDERS_TABLE_NAME",
        min_length=3,
    )


def load_aws_settings() -> AWSSettings:
    """Load AWS runtime settings from environment configuration."""

    return AWSSettings()  # type: ignore[call-arg]
