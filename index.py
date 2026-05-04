# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.23.3",
#     "numpy==2.4.4",
#     "pandas==3.0.2",
#     "requests==2.33.1",
#     "scikit-learn==1.8.0",
#     "svg.py==1.10.0",
# ]
# ///

import marimo

__generated_with = "0.23.3"
app = marimo.App(width="full", app_title="COOTEFOO Board Investigation")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import json
    import math
    import requests

    return json, math, mo, np, pd, requests


# ═══════════════════════════════════════════════════════════════════
# DATA LOADING — D1-D3 (pre-computed JSON)
# ═══════════════════════════════════════════════════════════════════


@app.cell
def _(mo, pd):
    def _load_json(name):
        try:
            return pd.read_json(str(mo.notebook_location() / "data" / name))
        except Exception:
            return pd.read_json(
                f"https://raw.githubusercontent.com/tvakul/dataviz1/refs/heads/main/data/{name}"
            )

    bias_persons = _load_json("bias_persons.json")
    nodes = _load_json("nodes.json")
    d3_df = _load_json("people_participation_summary.json")
    d3_totals = _load_json("people_participation_total.json")

    return bias_persons, d3_df, d3_totals, nodes


@app.cell
def _(json, mo, pd, requests):
    try:
        with open(mo.notebook_location() / "data" / "oceanus_map.geojson") as f:
            oceanus_geojson = json.load(f)
    except Exception:
        oceanus_geojson = requests.get(
            "https://raw.githubusercontent.com/tvakul/dataviz1/refs/heads/main/data/oceanus_map.geojson"
        ).json()

    def _load_json2(name, dtypes=None):
        try:
            return pd.read_json(str(mo.notebook_location() / "data" / name), dtype=dtypes)
        except Exception:
            return pd.read_json(
                f"https://raw.githubusercontent.com/tvakul/dataviz1/refs/heads/main/data/{name}",
                dtype=dtypes,
            )

    places_edited = _load_json2("places_edited.json")

    _dtypes_tts = {
        "trip_id": "object", "date": "object",
        "start_time": "datetime64[ns]", "end_time": "datetime64[ns]",
        "trip_id_1": "object", "place_id": "object",
        "time": "datetime64[ns]", "place_id_1": "object",
        "name": "object", "lat": "float64", "lon": "float64",
        "zone": "object", "zone_detail": "object", "people_id": "object",
        "index": "int64", "index_lead": "int64", "time_spend": "timedelta64[ns]",
    }
    time_trip_spend = _load_json2("time_trip_spend.json", _dtypes_tts)

    return oceanus_geojson, places_edited, time_trip_spend


# ═══════════════════════════════════════════════════════════════════
# DATA LOADING — D1 participation reasons (from CSV)
# ═══════════════════════════════════════════════════════════════════


@app.cell
def _(mo, pd):
    def _load_jr(filename):
        _path = f"data/Collected_by_the_Journalist/{filename}"
        try:
            return pd.read_csv(str(mo.notebook_location() / _path))
        except Exception:
            return pd.read_csv(
                f"https://raw.githubusercontent.com/tvakul/dataviz1/refs/heads/main/{_path}"
            )

    _jr = {
        t: _load_jr(f"{t}.csv")
        for t in [
            "discussion_people_participations",
            "plan_people_participations",
            "discussion_org_participations",
            "plan_org_participations",
            "discussion_topics",
            "plan_topics",
        ]
    }
    for _t in list(_jr.keys()):
        if "sentiment" in _jr[_t].columns:
            _jr[_t] = _jr[_t].copy()
            _jr[_t]["sentiment"] = pd.to_numeric(_jr[_t]["sentiment"], errors="coerce")

    participation_reasons = pd.concat(
        [
            _jr["discussion_people_participations"][
                ["discussion_id", "people_id", "sentiment", "reason"]
            ]
            .rename(columns={"discussion_id": "target_id", "people_id": "entity_id"})
            .assign(entity_type="person"),
            _jr["plan_people_participations"][
                ["plan_id", "people_id", "sentiment", "reason"]
            ]
            .rename(columns={"plan_id": "target_id", "people_id": "entity_id"})
            .assign(entity_type="person"),
            _jr["discussion_org_participations"][
                ["discussion_id", "organization_id", "sentiment", "reason"]
            ]
            .rename(
                columns={"discussion_id": "target_id", "organization_id": "entity_id"}
            )
            .assign(entity_type="org"),
            _jr["plan_org_participations"][
                ["plan_id", "organization_id", "sentiment", "reason"]
            ]
            .rename(columns={"plan_id": "target_id", "organization_id": "entity_id"})
            .assign(entity_type="org"),
        ],
        ignore_index=True,
    )
    participation_reasons = participation_reasons.merge(
        pd.concat(
            [
                _jr["discussion_topics"][["discussion_id", "topic_id"]].rename(
                    columns={"discussion_id": "target_id"}
                ),
                _jr["plan_topics"][["plan_id", "topic_id"]].rename(
                    columns={"plan_id": "target_id"}
                ),
            ],
            ignore_index=True,
        ).drop_duplicates(),
        on="target_id",
        how="left",
    )

    return (participation_reasons,)


# ═══════════════════════════════════════════════════════════════════
# D1 — BOARD SENTIMENT BIAS MAP
# ═══════════════════════════════════════════════════════════════════


@app.cell
def _(bias_persons, mo, nodes, participation_reasons):
    from _build_d1 import build_d1_html

    _html = build_d1_html(bias_persons, nodes, participation_reasons)
    visual1 = mo.vstack(
        [
            mo.md("### Board Sentiment Bias Map"),
            mo.md(
                '<span style="color:#8A7E74; font-size:12px;">'
                "Hover/click a person to see their topic connections and sentiment reasons. "
                "Red-glowing nodes = journalist-only data."
                "</span>"
            ),
            mo.iframe(_html, height="700px", width="1200px"),
        ],
        align="center",
    )
    return (visual1,)


# ═══════════════════════════════════════════════════════════════════
# D2 — BOARD VISIT MAP & TIME SPENT
# ═══════════════════════════════════════════════════════════════════


@app.cell
def _(mo, pd, time_trip_spend):
    _unique_dates = pd.to_datetime(time_trip_spend["date"]).sort_values().unique()
    _num_days = len(_unique_dates)

    d2_knn_dist = mo.ui.slider(
        start=0, stop=5, step=0.1, value=1, show_value=True
    )
    d2_knn_num = mo.ui.slider(
        start=0, stop=10, step=1, value=5, show_value=True
    )
    d2_mode = mo.ui.dropdown(options=["visits", "time_spend"], value="visits")
    d2_show_others = mo.ui.checkbox(value=False, label="Show 'Others'")
    d2_date_slider = mo.ui.range_slider(
        start=0,
        stop=_num_days - 1,
        step=1,
        value=(0, _num_days - 1),
        label="Date range",
    )
    d2_unique_dates = _unique_dates
    return (
        d2_date_slider,
        d2_knn_dist,
        d2_knn_num,
        d2_mode,
        d2_show_others,
        d2_unique_dates,
    )


@app.cell
def _(
    d2_date_slider,
    d2_knn_dist,
    d2_knn_num,
    d2_mode,
    d2_show_others,
    d2_unique_dates,
    mo,
    oceanus_geojson,
    places_edited,
    time_trip_spend,
):
    from _build_d2 import build_d2_html

    _sel_start = d2_unique_dates[int(d2_date_slider.value[0])]
    _sel_end = d2_unique_dates[int(d2_date_slider.value[1])]

    _html = build_d2_html(
        time_trip_spend,
        places_edited,
        oceanus_geojson,
        d2_knn_dist.value,
        d2_knn_num.value,
        d2_mode.value,
        d2_show_others.value,
        _sel_start,
        _sel_end,
    )

    visual2 = mo.vstack(
        [
            mo.md("### Board Visit Map and Time Spent"),
            mo.hstack(
                [
                    mo.iframe(_html, width=1020, height=820),
                    mo.vstack(
                        [
                            mo.hstack(
                                [mo.md("KNN distance (km)"), d2_knn_dist],
                                align="center",
                                justify="space-between",
                            ),
                            mo.hstack(
                                [mo.md("KNN neighbors"), d2_knn_num],
                                align="center",
                                justify="space-between",
                            ),
                            mo.hstack(
                                [mo.md("Mode"), d2_mode],
                                align="center",
                                justify="space-between",
                            ),
                            d2_show_others,
                            d2_date_slider,
                        ],
                        align="stretch",
                    ),
                ],
                justify="start",
                align="start",
            ),
        ],
        align="start",
    )
    return (visual2,)


# ═══════════════════════════════════════════════════════════════════
# D3 — TOPICS, MEETINGS, DISCUSSIONS & PLANS
# ═══════════════════════════════════════════════════════════════════


@app.cell
def _(d3_df, mo):
    d3_people_ui = mo.ui.dictionary(
        {
            p: mo.ui.checkbox(value=True, label=p)
            for p in sorted(d3_df["people_id"].dropna().unique())
        }
    )
    d3_focus_ui = mo.ui.dictionary(
        {
            f: mo.ui.checkbox(value=True, label=f)
            for f in sorted(d3_df["focus"].dropna().unique())
        }
    )
    return d3_focus_ui, d3_people_ui


@app.cell
def _(d3_df, d3_focus_ui, d3_people_ui, d3_totals, mo):
    from _build_d3 import build_d3_svg

    _selected_people = [p for p, a in d3_people_ui.value.items() if a]
    _selected_focuses = [f for f, a in d3_focus_ui.value.items() if a]
    _focus_colors = {
        "fishing": "#2ca02c",
        "tourism": "#d62728",
        "both": "#17becf",
        "other": "#7f7f7f",
    }

    _svg_str = build_d3_svg(
        d3_df, d3_totals, _selected_people, _selected_focuses, _focus_colors
    )

    visual3 = mo.vstack(
        [
            mo.md("### Topics, Meetings, Discussions and Plans"),
            mo.hstack(
                [
                    mo.Html(_svg_str),
                    mo.vstack(
                        [
                            mo.md("**People:**"),
                            d3_people_ui,
                            mo.md("**Focus:**"),
                            d3_focus_ui,
                        ]
                    ),
                ]
            ),
        ]
    )
    return (visual3,)


# ═══════════════════════════════════════════════════════════════════
# D4 — THE COMMITTEE (constellation + trip ribbon)
# ═══════════════════════════════════════════════════════════════════


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
    visual4 = mo.vstack(
        [
            mo.md("### The Committee, Charted"),
            mo.md(
                '<span style="color:#8A7E74; font-size:12px;">'
                "Sentiment constellation + trip ribbon. "
                "Hover a member or topic to see connections. "
                "Click to pin. Press Esc to clear."
                "</span>"
            ),
            mo.iframe(_html, width=1520, height=1300),
        ],
        align="center",
    )
    return (visual4,)


# ═══════════════════════════════════════════════════════════════════
# TABS — FINAL COMPOSITION
# ═══════════════════════════════════════════════════════════════════


@app.cell
def _(mo, visual1, visual2, visual3, visual4):
    mo.ui.tabs(
        {
            "Sentiment Map": visual1,
            "Visit Map": visual2,
            "Participation": visual3,
            "The Committee": visual4,
        }
    )
    return


if __name__ == "__main__":
    app.run()