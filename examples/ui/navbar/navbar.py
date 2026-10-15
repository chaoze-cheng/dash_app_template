from dash import html


def build_navbar(links: list[tuple[str, str]]) -> html.Nav:
    """Create a simple navigation bar."""
    return html.Nav(
        [html.A(label, href=href, className="example-nav-link") for label, href in links],
        className="example-navbar",
        **{"aria-label": "Main navigation"},
    )
