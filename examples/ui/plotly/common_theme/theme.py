import plotly.graph_objects as go


def apply_theme(fig: go.Figure) -> go.Figure:
    """Apply consistent text sizes and basic chart styling."""
    fig.update_layout(
        font=dict(family="Arial, sans-serif", size=16, color="#0f172a"),
        title_font=dict(size=20),
        legend=dict(font=dict(size=14)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=20, t=60, b=55),
    )
    fig.update_xaxes(tickfont=dict(size=14), title_font=dict(size=16))
    fig.update_yaxes(tickfont=dict(size=14), title_font=dict(size=16))
    return fig
