"""Application services for CV orders."""

from datetime import UTC, datetime
from uuid import uuid4

from backend.models.api import CreateOrderRequest
from backend.models.order import Order
from backend.repositories.order_repository import OrderRepository


def create_order(
    *,
    request: CreateOrderRequest,
    repository: OrderRepository,
) -> Order:
    """Create and persist a new CV order."""

    now = datetime.now(UTC)

    order = Order(
        order_id=f"ord_{uuid4().hex}",
        customer_id=request.customer_id,
        target_job_title=request.target_job_title,
        target_industry=request.target_industry,
        created_at=now,
        updated_at=now,
    )

    repository.create(order)

    return order


def get_order(
    *,
    order_id: str,
    repository: OrderRepository,
) -> Order | None:
    """Return one order by ID."""

    return repository.get(order_id)
