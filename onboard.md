# COOTEFOO Board Investigation Dashboard — Interaction Guide

VAST Challenge 2025 MC2 — Four interactive dashboards investigating the COOTEFOO board's activities across government and journalist records.

## Quick start

```bash
uv run marimo run index.py
```

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/). `uv run` reads the inline `# /// script` dependency block and handles dependencies automatically.

All 4 dashboards load in a single app with tab navigation along the top.

---

## Dashboard guide

### Sentiment Map (tab 1)

Radial network showing each board member's sentiment toward fishing and tourism topics.

- **Hover a person glyph** to see their connections to topic clusters. Other people blur out, edges appear, and sentiment scores update per-topic.
- **Click a person** to lock the view. Click again or click empty space to unlock.
- **Hover a discussion/plan node** (pentagon = discussion, square = plan) to see which people participated.
- **Reason panel** appears at the bottom with the person's stated reasons for each position.
- Red-glowing nodes with dashed borders = data missing from government records.

### Visit Map (tab 2)

Three-panel view: shoreline bias chart (top), geographic map (bottom-left), radial trip timeline (bottom-right).

- **Click a person figure** on the shoreline to filter the map and timeline to that person. Click again to unlock.
- **Scroll-wheel on the map** to zoom. Drag to pan when zoomed in. Use +/-/R buttons.
- **Hover any colored dot** on the map or timeline for a formatted tooltip.
- **Sidebar controls**: KNN distance/neighbors adjust how commercial/residential zones get reclassified as fishing or tourism. Toggle between visit count and time spent modes.
- **Date range slider** filters all three panels to a time window.

### Participation (tab 3)

Bubble matrix with pie charts showing participation volume.

- Rows = people, columns = metrics (topics, meetings, discussions, plans).
- Circle size = total count. Pie slices = focus type (fishing/tourism/both/other).
- **Hover a pie** for a breakdown tooltip.
- **Checkboxes** on the right to filter people and focus types.

### The Committee (tab 4)

Sentiment constellation + trip ribbon — a full-page interactive React dashboard.

**Constellation view** (left): six board members in a small inner ring on the left, fifteen topics arranged on a right-side arc (or grouped columns). Edges connect people to the topics they've weighed in on.

- **Edge color** encodes sentiment: red = opposed, neutral = straw, green = in favor.
- **Edge weight** encodes conviction (absolute sentiment value).
- **Halo size** around each member = number of topics they've opined on.
- **Hover a person** to reveal their topic connections (all other edges hidden). The right rail shows their stats, ranked stances, alignment with other members, and a quoted reason.
- **Hover a topic** to see which members participated. The right rail shows voices, meetings, industries, and a representative quote.
- **Click any node** to pin the selection. Click again or press **Esc** to release.
- **Constellation / Cluster toggle** (top-right): switch between arc layout and grouped-column layout.

**Right rail**: contextual detail panel that updates on hover/click. Shows briefing overview, per-member stats, or per-topic breakdown.

**Trip ribbon** (bottom): horizontal dot timeline showing all 536 field trips across Mar-Aug 2040.

- Each **row** is one person (sorted by trip count).
- **Dot size** = number of stops on the trip.
- **Hover a dot** for trip details (date, time, stops, places visited).
- **Click a dot** to focus the constellation on that traveler.

---

## Architecture

```
index.py              # Main app — all 4 dashboards in tabs
_build_d1.py          # D1 SVG builder (sentiment map)
_build_d2.py          # D2 SVG builder (visit map)
_build_d3.py          # D3 SVG builder (participation matrix)
_build_d4.py          # D4 SVG+JS builder (constellation + trip ribbon)
dashboard_*.py        # Standalone versions (can run individually)
plan/Claude-Design/   # Original design reference (app.jsx, styles.css)
data/                 # All source data
  Collected_by_the_Government/   # 18 CSVs, 13 meetings
  Collected_by_the_Journalist/   # 18 CSVs, 16 meetings (superset)
  cleaned_data/                  # Merged tables + data.js for D4
  *.json, *.geojson              # Pre-computed data for D1-D3
notebook/             # Data investigation Jupyter notebook
plan/                 # Improvement plans and peer reviews
docs/                 # CLAUDE.md project instructions
```

`index.py` handles data loading, UI controls, and tab composition. All four dashboards use `_build_d*.py` modules — pure Python functions that generate self-contained HTML (SVG + inline CSS + vanilla JS) rendered via `mo.iframe()`.

Dashboards 1-3 load pre-computed JSON. Dashboard 4 loads `data/cleaned_data/data.js` containing the full sentiment matrix, trips, discussions, and reason text.
