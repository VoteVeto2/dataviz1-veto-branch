"""Builder for dashboard 3: pie chart matrix (topics, meetings, discussions, plans).

Pure Python module -- no marimo imports.
Returns an SVG string suitable for mo.Html().
"""

import math
import svg
import pandas as pd


def build_d3_svg(df, df_totals, selected_people, selected_focuses, focus_colors):
    """Build pie chart matrix SVG. Returns SVG string (for mo.Html()).

    Parameters
    ----------
    df : pd.DataFrame
        people_participation_summary with columns:
        people_id, focus, num_topics, num_meetings, num_discussions, num_plans.
    df_totals : pd.DataFrame
        people_participation_total with columns:
        focus, num_topics, num_meetings, num_discussions, num_plans.
    selected_people : list[str]
        People IDs to display (rows).
    selected_focuses : list[str]
        Focus categories to display (pie slices).
    focus_colors : dict[str, str]
        Mapping focus -> hex color.

    Returns
    -------
    str
        Complete ``<svg>`` markup.
    """
    metrics = ["num_topics", "num_meetings", "num_discussions", "num_plans"]
    x_labels = ["Topics", "Meetings", "Discussions", "Plans"]

    # -- filter -----------------------------------------------------------
    filtered_df = df[
        (df["people_id"].isin(selected_people))
        & (df["focus"].isin(selected_focuses))
    ].copy()

    filtered_totals_df = df_totals[df_totals["focus"].isin(selected_focuses)].copy()

    if filtered_df.empty:
        totals = pd.DataFrame(columns=metrics)
        max_val = 1
    else:
        totals = filtered_df.groupby("people_id")[metrics].sum()
        max_val = totals.max().max()
        max_val = max(1, max_val)

    # -- layout constants -------------------------------------------------
    padding_x = 160
    padding_y = 100
    right_margin = 180
    width = 800
    height = max(400, len(selected_people) * 80 + padding_y * 2)
    max_radius = 35

    n_x = len(metrics)
    n_y = len(selected_people)

    if n_x > 1:
        x_coords = [
            padding_x + i * (width - right_margin - padding_x) / (n_x - 1)
            for i in range(n_x)
        ]
    else:
        x_coords = [(padding_x + width - right_margin) / 2]

    if n_y > 1:
        y_coords = [
            padding_y + i * (height - 2 * padding_y) / (n_y - 1)
            for i in range(n_y)
        ]
    elif n_y == 1:
        y_coords = [height / 2]
    else:
        y_coords = []

    # -- helpers ----------------------------------------------------------
    def _pie_slice(cx, cy, r, start_angle, end_angle, color):
        if end_angle - start_angle >= 2 * math.pi - 0.0001:
            return svg.Circle(
                class_="pie-slice", cx=cx, cy=cy, r=r,
                fill=color, stroke="white", stroke_width=0.5,
            )
        x1 = cx + r * math.cos(start_angle)
        y1 = cy + r * math.sin(start_angle)
        x2 = cx + r * math.cos(end_angle)
        y2 = cy + r * math.sin(end_angle)
        large_arc = 1 if end_angle - start_angle > math.pi else 0
        d = f"M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z"
        return svg.Path(
            class_="pie-slice", d=d,
            fill=color, stroke="white", stroke_width=0.5,
        )

    # -- build elements ---------------------------------------------------
    elements = []

    elements.append(svg.Style(text="""
        .pie-slice { transition: opacity 0.2s, stroke-width 0.2s; }
        .pie-group { cursor: pointer; }
        .pie-group:hover .pie-slice { opacity: 0.7; stroke: #333 !important; stroke-width: 1.5 !important; }
    """))
    elements.append(svg.Rect(width="100%", height="100%", fill="#FDF8F4"))

    # -- column-total bars (top) ------------------------------------------
    max_bar_width = 80
    bar_height = 16

    for j, metric in enumerate(metrics):
        x_pos = x_coords[j]
        col_total = (
            filtered_totals_df[metric].sum() if not filtered_totals_df.empty else 0
        )
        if col_total > 0:
            bar_w = max_bar_width
            curr_x = x_pos - bar_w / 2
            metric_clean = x_labels[j]
            tooltip_lines = [
                f"{metric_clean} (Unique, Overall)",
                f"Total: {int(col_total)}",
                "---",
            ]

            group_elements = []
            for focus in selected_focuses:
                val = filtered_totals_df.loc[
                    filtered_totals_df["focus"] == focus, metric
                ].sum()
                if val > 0:
                    seg_w = (val / col_total) * bar_w
                    color = focus_colors.get(focus, "#000000")
                    group_elements.append(
                        svg.Rect(
                            class_="pie-slice",
                            x=curr_x,
                            y=padding_y - 65,
                            width=seg_w,
                            height=bar_height,
                            fill=color,
                            stroke="white",
                            stroke_width=0.5,
                        )
                    )
                    curr_x += seg_w
                    tooltip_lines.append(f"{focus.capitalize()}: {int(val)}")

            group_elements.insert(0, svg.Title(text="\n".join(tooltip_lines)))
            elements.append(svg.G(class_="pie-group", elements=group_elements))
            elements.append(
                svg.Text(
                    x=x_pos,
                    y=padding_y - 72,
                    font_family="sans-serif",
                    font_size="11",
                    font_weight="bold",
                    fill="#8A7E74",
                    text_anchor="middle",
                    text=str(int(col_total)),
                )
            )

    # -- grid lines and labels --------------------------------------------
    for i, x_pos in enumerate(x_coords):
        elements.append(
            svg.Line(
                x1=x_pos, y1=padding_y - 45,
                x2=x_pos, y2=height - padding_y + 45,
                stroke="#E8DDD4", stroke_width=1,
            )
        )
        elements.append(
            svg.Text(
                x=x_pos,
                y=height - padding_y + 65,
                font_family="sans-serif",
                font_size="12",
                font_weight="bold",
                text_anchor="middle",
                text=x_labels[i],
            )
        )

    for i, person in enumerate(selected_people):
        y_pos = y_coords[i]
        elements.append(
            svg.Line(
                x1=padding_x - 45, y1=y_pos,
                x2=width - right_margin + 20, y2=y_pos,
                stroke="#E8DDD4", stroke_dasharray="4", stroke_width=1,
            )
        )
        elements.append(
            svg.Text(
                x=padding_x - 50,
                y=y_pos + 4,
                font_family="sans-serif",
                font_size="12",
                font_weight="bold",
                text_anchor="end",
                text=person,
            )
        )

    # -- pie charts -------------------------------------------------------
    for i, person in enumerate(selected_people):
        y_pos = y_coords[i]
        for j, metric in enumerate(metrics):
            x_pos = x_coords[j]
            if person not in totals.index:
                continue
            person_data = filtered_df[filtered_df["people_id"] == person]
            values = person_data[metric].values
            labels = person_data["focus"].values
            mask = values > 0
            values = values[mask]
            labels = labels[mask]
            if len(values) > 0:
                total_val = values.sum()
                r = max_radius * math.sqrt(total_val / max_val)
                metric_clean = x_labels[j]
                tooltip_lines = [
                    f"{person} | {metric_clean}",
                    f"Total: {int(total_val)}",
                    "---",
                ]
                for val, lbl in zip(values, labels):
                    tooltip_lines.append(f"{lbl.capitalize()}: {int(val)}")

                group_elements = [svg.Title(text="\n".join(tooltip_lines))]
                start_angle = 0
                for val, lbl in zip(values, labels):
                    angle = (val / total_val) * 2 * math.pi
                    end_angle = start_angle + angle
                    color = focus_colors.get(lbl, "#000000")
                    group_elements.append(
                        _pie_slice(x_pos, y_pos, r, start_angle, end_angle, color)
                    )
                    start_angle = end_angle
                elements.append(svg.G(class_="pie-group", elements=group_elements))

    # -- legend -----------------------------------------------------------
    legend_x = width - right_margin + 30
    legend_y = padding_y
    if len(selected_focuses) > 0:
        elements.append(
            svg.Text(
                x=legend_x, y=legend_y,
                font_family="sans-serif", font_size="14",
                font_weight="bold", text="Focus",
            )
        )
        legend_y += 20
        for focus in selected_focuses:
            color = focus_colors.get(focus, "#000000")
            elements.append(
                svg.Rect(x=legend_x, y=legend_y - 10, width=15, height=15, fill=color)
            )
            elements.append(
                svg.Text(
                    x=legend_x + 25, y=legend_y + 2,
                    font_family="sans-serif", font_size="12",
                    text=focus.capitalize(),
                )
            )
            legend_y += 20

    if max_val > 0 and len(selected_people) > 0:
        legend_y += 20
        elements.append(
            svg.Text(
                x=legend_x, y=legend_y,
                font_family="sans-serif", font_size="14",
                font_weight="bold", text="Total",
            )
        )
        legend_y += 45
        example_vals = (
            [max_val, max_val / 2, max_val / 4] if max_val >= 4 else [max_val, 1]
        )
        example_vals = sorted(
            list(set([max(1, int(v)) for v in example_vals])), reverse=True
        )
        for val in example_vals:
            r = max_radius * math.sqrt(val / max_val)
            elements.append(
                svg.Circle(
                    cx=legend_x + 30, cy=legend_y, r=r,
                    fill="#E8DDD4", stroke="white", stroke_width=1,
                )
            )
            elements.append(
                svg.Text(
                    x=legend_x + 50 + max_radius, y=legend_y + 4,
                    font_family="sans-serif", font_size="12",
                    text=str(val),
                )
            )
            legend_y += r + max_radius + 5

    svg_obj = svg.SVG(width=width, height=height, elements=elements)
    return svg_obj.as_str()
