# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.23.3",
#     "requests==2.33.1",
# ]
# ///

import marimo

__generated_with = "0.23.3"
app = marimo.App(width="full", app_title="The Committee, Charted")


@app.cell
def _():
    import marimo as mo
    import json
    import requests
    return json, mo, requests


@app.cell
def _(json, mo, requests):
    _path = "data/cleaned_data/data.js"
    try:
        with open(str(mo.notebook_location() / _path)) as _f:
            _raw = _f.read()
    except (FileNotFoundError, OSError):
        _raw = requests.get(
            f"https://raw.githubusercontent.com/tvakul/dataviz1/refs/heads/main/{_path}"
        ).text

    d4_data = json.loads(_raw.split("=", 1)[1].strip().rstrip(";"))
    return (d4_data,)


@app.cell
def _(d4_data, mo):
    from _build_d4 import build_d4_html

    _html = build_d4_html(d4_data)
    mo.iframe(_html, width=1520, height=1300)
    return


if __name__ == "__main__":
    app.run()
