"""
Builder module for Dashboard 2 – Board Visit Map and Time Spent.

Pure Python functions (no marimo dependency).  Call build_d2_html() to get a
complete HTML string suitable for mo.iframe().
"""

import json
import math

import numpy as np
import pandas as pd
import svg
from sklearn.neighbors import BallTree


# ---------------------------------------------------------------------------
# 1.  KNN zone classifier
# ---------------------------------------------------------------------------

def classify_weighted_knn(df, k=5, max_radius_km=1.0, epsilon=0.001):
    """Reclassify commercial/residential places using inverse-distance-weighted
    KNN against nearby tourism/industrial places."""

    df_comm = df[df["zone"].isin(["commercial", "residential"])].reset_index(drop=True)
    df_targets = df[df["zone"].isin(["tourism", "industrial"])].reset_index(drop=True)

    if df_comm.empty or df_targets.empty:
        return pd.DataFrame()

    comm_rad = np.radians(df_comm[["lat", "lon"]])
    target_rad = np.radians(df_targets[["lat", "lon"]])
    tree = BallTree(target_rad, metric="haversine")

    earth_radius_km = 6371.0
    radius_rad = max_radius_km / earth_radius_km
    distances, indices = tree.query(comm_rad, k=k, return_distance=True)

    results = []
    for i, (dist_array, idx_array) in enumerate(zip(distances, indices)):
        for dist, idx in zip(dist_array, idx_array):
            if dist <= radius_rad:
                dist_km = dist * earth_radius_km
                weight = 1.0 / (dist_km + epsilon)
                results.append(
                    {
                        "commercial_id": df_comm.iloc[i]["place_id"],
                        "target_zone": df_targets.iloc[idx]["zone"],
                        "weight": weight,
                    }
                )

    df_neighbors = pd.DataFrame(results)
    if df_neighbors.empty:
        return pd.DataFrame(columns=["commercial_id", "predicted_zone", "weighted_score"])

    weighted_scores = (
        df_neighbors.groupby(["commercial_id", "target_zone"])["weight"]
        .sum()
        .reset_index(name="weighted_score")
    )

    df_majority = (
        weighted_scores.sort_values(
            ["commercial_id", "weighted_score"], ascending=[True, False]
        )
        .drop_duplicates(subset=["commercial_id"], keep="first")
        .rename(columns={"target_zone": "predicted_zone"})
    )

    return df_majority.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 2.  SVG helper classes / drawing functions
# ---------------------------------------------------------------------------

def _slug(name):
    return str(name).replace(" ", "_")


class DataCircle(svg.Circle):
    def __init__(self, **kwargs):
        data_info = kwargs.pop("data_info", None)
        if data_info:
            kwargs["data"] = {"info": data_info}
        super().__init__(**kwargs)


class DataPath(svg.Path):
    def __init__(self, **kwargs):
        data_info = kwargs.pop("data_info", None)
        if data_info:
            kwargs["data"] = {"info": data_info}
        super().__init__(**kwargs)


class DataPolygon(svg.Polygon):
    def __init__(self, **kwargs):
        data_info = kwargs.pop("data_info", None)
        if data_info:
            kwargs["data"] = {"info": data_info}
        super().__init__(**kwargs)


class DataG(svg.G):
    def __init__(self, **kwargs):
        data_info = kwargs.pop("data_info", None)
        if data_info:
            kwargs["data"] = {"info": data_info}
        super().__init__(**kwargs)


def draw_rowboat(x, y, scale=0.5, color="#cf9154", name=""):
    attrs = {
        "class_": "member-node",
        "transform": f"translate({x}, {y}) scale({scale})",
        "style": "cursor:pointer",
    }
    if name:
        attrs["id"] = f"boat_{_slug(name)}"
    elements = [
        svg.Path(
            d="M -42 0 C -28 18 28 18 42 0 L 34 0 C 24 9 -24 9 -34 0 Z",
            fill="url(#c5-rowboat-wood)",
            stroke="#51341a",
            stroke_width=1.4,
        ),
        svg.Path(
            d="M -28 2 L 28 2",
            stroke="#efdcb8",
            stroke_width=2.6,
            stroke_linecap="round",
        ),
        svg.Path(
            d="M -14 7 L 18 7",
            stroke="#b98b59",
            stroke_width=1.8,
            stroke_linecap="round",
        ),
        svg.Line(
            x1=4, y1=3, x2=36, y2=-10,
            stroke="#7a5335", stroke_width=2, stroke_linecap="round",
        ),
        svg.Path(
            d="M -52 15 Q -16 23 18 18 Q 45 16 57 17",
            fill="none", stroke="#deefff", stroke_width=3,
            stroke_linecap="round", opacity=0.9,
        ),
    ]
    if name:
        elements.append(
            svg.Text(x=30, y=30, text=name, text_anchor="middle",
                      font_size=12, fill="#333", font_weight="bold")
        )
    return svg.G(**attrs, elements=elements)


def draw_person(x, y, scale=0.8, color="#2c3e50", name=""):
    attrs = {
        "class_": "member-node",
        "transform": f"translate({x}, {y}) scale({scale})",
        "style": "cursor:pointer",
    }
    if name:
        attrs["id"] = f"person_{_slug(name)}"
    elements = [
        svg.Ellipse(cx=0, cy=5, rx=14, ry=4, fill="#2f3d48", opacity=0.18),
        svg.Circle(cx=0, cy=-40, r=9, fill="#d1a07c", stroke="#805b48", stroke_width=0.8),
        svg.Path(
            d="M -5 -48 C -2 -53 5 -54 7 -47",
            fill="none", stroke="#45332a", stroke_width=2, stroke_linecap="round",
        ),
        svg.Path(
            d="M -14 -28 Q 0 -38 14 -28 L 10 -4 L -10 -4 Z",
            fill=color, stroke="#2e3d48", stroke_width=0.9,
        ),
        svg.Line(x1=-9, y1=-24, x2=-17, y2=-13, stroke="#d1a07c", stroke_width=2.8, stroke_linecap="round"),
        svg.Line(x1=9, y1=-24, x2=17, y2=-13, stroke="#d1a07c", stroke_width=2.8, stroke_linecap="round"),
        svg.Line(x1=-4, y1=-4, x2=-8, y2=8, stroke="#415365", stroke_width=3, stroke_linecap="round"),
        svg.Line(x1=4, y1=-4, x2=8, y2=8, stroke="#415365", stroke_width=3, stroke_linecap="round"),
        svg.Line(x1=-8, y1=8, x2=-14, y2=8, stroke="#2a2f34", stroke_width=3, stroke_linecap="round"),
        svg.Line(x1=8, y1=8, x2=14, y2=8, stroke="#2a2f34", stroke_width=3, stroke_linecap="round"),
    ]
    if name:
        elements.append(
            svg.Text(x=0, y=25, text=name, text_anchor="middle",
                      font_size=12, fill="#333", font_weight="bold")
        )
    return svg.G(**attrs, elements=elements)


def draw_umbrella(x, y, scale=1.0, color="#efb56f", name=""):
    attrs = {
        "class_": "member-node",
        "transform": f"translate({x}, {y}) scale({scale})",
        "style": "cursor:pointer",
    }
    if name:
        attrs["id"] = f"beach_{_slug(name)}"
    elements = [
        svg.Line(x1=0, y1=0, x2=0, y2=-58, stroke="#72563d", stroke_width=2.2, stroke_linecap="round"),
        svg.Path(
            d="M -36 -31 Q -20 -58 0 -60 Q 20 -58 36 -31 Z",
            fill="url(#c5-umbrella)", stroke="#a14e44", stroke_width=1.4,
        ),
        svg.Line(x1=-18, y1=-32, x2=-9, y2=-56, stroke="#f7e1b2", stroke_width=1.3),
        svg.Line(x1=0, y1=-31, x2=0, y2=-59, stroke="#f7e1b2", stroke_width=1.3),
        svg.Line(x1=18, y1=-32, x2=9, y2=-56, stroke="#f7e1b2", stroke_width=1.3),
        svg.Path(
            d="M -22 9 Q 0 15 22 9",
            fill="none", stroke=color, stroke_width=2,
            stroke_linecap="round", opacity=0.55,
        ),
    ]
    if name:
        elements.append(
            svg.Text(x=0, y=20, text=name, text_anchor="middle",
                      font_size=12, fill="#333", font_weight="bold")
        )
    return svg.G(**attrs, elements=elements)


# ---------------------------------------------------------------------------
# 3.  Main builder
# ---------------------------------------------------------------------------

def build_d2_html(
    time_trip_spend,
    places_edited,
    oceanus_geojson,
    knn_dist,
    knn_num,
    mode,
    show_others,
    sel_start,
    sel_end,
):
    """Return a complete HTML string (SVG + CSS + JS) for D2.

    Parameters
    ----------
    time_trip_spend : DataFrame
        Columns: trip_id, date, start_time, end_time, place_id, name, lat, lon,
        zone, zone_detail, people_id, time_spend.
    places_edited : DataFrame
        Columns: place_id, zone, lat, lon.
    oceanus_geojson : dict
        GeoJSON feature collection for the Oceanus map.
    knn_dist : float
        KNN max radius in km.
    knn_num : int
        KNN k neighbours.
    mode : str
        ``"visits"`` or ``"time_spend"``.
    show_others : bool
        Whether to render the *other* category.
    sel_start, sel_end : Timestamp
        Date-range boundaries.
    """

    # ------------------------------------------------------------------
    # A.  Remap zones via KNN
    # ------------------------------------------------------------------
    remapped_location = pd.concat(
        [
            places_edited.loc[places_edited["zone"].isin(["industrial", "tourism"])],
            classify_weighted_knn(
                places_edited, max_radius_km=knn_dist, k=knn_num
            ).rename(columns={"predicted_zone": "zone", "commercial_id": "place_id"}),
        ],
        ignore_index=True,
    ).drop_duplicates(subset=["place_id"], keep="first")[["place_id", "zone"]]

    # ------------------------------------------------------------------
    # B.  Filter trips by date range
    # ------------------------------------------------------------------
    _col = pd.to_datetime(time_trip_spend["date"])
    _mask = (_col >= sel_start) & (_col <= sel_end)
    filtered_tts = time_trip_spend[_mask]

    time_location_remapped = pd.merge(
        filtered_tts[
            ["trip_id", "date", "people_id", "place_id", "name",
             "time_spend", "zone", "lat", "lon"]
        ].copy(),
        remapped_location.rename(columns={"zone": "zone_remapped"}),
        on="place_id",
        how="left",
    ).fillna({"zone_remapped": "other"})

    # Add 'time' column alias if missing (used downstream as sort key)
    if "time" not in time_location_remapped.columns:
        time_location_remapped["time"] = time_location_remapped.get(
            "start_time", pd.NaT
        )

    # ------------------------------------------------------------------
    # C.  Compute zone summaries
    # ------------------------------------------------------------------
    # C-1  Visit-count delta
    _tmp = time_location_remapped.copy()
    _tmp["visit_id"] = (
        _tmp["trip_id"].astype(str) + "_"
        + _tmp["place_id"].astype(str) + "_"
        + _tmp["place_id"].astype(str)
    )
    people_zone_summary = (
        _tmp.groupby(["people_id", "zone_remapped"])
        .agg(total_visits=("visit_id", "nunique"))
        .reset_index()
    )
    people_zone_summary = people_zone_summary[
        people_zone_summary["zone_remapped"].isin(["industrial", "tourism"])
    ]
    people_zone_summary_delta = (
        people_zone_summary.pivot(
            index="people_id", columns="zone_remapped", values="total_visits"
        )
        .fillna(0)
        .reset_index()
    )
    if "industrial" not in people_zone_summary_delta.columns:
        people_zone_summary_delta["industrial"] = 0
    if "tourism" not in people_zone_summary_delta.columns:
        people_zone_summary_delta["tourism"] = 0
    people_zone_summary_delta["delta"] = (
        people_zone_summary_delta["industrial"] - people_zone_summary_delta["tourism"]
    )

    # C-2  Time-spend delta
    people_timespend_summary = (
        time_location_remapped.groupby(["people_id", "zone_remapped"])
        .agg({"time_spend": "sum", "trip_id": "nunique"})
        .reset_index()
    )
    people_timespend_summary_filtered = people_timespend_summary[
        people_timespend_summary["zone_remapped"].isin(["industrial", "tourism"])
    ].copy()
    delta_time_spend = (
        people_timespend_summary_filtered.pivot(
            index="people_id", columns="zone_remapped", values="time_spend"
        )
        .fillna(pd.Timedelta(0))
    )
    if "industrial" not in delta_time_spend.columns:
        delta_time_spend["industrial"] = pd.Timedelta(0)
    if "tourism" not in delta_time_spend.columns:
        delta_time_spend["tourism"] = pd.Timedelta(0)
    delta_time_spend["delta"] = (
        delta_time_spend.get("industrial", pd.Timedelta(0))
        - delta_time_spend.get("tourism", pd.Timedelta(0))
    )

    # C-3  Choose data for graphs based on mode
    if mode == "visits":
        graph_2_1_data = people_zone_summary_delta
        graph_2_2_data = (
            time_location_remapped.groupby(
                ["people_id", "date", "zone_remapped", "trip_id", "place_id"]
            )
            .size()
            .reset_index(name="num_visits")
        )
        graph_2_2_data["time_spend"] = 0
    else:
        graph_2_1_data = delta_time_spend.reset_index()
        temp_df = time_location_remapped.copy()
        if temp_df["time_spend"].dtype == "timedelta64[ns]":
            temp_df["time_hr"] = temp_df["time_spend"].dt.total_seconds() / 3600
        else:
            temp_df["time_hr"] = temp_df["time_spend"]
        graph_2_2_data = (
            temp_df.groupby(
                ["people_id", "date", "zone_remapped", "trip_id", "place_id"]
            )["time_hr"]
            .sum()
            .reset_index(name="time_spend")
        )
        graph_2_2_data["num_visits"] = 1

    # ------------------------------------------------------------------
    # D.  Build the SVG
    # ------------------------------------------------------------------

    def format_duration(hours):
        h = float(hours)
        days = int(h // 24)
        rem_h = h % 24
        mins = int((rem_h * 60) % 60)
        hh = int(rem_h)
        time_str = f"{hh:02d} hr :{mins:02d} mi"
        if days == 0:
            return time_str
        elif days == 1:
            return f"1 day, {time_str}"
        else:
            return f"{days} days, {time_str}"

    def fmt(v):
        return f"{v:.0f}" if mode == "visits" else format_duration(v)

    def clamp(v, lo, hi):
        return max(lo, min(hi, v))

    name_map = {"industrial": "fishing", "tourism": "tourism", "other": "other"}
    focus_colors = {"fishing": "#6c9474", "tourism": "#d48a57", "other": "#9ea8b1"}
    map_colors = {"fishing": "#6c9474", "tourism": "#d48a57", "other": "#9ea8b1"}
    map_strokes = {"fishing": "#4f7256", "tourism": "#b76e42", "other": "#7f8992"}

    W, H = 1000, 800
    els = [
        """
        <defs>
          <linearGradient id="c5-water" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#79addc"/>
            <stop offset="100%" stop-color="#4579a6"/>
          </linearGradient>
          <linearGradient id="c5-sand" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#dcc89d"/>
            <stop offset="100%" stop-color="#ceb27b"/>
          </linearGradient>
          <linearGradient id="c5-boat-hull" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#fafdff"/>
            <stop offset="56%" stop-color="#edf4f9"/>
            <stop offset="57%" stop-color="#213d55"/>
            <stop offset="100%" stop-color="#102b40"/>
          </linearGradient>
          <linearGradient id="c5-rowboat-wood" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#8d5d33"/>
            <stop offset="100%" stop-color="#63401f"/>
          </linearGradient>
          <linearGradient id="c5-umbrella" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#ea6f5d"/>
            <stop offset="50%" stop-color="#df5d52"/>
            <stop offset="100%" stop-color="#ee8a68"/>
          </linearGradient>
          <filter id="c5-shadow" x="-20%" y="-20%" width="160%" height="160%">
            <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#274055" flood-opacity="0.16"/>
          </filter>
        </defs>
        <style>
          .c5-code { font-family: Segoe UI, Tahoma, sans-serif; font-size: 15px; font-weight: 700; fill: #4a5b68; }
          .c5-title { font-family: Segoe UI, Tahoma, sans-serif; font-size: 16px; font-weight: 700; fill: #283844; }
          .c5-note { font-family: Segoe UI, Tahoma, sans-serif; font-size: 11px; fill: #738596; }
          .c5-side-note { font-family: Segoe UI, Tahoma, sans-serif; font-size: 11px; font-weight: 700; fill: #6d7e8c; }
          .c5-member-label { font-family: Segoe UI, Tahoma, sans-serif; font-size: 11px; font-weight: 700; fill: #806446; }
          .c5-axis-left { font-family: Segoe UI, Tahoma, sans-serif; font-size: 11px; font-weight: 700; fill: #2980b9; }
          .c5-axis-right { font-family: Segoe UI, Tahoma, sans-serif; font-size: 11px; font-weight: 700; fill: #cca300; }
          .c5-axis-mid { font-family: Segoe UI, Tahoma, sans-serif; font-size: 10px; font-weight: 700; fill: #728391; }
          .c6-note { font-family: Segoe UI, Tahoma, sans-serif; font-size: 11px; fill: #738596; }
          .c6-legend { font-family: Segoe UI, Tahoma, sans-serif; font-size: 10px; fill: #667786; }
          .c6-city { font-family: Segoe UI, Tahoma, sans-serif; font-size: 9px; fill: #7e8d99; }
          .c6-zoom-text { font-family: Segoe UI, Tahoma, sans-serif; font-size: 11px; font-weight: 700; fill: #44535f; }
          .c7-note { font-family: Segoe UI, Tahoma, sans-serif; font-size: 11px; fill: #738596; }
          .c7-legend { font-family: Segoe UI, Tahoma, sans-serif; font-size: 11px; fill: #5f6f7c; }
        </style>
        """,
    ]

    # Dynamic titles
    if mode == "visits":
        title_c5 = "Visit bias"
        title_c6 = "Visit map"
        title_c7 = "Trip visit split"
    else:
        title_c5 = "Time spend bias"
        title_c6 = "Time spend map"
        title_c7 = "Trip time split"

    # =================================================================
    # C5  –  Shoreline bias
    # =================================================================
    c5_x, c5_y, c5_w, c5_h = 40, 20, 920, 250
    els.append(
        svg.Rect(x=c5_x, y=c5_y, width=c5_w, height=c5_h,
                  fill="#f8fbfd", stroke="#ccd8e2", stroke_width=1.2, rx=10)
    )
    els.append(
        svg.Text(x=c5_x + 16, y=c5_y + 23,
                  text="Visit bias" if mode == "visits" else "Time spent bias",
                  class_="c5-title")
    )
    els.append(
        svg.Text(
            x=c5_x + c5_w - 16, y=c5_y + 23,
            text="balance from visits" if mode == "visits" else "balance from time spend",
            text_anchor="end", class_="c5-note",
        )
    )

    data_c5 = graph_2_1_data.copy()
    pos_col = "delta"
    if mode == "time_spend":
        data_c5["delta_val"] = data_c5["delta"].apply(
            lambda x: x.total_seconds() / 3600 if hasattr(x, "total_seconds") else x
        )
        pos_col = "delta_val"
    data_c5 = data_c5.sort_values(pos_col).reset_index(drop=True)

    min_d = min(0, data_c5[pos_col].min()) - 3
    max_d = max(0, data_c5[pos_col].max()) + 3
    range_d = max_d - min_d or 1
    scene_x = c5_x + 18
    scene_w = c5_w - 36
    scene_top = c5_y + 31
    scene_h = 215
    scene_bottom = scene_top + scene_h
    sea_level = scene_top + 61
    sand_line_y = scene_top + 166
    border_x = scene_x + scene_w - ((0 - min_d) / range_d) * scene_w

    members = []
    for _, row in data_c5.iterrows():
        val = row[pos_col]
        x = scene_x + scene_w - ((val - min_d) / range_d) * scene_w
        members.append(
            {"people_id": row["people_id"],
             "x": clamp(x, scene_x + 118, scene_x + scene_w - 102),
             "val": val}
        )

    water_members = [m for m in members if m["x"] < border_x]
    shore_members = [m for m in members if m["x"] >= border_x]

    water_groups = []
    for member in water_members:
        if not water_groups:
            water_groups.append([member])
            continue
        prev = water_groups[-1]
        if len(prev) < 2 and member["x"] - prev[-1]["x"] <= 72:
            prev.append(member)
        else:
            water_groups.append([member])

    min_boat_gap = 136
    left_boat_limit = scene_x + 96
    shore_start_x = border_x
    shore_end_x = border_x

    els.append(
        svg.Rect(x=scene_x, y=scene_top, width=scene_w, height=scene_h,
                  fill="#ffffff", stroke="#d7e2ea", stroke_width=1, rx=8)
    )
    els.append(
        svg.Rect(x=scene_x + 1, y=scene_top + 1, width=scene_w - 2,
                  height=49, fill="#dbeaf8", rx=8)
    )
    els.append(
        svg.Path(d=(
            f"M {scene_x + 14} {sea_level} "
            f"L {shore_start_x} {sea_level} "
            f"L {shore_end_x} {sand_line_y} "
            f"L {scene_x + 14} {sand_line_y} Z"
        ), fill="url(#c5-water)")
    )
    els.append(
        svg.Path(d=(
            f"M {shore_start_x} {sea_level} "
            f"L {scene_x + scene_w - 14} {sea_level} "
            f"L {scene_x + scene_w - 14} {sand_line_y} "
            f"L {shore_end_x} {sand_line_y} Z"
        ), fill="url(#c5-sand)")
    )
    els.append(
        svg.Line(x1=border_x, y1=scene_top + 26, x2=border_x, y2=sand_line_y,
                  stroke="#a9b6bf", stroke_width=1, stroke_dasharray="4")
    )
    els.append(
        svg.Text(x=border_x, y=scene_top + 18, text="neutral",
                  text_anchor="middle", class_="c5-axis-mid")
    )
    els.append(
        svg.Circle(cx=scene_x + scene_w - 74, cy=scene_top + 43, r=27,
                    fill="#efd695", opacity=0.9)
    )

    right_boat_limit = shore_start_x - 62
    adjusted_centers = []
    for group in water_groups:
        center = sum(item["x"] for item in group) / len(group)
        if adjusted_centers:
            center = max(center, adjusted_centers[-1] + min_boat_gap)
        else:
            center = max(center, left_boat_limit)
        adjusted_centers.append(center)
    if adjusted_centers:
        overflow = adjusted_centers[-1] - right_boat_limit
        if overflow > 0:
            adjusted_centers = [c - overflow for c in adjusted_centers]
        if adjusted_centers[0] < left_boat_limit:
            shift = left_boat_limit - adjusted_centers[0]
            adjusted_centers = [c + shift for c in adjusted_centers]

    label_levels = [scene_top + 16, scene_top + 31, scene_top + 10]
    boat_rows = [sea_level + 39, sea_level + 22, sea_level + 52]
    seat_offsets = {1: [0], 2: [-14, 14]}

    for group_idx, group in enumerate(water_groups):
        group_center = adjusted_centers[group_idx]
        boat_y = boat_rows[group_idx % len(boat_rows)]
        els.append(draw_rowboat(group_center, boat_y, 0.9, name=""))
        offsets = seat_offsets[len(group)]
        for member_idx, member in enumerate(group):
            px = group_center + offsets[member_idx]
            label_y = label_levels[(group_idx + member_idx) % len(label_levels)]
            label_x = clamp(
                px + (-18 if len(group) == 2 and member_idx == 0
                      else 18 if len(group) == 2 else 0),
                scene_x + 44, border_x - 18,
            )
            els.append(
                svg.Line(
                    x1=label_x, y1=label_y + 5, x2=px, y2=boat_y - 16,
                    stroke="#9eaab3", stroke_dasharray="4", stroke_width=1,
                )
            )
            els.append(
                svg.G(
                    class_=f"clickable-person pid-{member['people_id'].replace(' ', '_')}",
                    style="cursor:pointer",
                    elements=[
                        svg.Title(text=f"Delta: {member['val']:.2f}"),
                        svg.Circle(cx=px, cy=boat_y - 18, r=24, fill="#ffffff", opacity=0.01),
                        draw_person(px, boat_y - 1, 0.44, color="#d4944d", name=""),
                        svg.Text(x=label_x, y=label_y, text=member["people_id"],
                                  text_anchor="middle", class_="c5-member-label"),
                    ],
                )
            )

    if shore_members:
        shore_groups = []
        for member in shore_members:
            if not shore_groups:
                shore_groups.append([member])
                continue
            prev = shore_groups[-1]
            if abs(member["val"] - prev[-1]["val"]) < 1e-6:
                prev.append(member)
            else:
                shore_groups.append([member])

        group_centers = []
        for group in shore_groups:
            cx_ = sum(m["x"] for m in group) / len(group)
            cx_ = clamp(cx_, shore_start_x + 24, scene_x + scene_w - 40)
            group_centers.append(cx_)

        for i in range(1, len(group_centers)):
            group_centers[i] = min(group_centers[i], group_centers[i - 1] - 80)

        if group_centers and group_centers[-1] < shore_start_x + 24:
            group_centers[-1] = shore_start_x + 24
            for i in range(len(group_centers) - 2, -1, -1):
                group_centers[i] = max(group_centers[i], group_centers[i + 1] + 80)

        for g_idx, group in enumerate(shore_groups):
            px = group_centers[g_idx]
            for m_idx, member in enumerate(group):
                member_y = sand_line_y - 1 - m_idx * 58
                label_y = member_y - 32
                els.append(
                    svg.G(
                        class_=f"clickable-person pid-{member['people_id'].replace(' ', '_')}",
                        style="cursor:pointer",
                        elements=[
                            svg.Title(text=f"Delta: {member['val']:.2f}"),
                            svg.Circle(cx=px, cy=member_y - 15, r=24, fill="#ffffff", opacity=0.01),
                            draw_person(px, member_y, 0.52, color="#d4944d", name=""),
                            svg.Text(x=px, y=label_y, text=member["people_id"],
                                      text_anchor="middle", class_="c5-member-label"),
                        ],
                    )
                )

    # Axis
    ax_y = c5_y + c5_h - 30
    els.append(
        svg.Line(x1=scene_x + 14, y1=ax_y, x2=scene_x + scene_w - 14, y2=ax_y,
                  stroke="#c2ced8", stroke_width=1.2)
    )
    for tick_x in [scene_x + 14, border_x, scene_x + scene_w - 14]:
        els.append(
            svg.Line(x1=tick_x, y1=ax_y - 4, x2=tick_x, y2=ax_y + 4,
                      stroke="#aebbc5", stroke_width=1)
        )
    els.append(
        svg.Text(x=scene_x + 14, y=ax_y - 8, text="more fishing",
                  text_anchor="start", class_="c5-axis-left")
    )
    els.append(
        svg.Text(x=scene_x + scene_w - 14, y=ax_y - 8, text="more tourism",
                  text_anchor="end", class_="c5-axis-right")
    )
    els.append(
        svg.Text(
            x=scene_x + 14, y=ax_y + 16,
            text=(
                "left = more fishing visits, right = more tourism visits; click a member to update the other panels"
                if mode == "visits"
                else "left = more fishing time, right = more tourism time; click a member to update the other panels"
            ),
            text_anchor="start", class_="c5-note",
        )
    )

    # =================================================================
    # C6  –  Geographic map
    # =================================================================
    c6_x, c6_y, c6_w, c6_h = 40, 300, 440, 480
    els.append(
        svg.Rect(x=c6_x, y=c6_y, width=c6_w, height=c6_h,
                  fill="#fbfdff", stroke="#d5dee7", rx=10)
    )
    els.append(
        svg.Text(x=c6_x + 20, y=c6_y + 30, text=title_c6,
                  font_size=18, font_weight="bold", fill="#2c3e50")
    )
    els.append(
        svg.Text(
            x=c6_x + 20, y=c6_y + 46,
            text="size = repeated activity, color = remapped place type, wheel = zoom",
            class_="c6-note",
        )
    )

    map_x, map_y = c6_x + 18, c6_y + 58
    map_w, map_h = c6_w - 36, c6_h - 138
    map_inner_x, map_inner_y = map_x + 12, map_y + 12
    map_inner_w, map_inner_h = map_w - 24, map_h - 24
    legend_y = c6_y + c6_h - 56

    els.append(
        svg.Rect(
            id="c6-map-bg", x=map_x, y=map_y, width=map_w, height=map_h,
            fill="#dfeefa", stroke="#d4e0ea", stroke_width=1, rx=8,
            style="cursor:grab",
        )
    )
    els.append(
        f'<defs><clipPath id="c6-map-clip"><rect x="{map_x}" y="{map_y}" '
        f'width="{map_w}" height="{map_h}" rx="8"/></clipPath></defs>'
    )
    c6_zoom = svg.G(id="c6-map-zoom", elements=[])
    c6_shell = svg.G(id="c6-map-shell", clip_path="url(#c6-map-clip)",
                      elements=[c6_zoom])

    for row_y in [map_y + 86, map_y + 172, map_y + 258]:
        els.append(
            svg.Line(x1=map_x + 8, y1=row_y, x2=map_x + map_w - 8, y2=row_y,
                      stroke="#eef4f8", stroke_width=1)
        )

    def project(lon_val, lat_val):
        x_min, x_max = -166.3, -164.2
        y_min, y_max = 38.7, 39.9
        x_pct = (lon_val - x_min) / (x_max - x_min)
        y_pct = (lat_val - y_min) / (y_max - y_min)
        px = map_inner_x + x_pct * map_inner_w
        py = map_inner_y + map_inner_h - y_pct * map_inner_h
        return px, py

    def spread_map_points(df, value_col, grid_size=18):
        if df.empty:
            return df.copy()
        spread_df = df.copy()
        coords = spread_df.apply(
            lambda r: project(r["lat"], r["lon"]), axis=1, result_type="expand"
        )
        spread_df["map_px"] = coords[0]
        spread_df["map_py"] = coords[1]
        spread_df["disp_px"] = spread_df["map_px"]
        spread_df["disp_py"] = spread_df["map_py"]
        spread_df["cluster_x"] = (spread_df["map_px"] / grid_size).round().astype(int)
        spread_df["cluster_y"] = (spread_df["map_py"] / grid_size).round().astype(int)
        for _, cluster in spread_df.groupby(["cluster_x", "cluster_y"], sort=False):
            ordered = (
                cluster.sort_values([value_col, "place_id"], ascending=[False, True])
                .index.tolist()
            )
            n = len(ordered)
            if n <= 1:
                continue
            radius = min(24, 7 + n * 2.2)
            for pos, idx in enumerate(ordered):
                angle = -math.pi / 2 + (2 * math.pi * pos / n)
                spread_df.at[idx, "disp_px"] = (
                    spread_df.at[idx, "map_px"] + radius * math.cos(angle)
                )
                spread_df.at[idx, "disp_py"] = (
                    spread_df.at[idx, "map_py"] + radius * math.sin(angle)
                )
        return spread_df.drop(columns=["cluster_x", "cluster_y"])

    # GeoJSON islands / cities
    if oceanus_geojson:
        for feat in oceanus_geojson["features"]:
            geometry_type = feat["geometry"]["type"]
            kind = feat["properties"].get("Kind")
            name = feat["properties"].get("Name", "")
            if (geometry_type == "Polygon" and kind == "Island"
                    and name in ["Suna Island", "Thalassa Retreat"]):
                for poly in feat["geometry"]["coordinates"]:
                    pts = " ".join(
                        f"{project(c[0], c[1])[0]},{project(c[0], c[1])[1]}"
                        for c in poly
                    )
                    c6_zoom.elements.append(
                        svg.Polygon(
                            points=pts, fill="#eadfc2", stroke="#bfae81",
                            stroke_width=0.9, opacity=0.82,
                        )
                    )
            elif geometry_type == "Point" and kind == "city":
                px, py = project(*feat["geometry"]["coordinates"])
                label = name if len(name) <= 11 else name[:10] + "..."
                c6_zoom.elements.append(
                    svg.Circle(cx=px, cy=py, r=2.6, fill="#f8fbfe",
                                stroke="#90a2b2", stroke_width=1)
                )
                c6_zoom.elements.append(
                    svg.Text(x=px + 5, y=py - 5, text=label, class_="c6-city")
                )

    # Place names lookup
    place_names = {}
    if "name" in places_edited.columns:
        place_names = places_edited.set_index("place_id")["name"].to_dict()

    # Per-member visit dots
    visit_summary = (
        graph_2_2_data.groupby(["people_id", "place_id", "zone_remapped"])
        .agg({"time_spend": "sum", "num_visits": "sum"})
        .reset_index()
    )
    visit_summary = visit_summary.merge(
        places_edited[["place_id", "lat", "lon"]], on="place_id", how="left"
    )
    mode_col = "num_visits" if mode == "visits" else "time_spend"
    visit_summary["val"] = visit_summary[mode_col]
    max_v = visit_summary["val"].max() or 1
    visit_summary["m_zone"] = visit_summary["zone_remapped"].map(name_map).fillna("other")
    visit_summary = visit_summary.dropna(subset=["lat", "lon"])
    if not show_others:
        visit_summary = visit_summary[visit_summary["m_zone"] != "other"]
    visit_summary = spread_map_points(visit_summary, "val")

    for _, row in visit_summary.iterrows():
        m_zone = row["m_zone"]
        px, py = row["disp_px"], row["disp_py"]
        base_px, base_py = row["map_px"], row["map_py"]
        r = (row["val"] / max_v) ** 0.5 * 11 + 3
        pid_safe = row["people_id"].replace(" ", "_")
        loc_name = place_names.get(row["place_id"], str(row["place_id"]))
        info = (
            f"Member Activity | Member: {row['people_id']} | Location: {loc_name} | "
            f"Focus: {m_zone.capitalize()} | Value: {fmt(row['val'])}"
        )
        halo_class = f"visit_{pid_safe} map-dot"
        if abs(px - base_px) > 0.5 or abs(py - base_py) > 0.5:
            c6_zoom.elements.append(
                svg.Line(
                    x1=base_px, y1=base_py, x2=px, y2=py,
                    stroke="#b5c0c9", stroke_width=1,
                    class_=halo_class, style="display:none",
                )
            )
        c6_zoom.elements.append(
            svg.Circle(
                cx=px, cy=py, r=r + 2.4, fill="#ffffff", opacity=0.78,
                class_=halo_class, style="display:none",
            )
        )
        c6_zoom.elements.append(
            DataCircle(
                cx=px, cy=py, r=r,
                fill=map_colors.get(m_zone, "#9ea8b1"), opacity=0.76,
                stroke=map_strokes.get(m_zone, "#7f8992"), stroke_width=1.5,
                class_=f"visit_{pid_safe} map-dot c6-segment",
                style="display:none",
                data_info=info,
            )
        )

    # Aggregate (total) dots -- default view
    visit_data_agg = (
        time_location_remapped.groupby(["place_id", "zone_remapped"])
        .agg({"place_id": "count", "time_spend": "sum"})
        .rename(columns={"place_id": "count"})
        .reset_index()
    )
    if visit_data_agg["time_spend"].dtype == "timedelta64[ns]":
        visit_data_agg["hours"] = visit_data_agg["time_spend"].dt.total_seconds() / 3600
    else:
        visit_data_agg["hours"] = visit_data_agg["time_spend"]
    visit_data_agg = visit_data_agg.merge(
        places_edited[["place_id", "lat", "lon"]], on="place_id", how="left"
    )
    val_metric = "count" if mode == "visits" else "hours"
    max_total = visit_data_agg[val_metric].max() or 1
    visit_data_agg["m_zone"] = visit_data_agg["zone_remapped"].map(name_map).fillna("other")
    visit_data_agg = visit_data_agg.dropna(subset=["lat", "lon"])
    if not show_others:
        visit_data_agg = visit_data_agg[visit_data_agg["m_zone"] != "other"]
    visit_data_agg = spread_map_points(visit_data_agg, val_metric)

    total_group = svg.G(id="map_total", class_="map-total", elements=[])
    for _, row in visit_data_agg.iterrows():
        px, py = row["disp_px"], row["disp_py"]
        base_px, base_py = row["map_px"], row["map_py"]
        r = (row[val_metric] / max_total) ** 0.5 * 10 + 2.5
        m_zone = row["m_zone"]
        color = map_colors.get(m_zone, "#9ea8b1")
        loc_name = place_names.get(row["place_id"], str(row["place_id"]))
        info = (
            f"Global Stats | Location: {loc_name} | Total {mode.title()}: "
            f"{fmt(row[val_metric])} | Category: {m_zone.capitalize()}"
        )
        if abs(px - base_px) > 0.5 or abs(py - base_py) > 0.5:
            total_group.elements.append(
                svg.Line(x1=base_px, y1=base_py, x2=px, y2=py,
                          stroke="#c2cbd3", stroke_width=1)
            )
        total_group.elements.append(
            svg.Circle(cx=px, cy=py, r=r + 1.8, fill="#ffffff", opacity=0.64)
        )
        total_group.elements.append(
            DataCircle(
                cx=px, cy=py, r=r, fill=color, opacity=0.34,
                stroke=map_strokes.get(m_zone, "#7f8992"), stroke_width=1,
                class_="c6-segment", style="cursor:pointer",
                data_info=info,
            )
        )
    c6_zoom.elements.append(total_group)
    els.append(c6_shell)

    # Zoom buttons
    zoom_btn_y = c6_y + 24
    zoom_btn_x = c6_x + c6_w - 92
    zoom_buttons = [
        ("c6-zoom-out", "-", 0),
        ("c6-zoom-in", "+", 28),
        ("c6-zoom-reset", "R", 56),
    ]
    for btn_id, label, offset in zoom_buttons:
        els.append(
            svg.Rect(
                id=btn_id, x=zoom_btn_x + offset, y=zoom_btn_y,
                width=22, height=22, rx=5, fill="#ffffff",
                stroke="#ccd7e0", stroke_width=1, style="cursor:pointer",
            )
        )
        els.append(
            svg.Text(
                x=zoom_btn_x + offset + 11, y=zoom_btn_y + 15,
                text=label, text_anchor="middle", class_="c6-zoom-text",
            )
        )

    # Map legend
    legend_x = c6_x + 20
    els.append(svg.Text(x=legend_x, y=legend_y - 10, text="Category", class_="c6-legend"))
    legend_items_c6 = [("Fishing", "fishing"), ("Tourism", "tourism")]
    if show_others:
        legend_items_c6.append(("Other", "other"))
    lx = legend_x
    for label, key in legend_items_c6:
        els.append(
            svg.Circle(cx=lx + 6, cy=legend_y + 4, r=5.5,
                        fill=map_colors[key], stroke=map_strokes[key], stroke_width=1)
        )
        els.append(svg.Text(x=lx + 16, y=legend_y + 8, text=label, class_="c6-legend"))
        lx += 88

    scale_x = c6_x + c6_w - 118
    els.append(svg.Text(x=scale_x, y=legend_y - 10, text="Amount", class_="c6-legend"))
    for radius, cx_offset, label in [(4.5, 8, "low"), (8, 33, "mid"), (12, 66, "high")]:
        cx_val = scale_x + cx_offset
        els.append(svg.Circle(cx=cx_val, cy=legend_y + 4, r=radius + 1.6, fill="#ffffff", opacity=0.75))
        els.append(
            svg.Circle(cx=cx_val, cy=legend_y + 4, r=radius,
                        fill="#cfd8df", stroke="#9aa8b5", stroke_width=1)
        )
        els.append(svg.Text(x=cx_val - 7, y=legend_y + 24, text=label, class_="c6-legend"))

    # =================================================================
    # C7  –  Trip split donut
    # =================================================================
    c7_x, c7_y, c7_w, c7_h = 520, 300, 440, 480
    els.append(
        svg.Rect(x=c7_x, y=c7_y, width=c7_w, height=c7_h,
                  fill="#fbfdff", stroke="#d5dee7", rx=10)
    )
    els.append(
        svg.Text(x=c7_x + 20, y=c7_y + 30, text=title_c7,
                  font_size=18, font_weight="bold", fill="#2c3e50")
    )
    els.append(
        svg.Text(
            x=c7_x + 20, y=c7_y + 46,
            text="inner ring = overall split, outer ring = trips in chronological order",
            class_="c7-note",
        )
    )

    donut_cx, donut_cy = c7_x + c7_w * 0.53, c7_y + c7_h * 0.52 + 18
    inner_r, mid_r, outer_r = 48, 84, 136

    def draw_split(df, pid_safe, is_total=False):
        g = svg.G(
            id=f"split_{pid_safe}",
            style="display:none" if not is_total else "display:block",
            class_="split-info",
            elements=[],
        )
        if df.empty:
            return g

        m_data = df.copy()
        m_data["zone_mapped"] = m_data["zone_remapped"].map(name_map).fillna("other")
        if not show_others:
            m_data = m_data[m_data["zone_mapped"] != "other"]

        if m_data.empty:
            g.elements.append(
                svg.Text(
                    x=donut_cx, y=donut_cy, text="No Matching Activity",
                    text_anchor="middle", font_size=14, fill="#95a5a6",
                    font_style="italic",
                )
            )
            return g

        metric_col = "num_visits" if mode == "visits" else "time_spend"
        m_data["val"] = m_data[metric_col]

        z_sum = m_data.groupby("zone_mapped")["val"].sum()
        total = z_sum.sum() or 0
        primary_zone = z_sum.idxmax() if not z_sum.empty else "other"
        primary_pct = (
            (z_sum.max() / total) * 100 if total > 0 and not z_sum.empty else 0
        )

        if mode == "time_spend":
            center_main = f"{(total / 24):.1f}"
            center_sub = "total days"
        else:
            center_main = f"{total:.0f}"
            center_sub = "total visits"
        center_hint = f"{primary_pct:.0f}% {primary_zone}"

        header = "Total Overview" if is_total else "Member Overview"
        donut_info_base = (
            f"{header} | Mode: {mode.title()} | Total: {fmt(total)} | "
            f"Primary: {z_sum.idxmax().capitalize() if not z_sum.empty else 'N/A'}"
        )

        # Inner donut background ring
        g.elements.append(
            svg.Circle(
                cx=donut_cx, cy=donut_cy, r=(inner_r + mid_r) / 2,
                fill="none", stroke="#eef2f5", stroke_width=(mid_r - inner_r),
            )
        )

        cur_a = -math.pi / 2
        if len(z_sum) == 1:
            zone, val = list(z_sum.items())[0]
            pct = (val / total) * 100 if total > 0 else 0
            seg_info = f"{donut_info_base} | {zone.capitalize()}: {pct:.1f}%"
            donut_g = DataG(
                class_="c7-segment", style="cursor:pointer",
                data_info=seg_info, elements=[],
            )
            donut_g.elements.append(
                svg.Circle(
                    cx=donut_cx, cy=donut_cy, r=(inner_r + mid_r) / 2,
                    fill="none", stroke=focus_colors.get(zone, "#ccc"),
                    stroke_width=(mid_r - inner_r),
                )
            )
            donut_g.elements.append(
                svg.Text(
                    x=donut_cx, y=donut_cy - (inner_r + mid_r) / 2 + 4,
                    text=f"{pct:.0f}%", text_anchor="middle", font_size=12,
                    fill="#ffffff", font_weight="bold",
                    style="pointer-events:none;",
                )
            )
        else:
            donut_g = svg.G(elements=[])
            for zone, val in z_sum.items():
                swp = (val / max(0.001, total)) * 2 * math.pi
                if swp < 0.01:
                    continue
                pct = (val / total) * 100 if total > 0 else 0
                seg_info = f"{donut_info_base} | {zone.capitalize()}: {pct:.1f}%"

                x1 = donut_cx + inner_r * math.cos(cur_a)
                y1 = donut_cy + inner_r * math.sin(cur_a)
                x2 = donut_cx + inner_r * math.cos(cur_a + swp)
                y2 = donut_cy + inner_r * math.sin(cur_a + swp)
                x3 = donut_cx + mid_r * math.cos(cur_a + swp)
                y3 = donut_cy + mid_r * math.sin(cur_a + swp)
                x4 = donut_cx + mid_r * math.cos(cur_a)
                y4 = donut_cy + mid_r * math.sin(cur_a)
                arc = 1 if swp > math.pi else 0
                d = (
                    f"M {x1} {y1} A {inner_r} {inner_r} 0 {arc} 1 {x2} {y2} "
                    f"L {x3} {y3} A {mid_r} {mid_r} 0 {arc} 0 {x4} {y4} Z"
                )
                donut_g.elements.append(
                    DataPath(
                        d=d, fill=focus_colors.get(zone, "#ccc"),
                        stroke="#fff", class_="c7-segment",
                        style="cursor:pointer", data_info=seg_info,
                    )
                )
                if pct > 4:
                    mid_a = cur_a + swp / 2
                    r_text = (inner_r + mid_r) / 2
                    tx = donut_cx + r_text * math.cos(mid_a)
                    ty = donut_cy + r_text * math.sin(mid_a) + 4
                    donut_g.elements.append(
                        svg.Text(
                            x=tx, y=ty, text=f"{pct:.0f}%",
                            text_anchor="middle", font_size=12,
                            fill="#ffffff", font_weight="bold",
                            style="pointer-events:none;",
                        )
                    )
                cur_a += swp
        g.elements.append(donut_g)

        # Outer ring -- trip timeline
        trip_data = (
            m_data.groupby(["date", "zone_mapped"])["val"]
            .sum()
            .unstack(fill_value=0)
        )
        categories = ["fishing", "tourism", "other"]
        trip_data = trip_data.reindex(columns=categories, fill_value=0).reset_index()
        trip_data = trip_data.sort_values("date")

        n_t = len(trip_data)
        if n_t > 0:
            t_range = (
                (pd.to_datetime(sel_end) - pd.to_datetime(sel_start)).total_seconds()
                or 1
            )

            def get_ang(t):
                frac = (
                    (pd.to_datetime(t) - pd.to_datetime(sel_start)).total_seconds()
                    / t_range
                )
                return -math.pi / 2 + frac * 2 * math.pi

            m_t_v = trip_data[categories].sum(axis=1).max() or 1
            if not show_others:
                base_r = (mid_r + outer_r) / 2
                max_h = (outer_r - mid_r) / 2
                bg_rings = [base_r - max_h, base_r, base_r + max_h]
            else:
                base_r = mid_r + 12
                max_h = outer_r - base_r
                bg_rings = [base_r, base_r + max_h * 0.5, outer_r]

            slice_span = 0.05

            for ring_r in bg_rings:
                g.elements.append(
                    svg.Circle(
                        cx=donut_cx, cy=donut_cy, r=ring_r,
                        fill="none", stroke="#edf2f6", stroke_width=1,
                        stroke_dasharray="2,2",
                    )
                )

            # Day labels / spokes
            num_days = (
                (pd.to_datetime(sel_end) - pd.to_datetime(sel_start)).days + 1
            )
            label_step = 1 if num_days <= 14 else (5 if num_days <= 60 else 30)
            for d_idx in range(0, num_days + 1, label_step):
                d_val = pd.to_datetime(sel_start) + pd.Timedelta(days=d_idx)
                if d_val > pd.to_datetime(sel_end) + pd.Timedelta(days=1):
                    continue
                ang = get_ang(d_val)
                lx1 = donut_cx + (mid_r + 4) * math.cos(ang)
                ly1 = donut_cy + (mid_r + 4) * math.sin(ang)
                lx2 = donut_cx + (outer_r + 12) * math.cos(ang)
                ly2 = donut_cy + (outer_r + 12) * math.sin(ang)
                g.elements.append(
                    svg.Line(
                        x1=lx1, y1=ly1, x2=lx2, y2=ly2,
                        stroke="#d1dbe5", stroke_width=0.8, stroke_dasharray="2,2",
                    )
                )
                tx = donut_cx + (outer_r + 24) * math.cos(ang)
                ty = donut_cy + (outer_r + 24) * math.sin(ang)
                date_str = d_val.strftime("%b %d")
                g.elements.append(
                    svg.Text(
                        x=tx, y=ty, text=date_str, text_anchor="middle",
                        font_size=9, fill="#95a5a6",
                        transform=f"rotate({math.degrees(ang) + 90}, {tx}, {ty})",
                    )
                )

            for i, (_, row) in enumerate(trip_data.iterrows()):
                ang_b = get_ang(row["date"])
                cur_br = base_r
                t_val = row[categories].sum()
                date_string = (
                    row["date"].strftime("%Y-%m-%d")
                    if hasattr(row["date"], "strftime")
                    else str(row["date"])
                )
                date_info = f"Daily Summary | Date: {date_string} | Total: {fmt(t_val)}"

                focus_summary_parts = []
                for zone in categories:
                    v = row.get(zone, 0)
                    if v > 0:
                        p = (v / t_val) * 100 if t_val > 0 else 0
                        focus_summary_parts.append(
                            f"{zone.capitalize()}: {fmt(v)} ({p:.1f}%)"
                        )
                shared_info = f"{date_info} | {' | '.join(focus_summary_parts)}"

                trip_els = []
                sep_x1 = donut_cx + (base_r - 4) * math.cos(ang_b)
                sep_y1 = donut_cy + (base_r - 4) * math.sin(ang_b)
                sep_x2 = donut_cx + (outer_r + 4) * math.cos(ang_b)
                sep_y2 = donut_cy + (outer_r + 4) * math.sin(ang_b)
                trip_els.append(
                    svg.Line(
                        x1=sep_x1, y1=sep_y1, x2=sep_x2, y2=sep_y2,
                        stroke="#f0f4f7", stroke_width=1,
                    )
                )

                for zone in categories:
                    val = row.get(zone, 0)
                    h_v = (val / m_t_v) * max_h
                    if h_v < 0.5:
                        continue

                    if not show_others and zone == "tourism":
                        start_r = base_r
                        end_h_v = -h_v
                    else:
                        start_r = cur_br
                        end_h_v = h_v

                    x1 = donut_cx + start_r * math.cos(ang_b)
                    y1 = donut_cy + start_r * math.sin(ang_b)
                    x2 = donut_cx + start_r * math.cos(ang_b + slice_span)
                    y2 = donut_cy + start_r * math.sin(ang_b + slice_span)
                    x3 = donut_cx + (start_r + end_h_v) * math.cos(ang_b + slice_span)
                    y3 = donut_cy + (start_r + end_h_v) * math.sin(ang_b + slice_span)
                    x4 = donut_cx + (start_r + end_h_v) * math.cos(ang_b)
                    y4 = donut_cy + (start_r + end_h_v) * math.sin(ang_b)

                    trip_els.append(
                        svg.Polygon(
                            points=f"{x1},{y1} {x2},{y2} {x3},{y3} {x4},{y4}",
                            fill=focus_colors.get(zone, "#ccc"),
                            opacity=0.84, stroke="#ffffff", stroke_width=0.8,
                        )
                    )
                    if not (not show_others and zone == "tourism"):
                        cur_br += h_v

                g.elements.append(
                    DataG(
                        elements=trip_els, class_="c7-segment",
                        style="cursor:pointer", data_info=shared_info,
                    )
                )

        # Centre label
        g.elements.append(
            svg.Circle(cx=donut_cx, cy=donut_cy, r=inner_r - 11,
                        fill="#ffffff", stroke="#dce5ec", stroke_width=1.2)
        )
        g.elements.append(
            svg.Text(
                x=donut_cx, y=donut_cy - 4, text=center_main,
                id=f"t_val_{pid_safe}", text_anchor="middle",
                font_size=24, font_weight="bold", fill="#22313c",
            )
        )
        g.elements.append(
            svg.Text(x=donut_cx, y=donut_cy + 16, text=center_sub,
                      text_anchor="middle", font_size=12, fill="#738596")
        )
        g.elements.append(
            svg.Text(
                x=donut_cx, y=donut_cy + 48, text="",
                id=f"hover_txt_{pid_safe}", class_="hover-tip",
                text_anchor="middle", font_size=10, fill="#e74c3c",
                font_weight="bold",
            )
        )
        return g

    # -- Total split
    els.append(draw_split(graph_2_2_data, "total", is_total=True))

    # -- Per-member splits
    c5_members = data_c5["people_id"].unique()
    for member in c5_members:
        pid_safe = member.replace(" ", "_")
        els.append(
            draw_split(
                graph_2_2_data[graph_2_2_data["people_id"] == member], pid_safe
            )
        )

    # C7 legend
    legend_items_c7 = [("Fishing", "fishing"), ("Tourism", "tourism")]
    if show_others:
        legend_items_c7.append(("Other", "other"))
    lx, ly = c7_x + 34, c7_y + c7_h - 24
    for label, key in legend_items_c7:
        els.append(
            svg.Circle(cx=lx + 6, cy=ly - 4, r=5.5,
                        fill=focus_colors[key], stroke="#ffffff", stroke_width=1)
        )
        els.append(svg.Text(x=lx + 17, y=ly, text=label, class_="c7-legend"))
        lx += 96

    # =================================================================
    # Assemble final HTML
    # =================================================================
    svg_str = str(svg.SVG(width=W, height=H, elements=els))

    _CSS = """
    <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; position: relative; }
    #tooltip {
        position: absolute;
        background: #ffffff;
        border: 1px solid #d1d8e0;
        padding: 0;
        border-radius: 8px;
        pointer-events: none;
        display: none;
        font-size: 13px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        z-index: 10000;
        color: #2f3640;
        min-width: 180px;
        overflow: hidden;
    }
    .tt-header {
        background: #f1f2f6;
        padding: 8px 12px;
        font-weight: bold;
        border-bottom: 1px solid #d1d8e0;
        color: #2f3542;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .tt-body { padding: 10px 12px; line-height: 1.6; }
    .tt-row { display: flex; justify-content: space-between; gap: 15px; }
    .tt-label { color: #747d8c; }
    .tt-val { font-weight: 600; color: #2f3542; }
    .tt-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
    .locked-person circle, .locked-person path {
        filter: drop-shadow(0 0 10px rgba(44, 62, 80, 0.4));
        stroke: #2c3e50 !important;
        stroke-width: 2px !important;
    }
    </style>
    """

    _JS = """
    <div id="tooltip"></div>
    <script>
    (function() {
        let lockedPid = null;
        const tooltip = document.getElementById('tooltip');

        function formatInfo(info) {
            const parts = info.split(' | ');
            if (parts.length < 2) return info;
            let html = `<div class="tt-header">${parts[0]}</div><div class="tt-body">`;
            for (let i = 1; i < parts.length; i++) {
                const sub = parts[i].split(': ');
                if (sub.length === 2) {
                    html += `<div class="tt-row"><span class="tt-label">${sub[0]}</span><span class="tt-val">${sub[1]}</span></div>`;
                } else {
                    html += `<div style="margin-top:4px; font-weight:500;">${parts[i]}</div>`;
                }
            }
            html += '</div>';
            return html;
        }

        function showMember(pid) {
            document.querySelectorAll('.map-dot').forEach(d => d.style.display = 'none');
            document.querySelectorAll('.split-info').forEach(s => s.style.display = 'none');
            const mapTotal = document.getElementById('map_total');
            if (mapTotal) mapTotal.style.display = 'none';

            document.querySelectorAll('.visit_' + pid).forEach(d => d.style.display = '');
            const split = document.getElementById('split_' + pid);
            if (split) split.style.display = 'block';

            document.querySelectorAll('.clickable-person').forEach(p => p.classList.remove('locked-person'));
            const pEl = document.querySelector('.pid-' + pid);
            if (pEl) pEl.classList.add('locked-person');
        }

        function resetView() {
            if (lockedPid) return;
            document.querySelectorAll('.map-dot').forEach(d => d.style.display = 'none');
            document.querySelectorAll('.split-info').forEach(s => s.style.display = 'none');
            const mapTotal = document.getElementById('map_total');
            if (mapTotal) mapTotal.style.display = 'block';
            const splitTotal = document.getElementById('split_total');
            if (splitTotal) splitTotal.style.display = 'block';
            document.querySelectorAll('.clickable-person').forEach(p => p.classList.remove('locked-person'));
        }

        function initMapZoom() {
            const mapBg = document.getElementById('c6-map-bg');
            const mapZoom = document.getElementById('c6-map-zoom');
            const mapShell = document.getElementById('c6-map-shell');
            if (!mapBg || !mapZoom || !mapShell) return;
            const svgRoot = mapBg.ownerSVGElement;

            const bx = parseFloat(mapBg.getAttribute('x'));
            const by = parseFloat(mapBg.getAttribute('y'));
            const bw = parseFloat(mapBg.getAttribute('width'));
            const bh = parseFloat(mapBg.getAttribute('height'));
            const cx = bx + bw / 2;
            const cy = by + bh / 2;
            const minScale = 1;
            const maxScale = 4;
            let scale = 1;
            let tx = 0;
            let ty = 0;
            let isDragging = false;
            let dragStartX = 0;
            let dragStartY = 0;
            let dragTx = 0;
            let dragTy = 0;

            function clampPan() {
                const minTx = (bx + bw) * (1 - scale);
                const maxTx = bx * (1 - scale);
                const minTy = (by + bh) * (1 - scale);
                const maxTy = by * (1 - scale);
                tx = Math.min(maxTx, Math.max(minTx, tx));
                ty = Math.min(maxTy, Math.max(minTy, ty));
            }

            function eventPoint(e) {
                const svgRect = svgRoot.getBoundingClientRect();
                return {
                    x: e.clientX - svgRect.left,
                    y: e.clientY - svgRect.top,
                };
            }

            function applyZoom() {
                clampPan();
                mapZoom.setAttribute('transform', `matrix(${scale} 0 0 ${scale} ${tx} ${ty})`);
                const cursor = scale > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default';
                mapBg.style.cursor = cursor;
                mapShell.style.cursor = cursor;
                mapZoom.style.pointerEvents = isDragging ? 'none' : 'auto';
            }

            function zoomAt(factor, focusX, focusY) {
                const nextScale = Math.max(minScale, Math.min(maxScale, scale * factor));
                if (Math.abs(nextScale - scale) < 0.0001) return;
                const ratio = nextScale / scale;
                tx = focusX - (focusX - tx) * ratio;
                ty = focusY - (focusY - ty) * ratio;
                scale = nextScale;
                applyZoom();
            }

            function resetZoom() {
                scale = 1;
                tx = 0;
                ty = 0;
                isDragging = false;
                applyZoom();
            }

            [mapShell, mapBg].forEach(el => {
                el.addEventListener('wheel', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const { x: focusX, y: focusY } = eventPoint(e);
                    if (focusX < bx || focusX > bx + bw || focusY < by || focusY > by + bh) return;
                    zoomAt(e.deltaY < 0 ? 1.18 : 1 / 1.18, focusX, focusY);
                }, { passive: false });
            });

            svgRoot.addEventListener('mousedown', (e) => {
                if (scale <= 1) return;
                const { x: focusX, y: focusY } = eventPoint(e);
                if (focusX < bx || focusX > bx + bw || focusY < by || focusY > by + bh) return;
                isDragging = true;
                dragStartX = e.clientX;
                dragStartY = e.clientY;
                dragTx = tx;
                dragTy = ty;
                tooltip.style.display = 'none';
                applyZoom();
                e.preventDefault();
            });

            document.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                tx = dragTx + (e.clientX - dragStartX);
                ty = dragTy + (e.clientY - dragStartY);
                tooltip.style.display = 'none';
                applyZoom();
            });

            document.addEventListener('mouseup', () => {
                if (!isDragging) return;
                isDragging = false;
                applyZoom();
            });

            [
                ['c6-zoom-in', () => zoomAt(1.2, cx, cy)],
                ['c6-zoom-out', () => zoomAt(1 / 1.2, cx, cy)],
                ['c6-zoom-reset', resetZoom],
            ].forEach(([id, handler]) => {
                const btn = document.getElementById(id);
                if (!btn) return;
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handler();
                });
            });
        }

        function init() {
            const persons = document.querySelectorAll('.clickable-person');
            const segments = document.querySelectorAll('.c7-segment, .c6-segment');

            persons.forEach(p => {
                const pidClass = [...p.classList].find(c => c.startsWith('pid-'));
                if (!pidClass) return;
                const pid = pidClass.replace('pid-', '');

                p.addEventListener('mouseenter', () => { if (!lockedPid) showMember(pid); });
                p.addEventListener('mouseleave', () => resetView());
                p.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (lockedPid === pid) {
                        lockedPid = null;
                        resetView();
                    } else {
                        lockedPid = pid;
                        showMember(pid);
                    }
                });
            });

            segments.forEach(seg => {
                seg.addEventListener('mouseenter', () => {
                    const info = seg.getAttribute('data-info');
                    if (info) {
                        tooltip.style.display = 'block';
                        tooltip.innerHTML = formatInfo(info);
                    }
                });
                seg.addEventListener('mousemove', (e) => {
                    const x = e.pageX + 15;
                    const y = e.pageY + 15;
                    tooltip.style.left = x + 'px';
                    tooltip.style.top = y + 'px';

                    const box = tooltip.getBoundingClientRect();
                    if (x + box.width > window.innerWidth) tooltip.style.left = (e.pageX - box.width - 15) + 'px';
                    if (y + box.height > window.innerHeight) tooltip.style.top = (e.pageY - box.height - 15) + 'px';
                });
                seg.addEventListener('mouseleave', () => {
                    tooltip.style.display = 'none';
                });
            });

            document.addEventListener('click', () => {
                lockedPid = null;
                resetView();
            });

            initMapZoom();
        }

        let timer = setInterval(() => {
            if (document.querySelector('.clickable-person')) {
                clearInterval(timer);
                init();
            }
        }, 100);
    })();
    </script>
    """

    return svg_str + _CSS + _JS
