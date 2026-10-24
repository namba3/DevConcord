# Internal parser notes

`parse_row` accepts an object with `id` and `value` fields and returns those fields for internal use. Invalid input currently raises `ValueError("invalid row")`. Error details are intentionally broad in this baseline; do not include raw input, credentials, or machine-specific paths in future messages.

This internal parser is separate from the public JSON export contract in REQ-1001/1002 and ADR-1001. ISS-1003 may clarify its errors and this document without changing the public response, stored data, or configuration.
