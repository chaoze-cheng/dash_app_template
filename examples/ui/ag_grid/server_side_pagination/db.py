"""Demo DB adapter: replace with src/db/queries/ implementation in target app."""

DEMO_ROWS = [{"id": i, "name": f"Record {i}", "score": i % 17} for i in range(1, 201)]


def fetch_rows(start: int, end: int, sort_column: str | None, descending: bool):
    if start < 0 or end < start:
        raise ValueError("invalid pagination range")
    allowed = {"id", "name", "score"}
    if sort_column is not None and sort_column not in allowed:
        raise ValueError("unsupported sort column")
    data = sorted(DEMO_ROWS, key=lambda row: row[sort_column], reverse=descending) if sort_column else DEMO_ROWS
    return data[start:end], len(data)
