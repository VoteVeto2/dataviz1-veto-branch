# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.23.3",
#     "numpy==2.4.4",
#     "pandas==3.0.2",
#     "svg.py==1.10.0",
# ]
# ///

import marimo

__generated_with = "0.23.3"
app = marimo.App(width="full", app_title="Topics, Meetings, Discussions and Plans")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import svg
    import math
    import numpy as np

    return (math, mo, np, pd, svg)


@app.cell
def _(mo, pd):
    try:
        df = pd.read_json(str(mo.notebook_location() / "data" / "people_participation_summary.json"))
    except:
        df = pd.read_json("https://raw.githubusercontent.com/tvakul/dataviz1/refs/heads/main/data/people_participation_summary.json")
    return (df,)


@app.cell
def _(mo, pd):
    try:
        df_totals = pd.read_json(str(mo.notebook_location() / "data" / "people_participation_total.json"))
    except:
        df_totals = pd.read_json("https://raw.githubusercontent.com/tvakul/dataviz1/refs/heads/main/data/people_participation_total.json")
    return (df_totals,)


@app.cell
def _(df, mo):
    metrics = ['num_topics', 'num_meetings', 'num_discussions', 'num_plans']
    df[metrics] = df[metrics].fillna(0)

    focus_colors = {
        'fishing': '#2ca02c',
        'tourism': '#d62728',
        'both': '#17becf',
        'other': '#7f7f7f'
    }
    person_colors = {
        'Carol Limpet': '#ff7f0e',
        'Ed Helpsford': '#9467bd',
        'Seal': '#8c564b',
        'Simone Kat': '#e377c2',
        'Tante Titan': '#1f77b4',
        'Teddy Goldstein': '#bcbd22'
    }

    # UI Checkboxes
    all_people = sorted(df['people_id'].dropna().unique())
    all_focuses = sorted(df['focus'].dropna().unique())

    people_ui = mo.ui.dictionary({p: mo.ui.checkbox(value=True, label=p) for p in all_people})
    focus_ui = mo.ui.dictionary({f: mo.ui.checkbox(value=True, label=f) for f in all_focuses})
    return focus_colors, focus_ui, metrics, people_ui


@app.cell
def _(
    df,
    df_totals,
    focus_colors,
    focus_ui,
    math,
    metrics,
    mo,
    pd,
    people_ui,
    svg,
):

    selected_people = [p for p, active in people_ui.value.items() if active]
    selected_focuses = [f for f, active in focus_ui.value.items() if active]

    filtered_df = df[
        (df['people_id'].isin(selected_people)) &
        (df['focus'].isin(selected_focuses))
    ].copy()

    filtered_totals_df = df_totals[df_totals['focus'].isin(selected_focuses)].copy()

    x_labels = ['Topics', 'Meetings', 'Discussions', 'Plans']

    if filtered_df.empty:
        totals = pd.DataFrame(columns=metrics)
        max_val = 1
    else:
        totals = filtered_df.groupby('people_id')[metrics].sum()
        max_val = totals.max().max()
        max_val = max(1, max_val)

    padding_x = 160
    padding_y = 100
    right_margin = 180
    width = 800
    height = max(400, len(selected_people) * 80 + padding_y * 2)

    max_radius = 35

    n_x = len(metrics)
    n_y = len(selected_people)

    if n_x > 1:
        x_coords = [padding_x + _i * (width - right_margin - padding_x) / (n_x - 1) for _i in range(n_x)]
    else:
        x_coords = [(padding_x + width - right_margin) / 2]

    if n_y > 1:
        y_coords = [padding_y + _i * (height - 2 * padding_y) / (n_y - 1) for _i in range(n_y)]
    else:
        y_coords = [height / 2] if n_y == 1 else []

    def create_pie_slice(cx, cy, r, start_angle, end_angle, color):
        if end_angle - start_angle >= 2 * math.pi - 0.0001:
            return svg.Circle(class_="pie-slice", cx=cx, cy=cy, r=r, fill=color, stroke="white", stroke_width=0.5)
        x1 = cx + r * math.cos(start_angle)
        y1 = cy + r * math.sin(start_angle)
        x2 = cx + r * math.cos(end_angle)
        y2 = cy + r * math.sin(end_angle)
        large_arc = 1 if end_angle - start_angle > math.pi else 0
        path_data = f'M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z'
        return svg.Path(class_="pie-slice", d=path_data, fill=color, stroke="white", stroke_width=0.5)

    elements = []
    elements.append(svg.Style(text="""
        .pie-slice { transition: opacity 0.2s, stroke-width 0.2s; }
        .pie-group { cursor: pointer; }
        .pie-group:hover .pie-slice { opacity: 0.7; stroke: #333 !important; stroke-width: 1.5 !important; }
    """))
    elements.append(svg.Rect(width="100%", height="100%", fill="white"))

    # Column totals (top bars)
    max_bar_width = 80
    bar_height = 16

    for _j, metric in enumerate(metrics):
        x_pos = x_coords[_j]
        col_total = filtered_totals_df[metric].sum() if not filtered_totals_df.empty else 0
        if col_total > 0:
            bar_w = max_bar_width
            curr_x = x_pos - (bar_w / 2)
            metric_clean = x_labels[_j]
            tooltip_lines = [f"{metric_clean} (Unique, Overall)", f"Total: {int(col_total)}", "---"]

            group_elements = []
            for focus in selected_focuses:
                val = filtered_totals_df.loc[filtered_totals_df['focus'] == focus, metric].sum()
                if val > 0:
                    seg_w = (val / col_total) * bar_w
                    color = focus_colors.get(focus, '#000000')
                    group_elements.append(svg.Rect(class_="pie-slice", x=curr_x, y=padding_y - 65, width=seg_w, height=bar_height, fill=color, stroke="white", stroke_width=0.5))
                    curr_x += seg_w
                    tooltip_lines.append(f"{focus.capitalize()}: {int(val)}")

            # Add title for tooltip
            group_elements.insert(0, svg.Title(text="\n".join(tooltip_lines)))
            elements.append(svg.G(class_="pie-group", elements=group_elements))
            elements.append(svg.Text(x=x_pos, y=padding_y - 72, font_family="sans-serif", font_size="11", font_weight="bold", fill="#555", text_anchor="middle", text=str(int(col_total))))

    # Grid lines and labels
    for _i, x_pos in enumerate(x_coords):
        elements.append(svg.Line(x1=x_pos, y1=padding_y - 45, x2=x_pos, y2=height - padding_y + 45, stroke="#eeeeee", stroke_width=1))
        elements.append(svg.Text(x=x_pos, y=height - padding_y + 65, font_family="sans-serif", font_size="12", font_weight="bold", text_anchor="middle", text=x_labels[_i]))

    for _i, person in enumerate(selected_people):
        y_pos = y_coords[_i]
        elements.append(svg.Line(x1=padding_x - 45, y1=y_pos, x2=width - right_margin + 20, y2=y_pos, stroke="#dddddd", stroke_dasharray="4", stroke_width=1))
        elements.append(svg.Text(x=padding_x - 50, y=y_pos + 4, font_family="sans-serif", font_size="12", font_weight="bold", text_anchor="end", text=person))

    # Pie charts matrix
    for _i, person in enumerate(selected_people):
        y_pos = y_coords[_i]
        for _j, metric in enumerate(metrics):
            x_pos = x_coords[_j]
            if person not in totals.index:
                continue
            person_data = filtered_df[filtered_df['people_id'] == person]
            values = person_data[metric].values
            labels = person_data['focus'].values
            mask = values > 0
            values = values[mask]
            labels = labels[mask]
            if len(values) > 0:
                total_val = values.sum()
                _r = max_radius * math.sqrt(total_val / max_val)
                metric_clean = x_labels[_j]
                tooltip_lines = [f"{person} | {metric_clean}", f"Total: {int(total_val)}", "---"]
                for val, label in zip(values, labels):
                    tooltip_lines.append(f"{label.capitalize()}: {int(val)}")

                group_elements = [svg.Title(text="\n".join(tooltip_lines))]
                start_angle = 0
                for val, label in zip(values, labels):
                    angle = (val / total_val) * 2 * math.pi
                    end_angle = start_angle + angle
                    color = focus_colors.get(label, '#000000')
                    group_elements.append(create_pie_slice(x_pos, y_pos, _r, start_angle, end_angle, color))
                    start_angle = end_angle
                elements.append(svg.G(class_="pie-group", elements=group_elements))

    # Legend
    legend_x = width - right_margin + 30
    legend_y = padding_y
    if len(selected_focuses) > 0:
        elements.append(svg.Text(x=legend_x, y=legend_y, font_family="sans-serif", font_size="14", font_weight="bold", text="Focus"))
        legend_y += 20
        for focus in selected_focuses:
            color = focus_colors.get(focus, '#000000')
            elements.append(svg.Rect(x=legend_x, y=legend_y - 10, width=15, height=15, fill=color))
            elements.append(svg.Text(x=legend_x + 25, y=legend_y + 2, font_family="sans-serif", font_size="12", text=focus.capitalize()))
            legend_y += 20

    if max_val > 0 and len(selected_people) > 0:
        legend_y += 20
        elements.append(svg.Text(x=legend_x, y=legend_y, font_family="sans-serif", font_size="14", font_weight="bold", text="Total"))
        legend_y += 45
        example_vals = [max_val, max_val/2, max_val/4] if max_val >= 4 else [max_val, 1]
        example_vals = sorted(list(set([max(1, int(v)) for v in example_vals])), reverse=True)
        for val in example_vals:
            _r = max_radius * math.sqrt(val / max_val)
            elements.append(svg.Circle(cx=legend_x + 30, cy=legend_y, r=_r, fill="#dddddd", stroke="white", stroke_width=1))
            elements.append(svg.Text(x=legend_x + 50 + max_radius, y=legend_y + 4, font_family="sans-serif", font_size="12", text=str(val)))
            legend_y += _r + max_radius + 5

    svg_obj = svg.SVG(width=width, height=height, elements=elements)

    visual3 = mo.vstack([
            mo.md('### **Number of topics, meetings, discussions and plans**'),
            mo.hstack([
                mo.Html(svg_obj.as_str()),
                mo.vstack([
                    mo.vstack([mo.md("**Select People:**"), people_ui]),
                    mo.vstack([mo.md("**Select Focus Types:**"), focus_ui])
            ])
        ])
    ])
    visual3


if __name__ == "__main__":
    app.run()
