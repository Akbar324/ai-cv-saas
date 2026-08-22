"""Runtime secret retrieval."""

from __future__ import annotations

import json
from typing import Any


def get_json_secret(
    *,
    secret_id: str,
    session: Any,
    region: str,
) -> dict[str, str]:
    """Retrieve and validate one JSON Secrets Manager secret."""

    client = session.client(
        "secretsmanager",
        region_name=region,
    )

    response = client.get_secret_value(
        SecretId=secret_id,
    )

    value = response.get("SecretString")

    if not isinstance(value, str):
        raise RuntimeError("Secret does not contain SecretString.")

    payload = json.loads(value)

    if not isinstance(payload, dict):
        raise RuntimeError("Secret value must be a JSON object.")

    result: dict[str, str] = {}

    for key, item in payload.items():
        if isinstance(key, str) and isinstance(item, str):
            result[key] = item

    return result
