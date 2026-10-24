"""Internal row parser used by the decision-resolution evaluation fixture."""


def parse_row(raw: object) -> dict[str, object]:
    """Parse the required internal row fields with intentionally broad errors."""
    if not isinstance(raw, dict) or "id" not in raw or "value" not in raw:
        raise ValueError("invalid row")
    return {"id": raw["id"], "value": raw["value"]}
