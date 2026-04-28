# Improvement Plan for DataViz1

> Analysis of [tvakul.github.io/dataviz1](https://tvakul.github.io/dataviz1/) and the codebase, with actionable tasks to improve the application.

---

## Current State Assessment

The application works and its three visualizations are technically sophisticated. However, it presents as a raw notebook output rather than a polished data story. The main gaps are:

- **No narrative context** -- the app drops users straight into tabs with no framing
- **No visual identity** -- default Marimo styling, no custom theme
- **Accessibility issues** -- red/green color scheme is problematic for ~8% of male viewers
- **Dense information** -- all three tabs require significant effort to parse without guidance
- **Fixed dimensions** -- hardcoded pixel widths break on smaller screens
- **Tooltip/legend polish** -- overlaps, edge-clipping, and inconsistent styling

---

## Proposed Improvements

Keeping the big direction the same (same 3 visualizations, same data pipeline, same analytical approach). Ordered from simplest to most impactful.

### Phase 1: Quick UI Wins (2-3 hours)

#### 1.1 Colorblind-Safe Palette
**What:** Replace the red/green diverging scale with blue/orange.
**Where:** `index.py` lines 274-277 (`color_for()` function) and lines 946-951 (`focus_colors` dict).
**Change:**
```python
# Sentiment map: blue = pro-fishing, orange = pro-tourism
def color_for(s):
    t = min(abs(s), 1.0)
    return interp(t, (255, 255, 255),
                  (49, 130, 189) if s >= 0 else (222, 119, 42))

# Participation chart
focus_colors = {
    'fishing':  '#3182bd',   # blue
    'tourism':  '#de772a',   # orange
    'both':     '#756bb1',   # purple
    'other':    '#969696'    # gray
}
```

#### 1.2 Descriptive Tab Labels
**What:** Replace cryptic tab names with scannable labels.
**Where:** `index.py` lines 3077-3081.
**Change:**
```python
mo.ui.tabs({
    "Sentiment Bias Map": visual1,
    "Travel & Time Analysis": visual2,
    "Participation Metrics": visual3,
})
```

#### 1.3 Custom CSS Theme
**What:** Inject a unified CSS theme overriding Marimo defaults.
**Where:** New `@app.cell` near the top of `index.py`.
**Change:**
```python
@app.cell
def _(mo):
    mo.Html("""<style>
        :root {
            --primary: #1a3a4a;
            --accent-fishing: #3182bd;
            --accent-tourism: #de772a;
            --bg-card: #f8f9fa;
            --border-radius: 8px;
        }
        .marimo-tabs .tab-label {
            font-weight: 600;
            font-size: 14px;
            padding: 12px 24px;
        }
        h1, h2, h3 { color: var(--primary); }
        .marimo-accordion { border-radius: var(--border-radius); }
    </style>""")
    return
```

#### 1.4 Introduction Header
**What:** Add a styled intro section above the tabs.
**Where:** New `@app.cell` before the tab assembly cell (line ~3076).
**Change:**
```python
@app.cell
def _(mo):
    intro = mo.md("""
    # COOTEFOO Bias Investigation

    The Commission on Overseeing the Economic Future of Oceanus (COOTEFOO)
    has been accused of bias by both the fishing and tourism industries.
    Explore the evidence across three views: **sentiment patterns**,
    **travel behavior**, and **participation metrics**.
    """)
    header = mo.vstack([intro], align="center")
    return (header,)
```

---

### Phase 2: UX Polish (3-4 hours)

#### 2.1 "How to Read This Chart" Accordions
**What:** Add collapsible instruction panels at the top of each visualization tab.
**Where:** Each `visual1`, `visual2`, `visual3` definition.
**Change:** Wrap each visual in `mo.vstack` with `mo.accordion`:
```python
guide = mo.accordion({
    "How to read this chart": mo.md("""
    - **Blue** = pro-fishing sentiment, **Orange** = pro-tourism sentiment
    - Click a board member to lock their connections
    - Thicker edges indicate stronger sentiment
    - Center circle shows the board's average position
    """)
})
visual1 = mo.vstack([guide, existing_content])
```

#### 2.2 Tooltip Boundary Fix
**What:** Fix tooltips that overflow near window edges.
**Where:** `index.py`, the JavaScript `mousemove` handler (~line 3008-3017).
**Change:**
```javascript
seg.addEventListener('mousemove', (e) => {
    const pad = 15;
    const box = tooltip.getBoundingClientRect();
    let x = e.pageX + pad;
    let y = e.pageY + pad;
    if (x + box.width > window.innerWidth - pad)
        x = e.pageX - box.width - pad;
    if (y + box.height > window.innerHeight - pad)
        y = e.pageY - box.height - pad;
    if (x < pad) x = pad;
    if (y < pad) y = pad;
    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
});
```

#### 2.3 Plain-English Control Labels (Visual 2)
**What:** The KNN sliders are meaningless to non-technical users. Add descriptions.
**Where:** `index.py` lines 3050-3053.
**Change:**
```python
mo.vstack([
    mo.md("#### Controls"),
    mo.md("**Location Classification**"),
    mo.md("_How far to search for nearby zones:_"),
    mo.hstack([mo.md("Max distance (km)"), knn_dist_slider]),
    mo.md("_Number of neighbors to consider:_"),
    mo.hstack([mo.md("K neighbors"), knn_num_slider]),
    mo.md("---"),
    mo.md("**Display Options**"),
    mo.hstack([mo.md("Metric"), mode_dropdown]),
    show_others,
])
```

---

### Phase 3: Visual Presentation (4-6 hours)

#### 3.1 Responsive SVG Dimensions
**What:** Replace hardcoded pixel widths with `viewBox`-based SVGs.
**Where:** All SVG generation blocks + `mo.iframe()` calls.
**Change:**
```python
# Instead of: svg.SVG(width=800, height=height, elements=elements)
svg.SVG(width="100%", viewBox=f"0 0 800 {height}", elements=elements)

# Instead of: mo.iframe(..., width="1200px")
mo.iframe(..., width="100%")
```

#### 3.2 Key Findings Callouts
**What:** Embed text callout boxes below each visualization highlighting the main story.
**Where:** Below each visualization in the `visual1`/`visual2`/`visual3` assembly.
**Change:**
```python
findings = mo.callout(
    mo.md("""
    **Key finding:** Teddy Goldstein shows the strongest individual bias (pro-fishing, +0.72),
    while the board overall tilts slightly pro-tourism. The chair, Seal, remains nearly neutral.
    """),
    kind="info"
)
visual1 = mo.vstack([existing_content, findings])
```

#### 3.3 Summary Statistics Bar
**What:** A row of aggregate numbers above the tabs.
**Where:** New `@app.cell` between the intro and the tabs.
**Change:**
```python
@app.cell
def _(mo):
    stats = mo.hstack([
        mo.stat(value=6, label="Board Members"),
        mo.stat(value=47, label="Discussion Topics"),
        mo.stat(value=23, label="Plans Analyzed"),
        mo.stat(value=156, label="Trips Tracked"),
    ], justify="center", gap=2)
    return (stats,)
```

#### 3.4 Shared Constants Cell
**What:** Consolidate repeated color definitions into one place.
**Where:** New `@app.cell` near the top.
**Change:**
```python
@app.cell
def _():
    FOCUS_COLORS = {
        'fishing':  '#3182bd',
        'tourism':  '#de772a',
        'both':     '#756bb1',
        'other':    '#969696'
    }
    PERSON_COLORS = {
        'Carol Limpet': '#ff7f0e',
        'Ed Helpsford': '#9467bd',
        'Seal': '#8c564b',
        'Simone Kat': '#e377c2',
        'Tante Titan': '#1f77b4',
        'Teddy Goldstein': '#bcbd22'
    }
    return FOCUS_COLORS, PERSON_COLORS
```

---

### Extended: Future Improvements (Optional)

These tasks are lower priority or higher effort. Pursue after Phases 1-3 are stable.

#### Loading/Transition States
**What:** When filters change, the SVG re-renders can cause a brief flash. Add a fade transition.
**Where:** The `_CSS` block embedded in the iframe HTML.
**Change:**
```css
svg { transition: opacity 0.15s ease-in-out; }
.pie-group { transition: transform 0.2s ease; }
```

#### Cross-Tab Highlighting
**What:** When a user clicks a board member in one tab, highlight that member's data in the other tabs when the user switches.
**Where:** This requires a shared `mo.ui` state variable referenced across all three visualization cells.
**Change:** Create a shared `selected_person` reactive variable:
```python
@app.cell
def _(mo):
    selected_person = mo.ui.dropdown(
        options=["All"] + sorted(person_list),
        value="All",
        label="Focus on Member"
    )
    return (selected_person,)
```
Then reference `selected_person.value` in each visualization's filter/highlight logic.

#### Comparison Mode (Visual 1)
**What:** Allow side-by-side comparison of government data vs. journalist data in the sentiment map.
**Where:** Visual 1 cell (lines ~225-914), add a toggle that switches the data source.
**Change:**
1. Load both `database_gov.db` and `database_jour.db` data
2. Add a toggle: `data_source = mo.ui.radio(options=["Journalist Data", "Government Data", "Difference"], value="Journalist Data")`
3. Regenerate the SVG based on the selected source

#### Timeline Slider (Visual 1)
**What:** Add temporal filtering to the sentiment map so users can see how bias evolved over time.
**Where:** Visual 1 cell, add a date range slider that filters the `nodes` dataframe before aggregation.
**Change:** Filter `nodes` by date before the `groupby` aggregation at line ~360:
```python
date_range = mo.ui.range_slider(...)
filtered_nodes = nodes[(nodes['date'] >= start) & (nodes['date'] <= end)]
# then use filtered_nodes instead of nodes in the aggregation
```

#### Error Handling for Data Loading
**What:** Replace bare `try/except` blocks with specific exception handling and user-facing error messages.
**Where:** All data loading cells (lines ~81, ~209, ~924, ~933, ~1218, ~1240, ~1344).
**Change:**
```python
try:
    bias_persons = pd.read_json(str(mo.notebook_location() / "data" / "bias_persons.json"))
except FileNotFoundError:
    mo.output.append(mo.callout("Loading data from GitHub (local files not found)...", kind="warn"))
    bias_persons = pd.read_json(GITHUB_RAW_URL + "bias_persons.json")
except Exception as e:
    mo.stop(True, mo.callout(f"Failed to load data: {e}", kind="danger"))
```

---

## Execution Order

| Phase | Tasks | Effort | Dependencies |
|---|---|---|---|
| **Phase 1** | 1.1, 1.2, 1.3, 1.4 | 2-3 hours | None |
| **Phase 2** | 2.1, 2.2, 2.3 | 3-4 hours | Phase 1 (for color constants) |
| **Phase 3** | 3.1, 3.2, 3.3, 3.4 | 4-6 hours | Phase 2 |

**Total estimated effort:** 9-13 hours.

---

## Files to Modify

| File | Changes |
|------|---------|
| `index.py` | All tasks (single-file app) |
| `data/` | No changes needed (data is pre-processed) |

---

## How to Validate Each Change

1. Run `marimo run index.py` after each task
2. Check all three tabs render correctly
3. Test interactivity (hover, click, filter) on each tab
4. Verify WASM compatibility by testing with `marimo edit --sandbox index.py`
5. Test on at least two screen widths (1280px and 1920px)
6. Run through the three persona scenarios to ensure the narrative still holds

---

## What NOT to Change

- **Data files** -- the pre-processed JSON/CSV/GeoJSON files are stable
- **Data aggregation logic** -- pandas groupby/merge logic is well-tested
- **SVG glyph designs** -- the crown, halo, devil horns glyphs are distinctive
- **Marimo cell DAG structure** -- avoid introducing circular dependencies
- **KNN classification algorithm** -- the BallTree approach is correct
