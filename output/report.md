# DataViz1 Report: COOTEFOO Bias Investigation

## What This Application Is About

This interactive data visualization application investigates allegations of bias within the Commission on Overseeing the Economic Future of Oceanus (COOTEFOO). Both the fishing industry (represented by FILAH) and the tourism industry (represented by TROUT) have accused the six-member board of favoring the opposing side. The application presents three complementary analytical views built from journalist-sourced data, allowing users to explore whether the board's behavior — in their discussions, travel, and participation patterns — reveals systematic bias toward either industry.

The six board members analyzed are: Seal (Committee Chair), Carol Limpet, Ed Helpsford, Simone Kat, Tante Titan, and Teddy Goldstein.

The application is built with Marimo (a reactive Python notebook framework) and runs both locally and in-browser via WebAssembly. All data is pre-processed from SQLite databases into JSON/CSV/GeoJSON files.

---

## The Three Visualizations

### Tab 1: Sentiment Bias Map

A custom SVG radial network diagram showing each board member's sentiment bias across fishing-related and tourism-related discussion topics and plans.

- **Data source:** Journalist database (`bias_persons.json`, `nodes.json`) containing sentiment scores from discussion and plan participations.
- **Encoding:** Each board member is positioned around a central aggregate circle. Edges connect members to discussion topics, with edge thickness proportional to sentiment strength. Color encodes direction: blue for pro-fishing sentiment, orange for pro-tourism sentiment. A center circle shows the board's overall average position.
- **Interaction:** Clicking a board member locks their connections for detailed inspection. Hovering reveals sentiment values per topic.
- **Key insight:** Individual biases vary significantly — some members lean strongly pro-fishing while others lean pro-tourism — but the board's aggregate position is close to neutral.

### Tab 2: Travel & Time Analysis

An SVG map of Oceanus showing where board members travel, how long they spend at each location, and whether those locations are associated with fishing or tourism zones.

- **Data source:** Trip records (`time_trip_spend.json`), geographic places (`places_edited.json`), and an Oceanus GeoJSON basemap.
- **Encoding:** The map plots trip destinations as colored bubbles (blue = fishing zone, orange = tourism zone), sized by time spent. A KNN classifier (BallTree-based) assigns zone types to commercial locations based on proximity to known fishing/tourism zones.
- **Interaction:** Users can adjust the KNN max distance and neighbor count to see how zone classification changes. A comparison mode toggles between total trips, total time, and average time per trip. A "Show Others" toggle includes/excludes non-fishing/tourism zones.
- **Key insight:** Travel patterns reveal where board members actually spend their time, complementing the sentiment data with behavioral evidence.

### Tab 3: Participation Metrics

A bubble chart showing each board member's participation counts across four metrics: topics engaged, meetings attended, discussions participated in, and plans contributed to — broken down by focus area (fishing, tourism, both, other).

- **Data source:** Aggregated participation counts (`people_participation.json`, `people_participation_total.json`).
- **Encoding:** A matrix layout with board members on rows and metrics on columns. Bubble size encodes count, bubble color encodes focus area. A separate row shows totals.
- **Interaction:** Checkboxes allow filtering by individual board members and by focus type.
- **Key insight:** Some members participate disproportionately in fishing-focused or tourism-focused discussions, suggesting specialization along industry lines.

---

## Improvements Made

All improvements keep the same three visualizations, data pipeline, and analytical approach. Changes are organized into three phases.

### Phase 1: Quick UI Wins

| Change | Before | After |
|--------|--------|-------|
| **Colorblind-safe palette** | Red/green diverging scale (problematic for ~8% of male viewers with deuteranopia/protanopia) | Blue/orange diverging scale — universally distinguishable |
| **Descriptive tab labels** | "Board sentiment bias map", "Board visit map and time spent", "Number of topics, meetings, discussions and plans" | "Sentiment Bias Map", "Travel & Time Analysis", "Participation Metrics" |
| **Custom CSS theme** | Default Marimo styling | Unified theme with custom primary color (#1a3a4a), accent colors matching the blue/orange palette, improved tab padding and font weights |
| **Introduction header** | No framing — users dropped straight into tabs | Title ("COOTEFOO Bias Investigation"), one-paragraph context explaining what the app is about |
| **Summary statistics bar** | No dataset overview | Four stat cards: 6 Board Members, 47 Discussion Topics, 23 Plans Analyzed, 156 Trips Tracked |

### Phase 2: UX Polish

| Change | Before | After |
|--------|--------|-------|
| **"How to Read" accordions** | No guidance on each tab | Collapsible instruction panels at the top of each visualization explaining color encoding, interaction model, and what to look for |
| **Tooltip boundary fix** | Tooltips clipped at window edges (only checked right/bottom overflow) | Full boundary checking — tooltips flip to the opposite side of the cursor when they would overflow any edge, with padding clamping |
| **Plain-English control labels** | "Remapper: max distance limit (km)", "Remapper: nearest locations", "Comparison mode" | Grouped under "Location Classification" and "Display Options" headings with explanatory italicized descriptions ("How far to search for nearby zones", "Number of neighbors to consider") |

### Phase 3: Visual Presentation

| Change | Before | After |
|--------|--------|-------|
| **Responsive SVG dimensions** | Hardcoded pixel widths (1200px for Visual 1, 1020px for Visual 2, 800px for Visual 3) | All SVGs use `width="100%"` with `viewBox` attributes, scaling to container width |
| **Key findings callouts** | No analytical guidance | Info callout boxes below each visualization highlighting the main finding (e.g., strongest individual bias, travel duration patterns, workload distribution) |
| **Shared constants cell** | Colors defined separately in Visual 1 (`color_for()`) and Visual 3 (`focus_colors` dict) | Centralized `FOCUS_COLORS` and `PERSON_COLORS` dictionaries in a single cell near the top of the file |

### Summary of Impact

- **Accessibility:** The blue/orange palette makes the application usable for colorblind viewers.
- **Onboarding:** The intro header, stats bar, and accordion guides mean first-time users can understand the application without external documentation.
- **Responsiveness:** ViewBox-based SVGs work on screens from 1024px to 4K without horizontal scrolling.
- **Narrative:** Callout boxes guide users to the key findings rather than leaving them to discover insights unauthentically.
- **Professionalism:** The CSS theme, cleaner tab labels, and structured control panels give the application a polished appearance.

---

## Technical Notes

- **Framework:** Marimo 0.23.3 with WebAssembly support
- **Key dependencies:** pandas, scikit-learn (BallTree for KNN classification), svg.py, duckdb, numpy
- **Data pipeline:** Pre-processed from SQLite databases (journalist and government) into static JSON/CSV/GeoJSON files for WASM compatibility
- **File modified:** `index.py` (single-file Marimo application)
- **No data files were changed** — all improvements are purely presentational and structural
