"""Runtime dependency construction for deployed application handlers."""

from backend.models.aws_settings import load_aws_settings
from backend.repositories.order_repository import OrderRepository
from backend.services.repository_factory import create_order_repository


def get_order_repository() -> OrderRepository:
    """Create the configured order repository."""

    settings = load_aws_settings()
    return create_order_repository(settings)
