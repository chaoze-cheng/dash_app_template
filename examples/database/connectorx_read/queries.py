import connectorx as cx
import pandas as pd


def read_public_items(uri: str, limit: int = 100) -> pd.DataFrame:
    """Read public rows using a bounded integer limit (demo schema)."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
        raise ValueError("limit must be an integer between 1 and 1000")
    # This SQL uses only a validated integer; never interpolate user strings.
    sql = f"SELECT id, title FROM items WHERE visibility = 'public' ORDER BY id LIMIT {limit}"
    return cx.read_sql(uri, sql, return_type="pandas")
