from dash import Input, Output
from services import get_page


def register_table_callbacks(app):
    @app.callback(Output("example-grid", "getRowsResponse"), Input("example-grid", "getRowsRequest"))
    def load_rows(request):
        if not request:
            return {"rowData": [], "rowCount": 0}
        rows, total = get_page(
            request.get("startRow", 0),
            request.get("endRow", 50),
            request.get("sortModel", []),
        )
        return {"rowData": rows, "rowCount": total}
