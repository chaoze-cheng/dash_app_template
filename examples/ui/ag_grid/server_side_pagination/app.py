from dash import Dash, html
import dash_ag_grid as dag
from callbacks import register_table_callbacks

app = Dash(__name__)
server = app.server
app.layout = html.Div([
    html.H2("AG Grid Pagination Example"),
    dag.AgGrid(
        id="example-grid",
        columnDefs=[{"field": "id"}, {"field": "name"}, {"field": "score"}],
        rowModelType="infinite",
        dashGridOptions={"cacheBlockSize": 50, "pagination": True, "paginationPageSize": 50},
        columnSize="sizeToFit",
        style={"height": "480px", "width": "100%"},
    ),
])
register_table_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)
