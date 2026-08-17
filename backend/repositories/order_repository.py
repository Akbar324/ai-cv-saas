"""Persistence contract for CV orders."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend.models.order import Order, OrderStatus, ProcessingStatus


@dataclass(frozen=True)
class OrderPage:
    """One paginated page of orders."""

    items: list[Order]
    next_token: str | None = None


class OrderRepository(ABC):
    """Storage-independent persistence contract for orders."""

    @abstractmethod
    def create(self, order: Order) -> None:
        """Persist a new order."""

    @abstractmethod
    def get(self, order_id: str) -> Order | None:
        """Return one order by ID."""

    @abstractmethod
    def update(self, order: Order) -> None:
        """Persist the current state of an existing order."""

    @abstractmethod
    def list_by_customer(
        self,
        customer_id: str,
        *,
        limit: int = 50,
        next_token: str | None = None,
    ) -> OrderPage:
        """Return a customer's orders newest first."""

    @abstractmethod
    def list_by_order_status(
        self,
        status: OrderStatus,
        *,
        limit: int = 50,
        next_token: str | None = None,
    ) -> OrderPage:
        """Return orders in one business workflow state."""

    @abstractmethod
    def list_by_processing_status(
        self,
        status: ProcessingStatus,
        *,
        limit: int = 50,
        next_token: str | None = None,
    ) -> OrderPage:
        """Return orders in one technical processing state."""

    @abstractmethod
    def list_recent(
        self,
        *,
        limit: int = 50,
        next_token: str | None = None,
    ) -> OrderPage:
        """Return recent orders for the admin view."""
