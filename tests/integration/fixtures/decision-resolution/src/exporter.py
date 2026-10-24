"""Tiny public-export contract used by the decision-resolution eval fixture."""


def encode_public_row(row: dict[str, object]) -> dict[str, object]:
    """Return the stable public fields; do not leak machine-specific provenance."""
    return {"id": row["id"], "value": row["value"]}
