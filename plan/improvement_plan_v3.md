# Improvement Plan v3 — Rebuilding Dashboards 4-6

Replaces the current dashboards 4-6, which were reviewed as "mostly static summaries, not investigative tools." This plan draws analytical threads from dashboards 1-3 and extends them into dimensions those views cannot reach.

---

## What dashboards 1-3 already cover

| Dashboard | Core strength | Blind spots |
|-----------|--------------|-------------|
| D1 — Sentiment map | Per-person sentiment polarity on fishing/tourism topics; participation links; reason text tooltips | Static aggregate. No temporal dimension. No pairwise person comparison. |
| D2 — Trip analyzer | Geographic visit patterns; fishing/tourism zone bias per person; temporal radial chart; KNN reclassification | Individual trips only. No co-travel detection. No link between trip destinations and meeting agenda. |
| D3 — Participation matrix | Participation volume by person x metric (topics, meetings, discussions, plans); focus-type pie breakdown | Counts only. No sentiment overlay. No temporal ordering. No outcome tracking. |

Three analytical gaps remain:

1. **Temporal dynamics** — How did positions evolve across the 16 meetings? Who shifted, who hardened? D1 is a snapshot; the story is in the arc.
2. **Relational structure** — Who aligns with whom? Which person-organization pairs share suspiciously similar sentiment profiles? D1 shows individuals in isolation.
3. **Action vs. rhetoric** — Which discussions produced results? How many plans completed vs. stalled? D3 counts participation but not outcomes. The trip data (D2) shows where people went, but not whether those trips connected to agenda items.

---

## Design principles (informed by GPT-5.5 review of v2)

These address the concrete failures identified in `claude_code_latest_dashboards_peer_review.md`:

| Principle | Rationale |
|-----------|-----------|
| **Every aggregate must be drillable.** | The v2 review's central criticism: "static summaries, not investigative tools." Every chart cell, bar segment, or node must reveal its underlying records on click. |
| **Use SVG for pattern, HTML for evidence.** | SVG is good for layout and interaction. Reason text, participation details, and omission records belong in `mo.ui.table` or styled HTML panels beside the chart. |
| **Unknown sentiment = gray `?`, not invisible.** | Null sentiment was silently dropped in v2. It may indicate incomplete source collection around sensitive topics. |
| **Label metrics honestly.** | If it's a final-status distribution, don't call it a funnel. If alignment requires 3+ shared topics, say "insufficient data" below that threshold. |
| **Journalist is canonical superset.** | Left-join government onto journalist. Never the reverse. |
| **Normalize at load time.** | Lowercase `plan_type`, `status`. Parse sentiment as float with null preservation. Sort meetings by numeric suffix of `meeting_id`, not the `date` column. |
| **Keep data prep and rendering in separate cells.** | The existing v2 data-loading cell (`jour`, `gov`, normalization) is correctly structured. Reuse it. |

---

## New Dashboard 4 — Sentiment Evolution Timeline

### Question

> "How did each person's stance evolve across meetings? Who shifted, who hardened, and on which topics did the committee converge or diverge?"

### Why dashboards 1-3 can't answer this

D1 shows average sentiment per person per topic across all meetings. It cannot distinguish a person who was always +0.5 from one who went from -1.0 to +1.0. D3 counts participation but has no sentiment axis. D2 is geographic, not topical.

### Layout

```
+--------------------------------------------------------------+
|  CONTROLS                                                     |
|  [Person filter: multiselect]  [Topic filter: All / specific] |
+--------------------------------------------------------------+
|  TIMELINE CHART (main, ~70% height)                           |
|                                                               |
|  Y-axis: sentiment (-1 to +1)                                |
|  X-axis: meetings M1..M16                                     |
|                                                               |
|  One line per selected person, colored by person.             |
|  Each point = avg sentiment for that person's participations  |
|  in discussions/plans at that meeting for the selected topic. |
|                                                               |
|  Point size = number of participations at that meeting.       |
|  Dashed point border = journalist-only (gov data missing).    |
|                                                               |
|  Click a point -> detail panel shows discussion titles,       |
|  plan titles, individual sentiment scores, reason text.       |
|                                                               |
|  Band overlay: light green/red shading shows committee-wide   |
|  sentiment range (min to max across all persons per meeting). |
|                                                               |
+--------------------------------------------------------------+
|  DETAIL PANEL (bottom, scrollable HTML)                       |
|  Selected meeting + person + topic:                           |
|  - Discussion title, sentiment, reason text                   |
|  - Plan title, plan_type, status, sentiment, reason text      |
|  - "Gov data missing" badge where applicable                  |
+--------------------------------------------------------------+
```

### Data pipeline

```python
# Per-meeting, per-person, per-topic sentiment:
meeting_disc = jour["meeting_discussions"]
disc_topics = jour["discussion_topics"]
disc_people = jour["discussion_people_participations"]

timeline_sent = (
    meeting_disc
    .merge(disc_topics, on="discussion_id")
    .merge(disc_people, on="discussion_id")
    .merge(jour["meetings"][["meeting_id", "meeting_order"]], on="meeting_id")
)

# Add plan participations via meeting_plans:
meeting_plans = jour["meeting_plans"]
plan_topics = jour["plan_topics"]
plan_people = jour["plan_people_participations"]

plan_sent = (
    meeting_plans
    .merge(plan_topics, on="plan_id")
    .merge(plan_people, on="plan_id")
    .merge(jour["meetings"][["meeting_id", "meeting_order"]], on="meeting_id")
)

# Combine and aggregate:
all_sent = pd.concat([
    timeline_sent[["meeting_order", "topic_id", "people_id", "sentiment", "discussion_id"]]
        .rename(columns={"discussion_id": "item_id"}).assign(item_type="discussion"),
    plan_sent[["meeting_order", "topic_id", "people_id", "sentiment", "plan_id"]]
        .rename(columns={"plan_id": "item_id"}).assign(item_type="plan"),
])

person_meeting_topic = (
    all_sent.groupby(["meeting_order", "topic_id", "people_id"])
    .agg(avg_sentiment=("sentiment", "mean"),
         count=("sentiment", "size"),
         null_count=("sentiment", lambda x: x.isna().sum()))
    .reset_index()
)
```

### Interactions

- **Hover line point**: show tooltip with person name, meeting, avg sentiment, participation count.
- **Click line point**: populate detail panel with all participation records (discussion/plan titles, sentiments, reason text).
- **Click person in legend**: toggle that person's line on/off.
- **Topic filter**: re-aggregates the data for the selected topic only (or all topics).
- **Gov-missing badge**: dashed circle border on points where the underlying participation is journalist-only.

### SVG approach

- Lines: `<polyline>` per person with `stroke` = person color.
- Points: `<circle>` with `r` = sqrt(count) scaled, `fill` = sentiment color, `stroke-dasharray` for gov-missing.
- Band: `<path>` with `fill-opacity=0.08` showing min-max envelope.
- X-axis labels: M1..M16 positioned by meeting_order.
- Detail panel: `mo.ui.table` below the SVG, populated reactively on click via a marimo state variable.

### Key insight this enables

Identifying **position shifts**: if Teddy Goldstein's sentiment on `affordable_housing` goes from +1.0 at M6 to -1.0 at M9, that's a story. The committee-wide band reveals whether this was an individual shift or a collective one.

---

## New Dashboard 5 — Person-Topic Heatmap with Drilldown

### Question

> "What is the complete sentiment fingerprint of each committee member? Where do they agree, where do they clash, and what are their stated reasons?"

### Why dashboards 1-3 can't answer this

D1's radial layout makes pairwise comparison difficult. The user has to click each person separately and mentally compare. D3 shows volume, not sentiment. There's no single view that lets you scan all 6 people x 15 topics and immediately see the conflict structure.

### Layout

```
+--------------------------------------------------------------+
|  HEATMAP (main, ~60% height)                                  |
|                                                               |
|  Rows: 6 people (sorted by overall avg sentiment)            |
|  Cols: 15 topics (grouped: fishing-related | tourism-related |
|                   | neutral/both)                             |
|                                                               |
|  Cell: colored rectangle                                      |
|    Fill = avg sentiment (green positive, red negative,        |
|           gray = no participation, striped gray = unknown)    |
|    Border width = participation count (thicker = more active) |
|    Dashed border = some records journalist-only               |
|                                                               |
|  Row header: person name + overall avg sentiment badge        |
|  Col header: topic name + topic group color bar               |
|                                                               |
|  Click a cell -> detail panel + highlight column/row          |
|                                                               |
+--------------------------------------------------------------+
|  AGREEMENT MATRIX (bottom-left, ~40% width)                   |
|                                                               |
|  6x6 pairwise person agreement scores                        |
|  Cell = Pearson r of sentiment vectors across shared topics   |
|  Color = green (allies), red (opponents), gray (< 3 shared)  |
|  Click a cell pair -> highlights their matching/clashing      |
|  topics in the heatmap above                                  |
|                                                               |
+--------------------------------------------------------------+
|  REASON PANEL (bottom-right, ~60% width)                      |
|                                                               |
|  Selected person + topic:                                     |
|  - All discussion participations with sentiment + reason      |
|  - All plan participations with sentiment + reason            |
|  - Gov/journalist data source flag per record                 |
|  - Organization participation in same topic (for context)     |
|                                                               |
+--------------------------------------------------------------+
```

### Data pipeline

```python
# Person x Topic sentiment matrix (already partially computed in D1):
person_topic_matrix = (
    all_sent[all_sent["sentiment"].notna()]
    .groupby(["people_id", "topic_id"])
    .agg(avg_sentiment=("sentiment", "mean"),
         count=("sentiment", "size"))
    .reset_index()
    .pivot(index="people_id", columns="topic_id", values="avg_sentiment")
)

# Pairwise agreement:
from itertools import combinations
agreements = []
for p1, p2 in combinations(people_ids, 2):
    v1 = person_topic_matrix.loc[p1].dropna()
    v2 = person_topic_matrix.loc[p2].dropna()
    shared = v1.index.intersection(v2.index)
    if len(shared) >= 3:
        r = np.corrcoef(v1[shared], v2[shared])[0, 1]
        agreements.append({"p1": p1, "p2": p2, "r": r, "shared": len(shared)})
```

### Interactions

- **Hover cell**: tooltip with person, topic, avg sentiment, count, null count.
- **Click cell**: populate reason panel. Highlight row and column with accent border.
- **Click agreement cell**: highlight the two people's rows in the heatmap, and color-code their matching/clashing topics.
- **Sort toggle**: sort topics by fishing/tourism grouping (default) or by variance (most contested first).

### SVG approach

- Heatmap: `<rect>` grid with `fill` = sentiment color, `stroke-width` proportional to count.
- Agreement matrix: `<rect>` grid with color scale from red (-1) through gray (0) to green (+1).
- Both grids use data-attributes for hover/click interactivity.
- Reason panel: `mo.ui.table` populated reactively.

### Key insight this enables

The **conflict structure** becomes immediately visible. You can see at a glance that Teddy Goldstein and Simone Kat are anti-correlated across fishing/tourism topics, while Carol Limpet is moderate everywhere. The agreement matrix quantifies these alliances.

---

## New Dashboard 6 — Plan Outcome Tracker

### Question

> "Which plans actually produced results? What's the conversion rate from 'introduced' to 'completed', and where did plans stall?"

### Why dashboards 1-3 can't answer this

D3 counts plans per person but doesn't track their status progression. D1 shows sentiment on plans but not whether those plans succeeded. D2's trip data could connect to plan-related travel, but that link isn't made.

### Layout

```
+--------------------------------------------------------------+
|  CONTROLS                                                     |
|  [Topic filter: All / specific]                               |
|  [Plan type filter: All / proposal / report / travel / ...]   |
|  [Show gov-missing: toggle]                                   |
+--------------------------------------------------------------+
|  SWIM LANE TIMELINE (main, ~55% height)                       |
|                                                               |
|  Y-axis: topics (one row per topic)                           |
|  X-axis: meetings M1..M16                                     |
|                                                               |
|  Each topic row contains:                                     |
|  - Small circles for discussion presence (colored by          |
|    avg participant sentiment)                                  |
|  - Plan progression arcs: horizontal bars from first meeting  |
|    to last meeting where the plan appears.                    |
|    Color = final status (gray=introduced, yellow=planned,     |
|    blue=in_progress, green=completed)                         |
|    Status badges at each transition point.                    |
|    Gov-missing plans get red dashed outline.                  |
|                                                               |
|  Click a plan arc -> detail panel                             |
|  Click a discussion circle -> detail panel                    |
|                                                               |
+--------------------------------------------------------------+
|  STATUS FUNNEL (bottom-left, ~30% width)                      |
|                                                               |
|  Cumulative: how many plans reached each stage                |
|  introduced: 74 (100%)                                        |
|  planned:    72 (97%)  -- 2 never advanced                    |
|  in_progress: 53 (72%) -- 19 stalled at planned              |
|  completed:  46 (62%)  -- 7 stalled at in_progress           |
|                                                               |
|  Trapezoid shape, sized by count. Drop-off shown.             |
|                                                               |
+--------------------------------------------------------------+
|  PLAN TYPE x STATUS MATRIX (bottom-center, ~30% width)        |
|                                                               |
|  Rows: plan_type (proposal, report, travel, etc.)            |
|  Cols: final status (introduced..completed)                   |
|  Cell = count. Color intensity by cell value.                |
|  Answers: do proposals complete more than reports?            |
|                                                               |
+--------------------------------------------------------------+
|  DETAIL PANEL (bottom-right, ~40% width)                      |
|                                                               |
|  Selected plan:                                               |
|  - Plan title, type, topic                                    |
|  - Status history: meeting_id + status at each appearance     |
|  - Participant sentiments + reason text                       |
|  - Related discussions                                        |
|  - Travel links (place names from travel_links)               |
|  - Gov-missing flag                                           |
|                                                               |
+--------------------------------------------------------------+
```

### Data pipeline

```python
# Plan lifecycle with per-meeting status:
disc_plans = jour["discussion_plans"]
STATUS_ORDER = {"introduced": 0, "planned": 1, "in_progress": 2, "completed": 3}
disc_plans["status_rank"] = disc_plans["status"].map(STATUS_ORDER)

# Join to get meeting context:
plan_at_meeting = (
    disc_plans
    .merge(jour["meeting_discussions"], on="discussion_id")
    .merge(jour["meetings"][["meeting_id", "meeting_order"]], on="meeting_id")
    .dropna(subset=["status_rank"])
    .sort_values("meeting_order")
    .groupby(["plan_id", "meeting_order"])
    .agg(best_rank=("status_rank", "max"))
    .reset_index()
)

# Cumulative funnel (not final-status distribution):
all_plans_max_rank = disc_plans.groupby("plan_id")["status_rank"].max()
for rank, label in STATUS_ORDER.items():
    reached = (all_plans_max_rank >= STATUS_ORDER[label]).sum()
    # -> this gives the correct funnel: 74 -> 72 -> 53 -> 46

# Plan type x status cross-tab:
plan_type_status = (
    jour["plans"][["plan_id", "plan_type"]]
    .merge(all_plans_max_rank.reset_index().rename(columns={"status_rank": "max_rank"}),
           on="plan_id")
)
```

### Interactions

- **Click plan arc**: populate detail panel with full plan history.
- **Click discussion circle**: show discussion participants and sentiment.
- **Topic filter**: reduce to one topic's swim lane.
- **Plan type filter**: dim plans not matching the selected type.
- **Gov-missing toggle**: highlight/dim plans absent from government data.
- **Hover funnel segment**: tooltip with stage, count, percentage, drop-off from previous.

### SVG approach

- Swim lanes: horizontal `<line>` per topic, `<circle>` for discussions, `<rect>` bars for plan spans.
- Plan arcs: `<rect>` from first to last meeting_order, `fill` = final status color.
- Status badges: small `<circle>` or `<polygon>` at each meeting where status changed.
- Funnel: trapezoid `<polygon>` elements with decreasing widths, labeled with count + percentage + drop-off.
- Type x status matrix: `<rect>` grid, same pattern as D5's heatmap.
- Detail panel: `mo.ui.table` populated reactively.

### Key insight this enables

62% of plans completed. But **which topics stall**? If fishing-related plans complete at 80% while tourism proposals stall at 40%, that tells a story about power dynamics. The plan type breakdown reveals whether the issue is structural (e.g., "travel" type plans always complete because they're just site visits) or political.

---

## Cross-cutting: data layer improvements

The existing v2 data-loading cell (`jour`, `gov`, normalization at line ~3136) is correctly structured. These additions should be separate cells downstream:

### 1. `participation_reasons` DataFrame (already built in v2, keep it)

Used by D4 detail panel, D5 reason panel, and D6 detail panel.

### 2. `gov_coverage_flags` DataFrame (new)

```python
# For each participation row in journalist, flag whether government has it:
for table, keys in COMPARABLE_TABLES.items():
    jour[table]["in_gov"] = jour[table].merge(
        gov[table][keys].drop_duplicates().assign(_g=True),
        on=keys, how="left"
    )["_g"].fillna(False)
```

Used as dashed-border indicator across all three dashboards.

### 3. Topic grouping reference

```python
FISHING_TOPICS = {"fish_vacuum", "deep_fishing_dock", "new_crane_lomark", "low_volume_crane", "affordable_housing"}
TOURISM_TOPICS = {"expanding_tourist_wharf", "heritage_walking_tour", "marine_life_deck", "seafood_festival", "waterfront_market", "statue_john_smoth"}
NEUTRAL_TOPICS = {"concert", "renaming_park_himark", "name_harbor_area", "name_inspection_office"}
```

Used for column ordering in D5 heatmap and color-coding across dashboards.

---

## Implementation sequence

### Phase 1 — Shared data layer + Dashboard 5 (Person-Topic Heatmap)

**Why first**: The person-topic sentiment matrix is the simplest new computation. It validates the data pipeline and gives immediate analytical value. The pairwise agreement matrix is a direct extension.

Steps:
1. Build `person_meeting_topic` aggregation (reused by D4 and D5).
2. Build `gov_coverage_flags`.
3. Implement D5: heatmap SVG + agreement matrix SVG + reason panel wiring.
4. Add topic grouping (fishing/tourism column headers).
5. Add click interactions and detail panel.
6. Replace existing dashboard 5 tab.

### Phase 2 — Dashboard 4 (Sentiment Evolution Timeline)

**Why second**: Uses the same `person_meeting_topic` data but adds the temporal axis. Building it second avoids duplicating the aggregation work.

Steps:
1. Aggregate person_meeting_topic into time series per person per topic.
2. Implement line chart SVG with committee-wide sentiment band.
3. Add person toggle, topic filter, meeting-level detail panel.
4. Add gov-missing dashed borders on individual data points.
5. Replace existing dashboard 4 tab.

### Phase 3 — Dashboard 6 (Plan Outcome Tracker)

**Why third**: Requires the most complex data joins (plan lifecycle across meetings) and benefits from the interaction patterns established in Phases 1-2.

Steps:
1. Build plan lifecycle: per-plan status at each meeting.
2. Build cumulative funnel (not final-status distribution).
3. Build plan_type x status cross-tab.
4. Implement swim lane SVG with plan arcs and status badges.
5. Implement funnel + type-status matrix SVG.
6. Wire detail panel with plan history, participants, travel links.
7. Replace existing dashboard 6 tab.

### Phase 4 — Polish and validation

1. Visual consistency: match warm palette from D1-D3 (cream background `#FDF8F4`, warm gray labels `#8A7E74`, brown text `#3D3229`).
2. Interaction consistency: same click-to-lock, hover-to-preview pattern as D1 and D2.
3. Remove the 3 existing static dashboards (4-6) once replacements are complete.
4. Run `marimo check --fix`.
5. Smoke-test all 6 tabs in browser.

---

## What this plan does NOT include

- **Geographic overlays on the map** (linking discussion places to the D2 map). Good idea, but adds complexity without a clear investigative payoff. Save for v4.
- **Network graph of person-organization relationships**. The org data has only 8 organizations with sparse participation. A matrix (D5's agreement panel) serves better than a force-directed graph.
- **Automated anomaly detection**. The dataset is small enough (6 people, 15 topics, 16 meetings) that pattern recognition should be visual, not algorithmic.

---

## Constraints

- **No new visualization libraries.** Continue with `svg.py` + hand-coded JavaScript + `mo.ui` HTML elements.
- **Reuse the existing data-loading cell.** Don't duplicate CSV loading or normalization.
- **Maintain the tab interface.** New dashboards replace existing tabs 4-6, keeping the total at 6.
- **Null sentiment = unknown, not zero.** Gray striped cells in heatmaps, `?` labels, excluded from averages but counted in participation totals.
- **Sort meetings by numeric ID suffix**, not by the `date` column.
- **Detail panels use `mo.ui.table`**, not SVG text. SVG is for patterns; HTML tables are for reading reason text and auditing records.
