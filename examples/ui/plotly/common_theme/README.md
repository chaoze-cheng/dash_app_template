# UI-003 — Plotly Theme

- **Status:** experimental
- **Purpose:** A shared Plotly theme meeting the minimum 14px font rule.
- **Dependencies:** `plotly`.
- **Run:** `python example.py` (writes no file; prints a figure summary).
- **Integration:** Move `theme.py` into target `src/graphs/` or other approved graph utility.
- **Interface:** `apply_theme(fig)` mutates and returns a Plotly figure.
- **Limitations:** Colors are a generic starting point, not validated for all scientific plots or color-vision deficiencies.
- **Source/License:** Original scaffold; no third-party project code included.
- **Verification:** Not executed against a deployed Plotly environment.
