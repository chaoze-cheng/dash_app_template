# UI-001 — Navbar

- **Status:** experimental
- **Purpose:** Reusable simple Dash navbar with CSS tokens.
- **Dependencies:** Dash (install `dash` in a virtual environment).
- **Run:** `python app.py` from this directory.
- **Integration:** Move `navbar.py` into target `src/components/`, copy CSS tokens into project assets; register no additional callbacks.
- **Interface:** `build_navbar(links)` where `links` is a list of `(label, href)` tuples.
- **Limitations:** Demonstration only; no authentication, responsive sidebar, or active-route highlighting.
- **Source/License:** Original scaffold written for this example; no third-party project code included.
- **Verification:** Not executed against a deployed Dash installation.
