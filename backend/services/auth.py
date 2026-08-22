"""Authentication helpers for API Gateway JWT-authorized requests."""

from __future__ import annotations

from typing import Any


class AuthenticationError(ValueError):
    """Raised when authenticated identity claims are unavailable."""


def authenticated_customer_id(
    event: dict[str, Any],
) -> str:
    """Return the authenticated Cognito subject from API Gateway claims."""

    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )

    customer_id = claims.get("sub")

    if not isinstance(customer_id, str) or not customer_id.strip():
        raise AuthenticationError("Authenticated customer identity is unavailable.")

    return customer_id
