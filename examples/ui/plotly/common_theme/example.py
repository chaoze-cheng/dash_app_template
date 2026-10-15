import plotly.graph_objects as go
from theme import apply_theme

figure = apply_theme(go.Figure(data=[go.Bar(x=["A", "B"], y=[3, 5])]))
figure.update_layout(title="Example Chart")
print(figure.to_dict()["layout"]["font"])
