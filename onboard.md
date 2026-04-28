# Onboarding Guide - DataViz1 (Veto Branch)

## What Is This Project?

This is an **interactive data visualization application** built for the [VAST Challenge 2025 (MC2)](https://vast-challenge.github.io/2025/). It investigates whether the government oversight board **COOTEFOO** (Commission on Overseeing the Economic Future of Oceanus) shows economic bias toward either the fishing or tourism industry in the fictional city of Saltmere/Oceanus.

Two advocacy groups have made opposing accusations:
- **FILAH** (Fishing is Living and Heritage) claims the board favors tourism over fishing.
- **TROUT** (Tourism Raises OceanUs Together) claims the board favors the entrenched fishing industry over emerging tourism.

The application provides three interactive visualizations to help three personas (a pro-fishing representative, a pro-tourism representative, and a neutral journalist) explore the evidence and form their own conclusions.

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | **Marimo** (reactive Python notebook, v0.23.3+) |
| Language | Python 3.13+ |
| Data Processing | pandas, polars, duckdb, numpy, scikit-learn |
| Visualization | **svg.py** (programmatic SVG generation), embedded JavaScript for interactivity |
| Deployment | Marimo WASM (runs in browser), GitHub Pages |
| Data Format | JSON, CSV, SQLite, GeoJSON |

There is **no npm/webpack build pipeline**. The entire application is a single Python file (`index.py`) that Marimo serves as a web application.

## Repository Structure

```
dataviz1-veto-branch/
├── index.py                 # The entire app (~3,086 lines, single Marimo notebook)
├── README.md                # Project background and persona descriptions
├── schema_diagram.png       # Database schema diagram
├── docs/
│   ├── CLAUDE.md            # Marimo notebook coding guidelines
│   └── manifest.json        # PWA manifest (Marimo branding)
└── data/
    ├── bias_persons.json    # Committee member sentiment bias scores
    ├── nodes.json           # Graph nodes (discussion/plan participation)
    ├── graph_2_1_data.json  # Personnel participation summary
    ├── graph_2_2_data.json  # Personnel participation details
    ├── places_edited.json   # Location data with coordinates
    ├── time_trip_spend.json # Travel/time data (largest file, ~423KB)
    ├── oceanus_map.geojson  # Geographic boundaries
    ├── people_participation_summary.json
    ├── people_participation_total.json
    ├── time_location_remapped.csv
    ├── database_gov.db      # Government-collected data (SQLite)
    ├── database_jour.db     # Journalist-collected data (SQLite)
    ├── checking.ipynb       # Exploratory analysis notebook
    ├── Collected_by_the_Government/   # Raw CSV data from the board
    │   ├── discussions.csv, meetings.csv, plans.csv, people.csv, ...
    │   └── schema.sql
    └── Collected_by_the_Journalist/   # Independent journalist data
        └── (same structure + trips.csv, trip_people.csv, trip_places.csv, topics.csv)
```

## The Three Visualizations

### Tab 1: Board Sentiment Bias Map
A circular hub-and-spoke network showing **who** on the board leans toward fishing vs. tourism. Board members are arranged in a ring around a center circle (aggregate sentiment). Edges connect members to discussion topics/plans, color-coded by sentiment (green = pro-fishing, red = pro-tourism). Click a member to lock their highlight.

### Tab 2: Board Visit Map and Time Spent
A geographic map with animated glyphs (boats, umbrellas, people) showing **where** board members traveled and how much time they spent. Includes KNN-based location classification sliders and a comparison mode toggle. Supports zoom/pan.

### Tab 3: Number of Topics, Meetings, Discussions and Plans
A participation matrix of pie charts showing **how much** each member engaged across four dimensions (topics, meetings, discussions, plans). Pie slices are colored by focus area (fishing/tourism/both/other). Checkbox filters let you isolate specific members or focus areas.

## How to Run Locally

```bash
# Install marimo (if not already installed)
pip install marimo

# Run the application
marimo run index.py

# Or open in edit mode (interactive notebook editor)
marimo edit index.py
```

The app will open in your browser. Data is loaded from the local `data/` folder; if files are missing, it falls back to fetching from the GitHub raw content URL.

## How the Code Is Organized

The entire app lives in `index.py` as a single Marimo notebook. Key sections:

| Lines (approx.) | Purpose |
|---|---|
| 1-55 | Imports, dependencies, micropip installs |
| 58-216 | Data loading (bias_persons.json, nodes.json) with GitHub fallback |
| 225-914 | **Visualization 1**: SVG sentiment map (custom classes, glyphs, edges, JS interactivity) |
| 915-3066 | **Visualization 2**: Geographic map (GeoJSON, SVG glyphs, zoom/pan JS) |
| (interleaved) | **Visualization 3**: Participation pie-chart matrix with checkbox filters |
| 3076-3086 | Tab assembly (`mo.ui.tabs`) and `app.run()` |

### Key patterns in the code:
- **Custom SVG classes** (`DataRect`, `DataPolygon`, `DataG`) extend svg.py to inject `data-*` attributes via regex for JavaScript interactivity.
- **Glyph functions** (`person_glyph`, `king_crown`, `queen_crown`, `chest`, `halo`, `devil_horns`) draw board member icons with role indicators.
- **Embedded JavaScript** handles hover/click interactions, blur effects, tooltip positioning, and map zoom/pan.
- **Data fallback**: `try/except` blocks attempt local file reads first, then fall back to GitHub raw content URLs.

## How to Contribute (Pull Request Workflow)

### 1. Fork and Clone
```bash
git clone https://github.com/<your-username>/dataviz1-veto-branch.git
cd dataviz1-veto-branch
```

### 2. Create a Feature Branch
```bash
git checkout -b feature/your-improvement-name
```

### 3. Make Your Changes
- Edit `index.py` for visualization changes.
- Follow Marimo conventions: only edit code inside `@app.cell` decorated functions.
- Do not redeclare variables across cells (Marimo enforces DAG structure).
- Test locally with `marimo run index.py` before committing.

### 4. Test Your Changes
```bash
# Run the app and verify in browser
marimo run index.py

# Optional: run marimo's linter
marimo check --fix index.py
```

### 5. Commit and Push
```bash
git add index.py  # (and any new data files if needed)
git commit -m "feat: describe your change concisely"
git push origin feature/your-improvement-name
```

### 6. Open a Pull Request
- Go to the repository on GitHub.
- Click "New Pull Request" and select your branch.
- Describe **what** you changed and **why**.
- Include screenshots or GIFs of visual changes if applicable.

### Important Notes for Contributors
- The app is a **single file** (`index.py`). All visualization logic, data processing, and interactivity live here.
- SVG elements are generated programmatically with Python (`svg.py`) and made interactive with embedded JavaScript.
- Data attributes (`data-fill`, `data-people`, `data-topic`, etc.) bridge the Python-generated SVG and the JavaScript interaction layer.
- The app must work both locally and in **WASM mode** (browser-only, no filesystem access), which is why GitHub raw content fallback URLs exist.
- Be careful with imports: some packages are installed via `micropip` for WASM compatibility.

## Data Model Overview

Two parallel datasets exist:
- **Government-collected**: Official records of meetings, discussions, plans, and participants.
- **Journalist-collected**: Independent data with the same schema plus additional trip/travel records.

Differences between the two datasets are central to the analysis -- they reveal potential gaps or discrepancies in government reporting.

### Key entities:
- **People**: 6 board members with roles (chair, vice-chair, treasurer, members)
- **Discussions/Plans**: Decisions and proposals with associated topics and sentiment scores
- **Topics**: Subject areas tied to fishing or tourism industries
- **Trips**: Travel records (journalist data only) showing where members went

Sentiment is scored as: positive = pro-fishing, negative = pro-tourism, with the sign flipped for tourism-industry discussions to create a unified bias axis.

## Quick Reference

| Task | Command |
|---|---|
| Run the app | `marimo run index.py` |
| Edit interactively | `marimo edit index.py` |
| Lint/fix | `marimo check --fix index.py` |
| Live demo | [tvakul.github.io/dataviz1](https://tvakul.github.io/dataviz1/) |
| Original repo | [github.com/tvakul/dataviz1](https://github.com/tvakul/dataviz1) |
