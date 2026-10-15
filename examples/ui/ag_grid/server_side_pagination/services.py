from db import fetch_rows


def get_page(start_row: int, end_row: int, sort_model: list | None):
    """Validate UI request and orchestrate DB-layer pagination."""
    if end_row - start_row > 200 or start_row < 0 or end_row <= start_row:
        raise ValueError("invalid page size")
    sort = (sort_model or [{}])[0]
    column = sort.get("colId")
    descending = sort.get("sort") == "desc"
    return fetch_rows(start_row, end_row, column, descending)
