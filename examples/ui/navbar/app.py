from dash import Dash, html
from navbar import build_navbar

app = Dash(__name__)
server = app.server
app.layout = html.Div([build_navbar([("Home", "/"), ("Docs", "/docs")]), html.Main("Demo content")])

if __name__ == "__main__":
    app.run(debug=True)
