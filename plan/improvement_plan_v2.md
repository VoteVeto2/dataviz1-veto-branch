# Improvement Plan v2 — Three New Dashboards

Incorporates corrections from the GPT-5.5 peer review of v1. The core finding: the government dataset is a **subset** of the journalist dataset. Shared rows match exactly; the difference is missing coverage, not changed values. This reframes the investigative angle from "who disagrees" to "what did the government omit."

---

## Decisions

**Three new dashboards** added to the existing tabbed interface (bringing the total to six). One cross-cutting enhancement applied to the existing Dashboard 1.

| New | Dashboard | Core question |
|-----|-----------|---------------|
| 4 | **Source Coverage Gap Detector** | What did the government leave out? |
| 5 | **Meeting Timeline & Plan Lifecycle** | How did topics evolve across meetings, and which plans went somewhere? |
| 6 | **Organization Stakeholder Analysis** | Which organizations influenced which topics, and why? |

**Not selected** (and why):
- *Topic-Place Geography* — the existing Dashboard 3 already covers geographic context. The review confirms this should come last, after the source-difference and lifecycle stories are solid. Could be a future v3 addition.

**Cross-cutting enhancement** (not a new dashboard):
- Add reason text tooltips to existing Dashboard 1 sentiment nodes. This is the review's #2 priority — cheapest high-impact improvement — and belongs as an augmentation, not a standalone view.

---

## Data Preparation (shared across all three dashboards)

Before building any dashboard, create a data preparation layer that all new visuals draw from. This runs once at app startup.

### Source: CSV files, not pre-computed JSON

The new dashboards load CSV files from both `Collected_by_the_Government/` and `Collected_by_the_Journalist/` directories. The existing JSON pipeline is left untouched so Dashboards 1-3 keep working.

### Normalization rules (applied at load time)

| Field | Rule |
|-------|------|
| `plan_type` | Lowercase. `"Report"` and `"report"` become `"report"`. |
| `status` | Lowercase. `"Completed"` becomes `"completed"`. |
| `sentiment` | Keep as float. **Blank/empty values become `None`**, displayed as "unknown". Never coerce to 0. |
| `meeting_id` / `date` | The `date` column contains labels like `"Meeting 16"`, not real dates. Sort by the numeric suffix extracted from `meeting_id`. |

### Derived DataFrames

Build these once, reference everywhere:

| DataFrame | Source tables (journalist left-joined with government) | Key columns |
|-----------|-------------------------------------------------------|-------------|
| `source_coverage_entities` | `meetings`, `discussions`, `plans`, `people`, `organizations`, `places`, `topics` | `entity_type`, `entity_id`, `label`, `in_jour`, `in_gov` |
| `source_coverage_links` | `discussion_people_participations`, `plan_people_participations`, `discussion_org_participations`, `plan_org_participations`, `meeting_discussions`, `meeting_plans`, `discussion_plans`, `refers_to`, `travel_links` | `link_type`, `left_id`, `right_id`, `in_jour`, `in_gov`, `sentiment_jour`, `reason_jour` |
| `topic_lifecycle` | `plans` + `discussion_plans` + `plan_topics` + `meeting_plans` | `topic_id`, `plan_id`, `plan_type`, `status`, `meeting_id_introduced`, `meeting_id_latest` |
| `meeting_agenda` | `meetings` + `meeting_discussions` + `meeting_plans` + `discussion_topics` | `meeting_id`, `meeting_order`, `topic_id`, `discussion_id`, `plan_id` |
| `org_participation` | `organizations` + `discussion_org_participations` + `plan_org_participations` + `discussion_topics` + `plan_topics` | `org_id`, `org_name`, `topic_id`, `sentiment`, `reason`, `participation_type` |
| `participation_reasons` | All `*_participations` CSVs (journalist source) | `person_or_org`, `entity_id`, `topic_id`, `sentiment`, `reason` |

### Join strategy

Use the journalist dataset as the **canonical superset**. For each comparable CSV:

```
journalist_df.merge(
    government_df,
    on=[primary_key_columns],
    how="left",
    indicator=True,
    suffixes=("_jour", "_gov")
)
```

The `_merge` column gives: `"both"` (in both sources), `"left_only"` (journalist-only, i.e., government omission).

Track omissions at **two levels**:
- **Entity-level**: a meeting, plan, person, or place exists in journalist but not government data.
- **Link-level**: the entity exists in both, but a participation row or agenda link is missing from the government side. This is a subtler omission — the government acknowledges the plan exists but hides who participated.

---

## Dashboard 4 — Source Coverage Gap Detector

### Question it answers

> "What did the government data collection leave out, and is the omission pattern random or systematic?"

### Layout

```
+--------------------------------------------------------------+
|  SUMMARY BAR (top strip)                                      |
|  [Meetings: 3 missing] [Discussions: 26 missing] [Plans: ... ]|
+--------------------------------------------------------------+
|                          |                                    |
|   ENTITY COVERAGE TABLE  |   OMISSION DETAIL PANEL            |
|   (left, ~40% width)     |   (right, ~60% width)              |
|                          |                                    |
|   entity_type | jour | gov| missing  Selected entity details:  |
|   meetings    |  16  | 13 |   3     - What's in it             |
|   discussions | 101  | 75 |  26     - Who participated (jour)  |
|   plans       |  74  | 55 |  19     - Linked topics            |
|   people-disc |  99  | 71 |  28     - Sentiment + reason text  |
|   people-plan |  75  | 49 |  26     - "NOT in government data" |
|   places      | 172  | 93 |  79     badge                     |
|   ...         |      |    |         |                         |
|                          |                                    |
+--------------------------------------------------------------+
|  TOPIC OMISSION HEATMAP (bottom)                              |
|  Rows: 16 topics                                              |
|  Cols: entity types (meetings, discussions, plans, people,    |
|        places, org participations)                            |
|  Cell color: % of journalist records missing from government  |
|  (white = 0% missing, dark red = 100% missing)               |
+--------------------------------------------------------------+
```

### Components

1. **Summary bar** — One badge per entity/link type showing `journalist_count`, `government_count`, `journalist_only_count`. Clickable to filter the table below.

2. **Entity coverage table** — Left panel. Rows are entity types. Columns: journalist count, government count, missing count, missing %. Clicking a row filters the detail panel.

3. **Omission detail panel** — Right panel. Shows the actual journalist-only records for the selected entity type, with joined labels: meeting label, topic name, discussion title, plan title, person name, organization name, place name. Each row shows the reason text (journalist source) and a red "Gov data missing" badge.

4. **Topic omission heatmap** — Bottom panel. 16 rows (topics) by N columns (entity/link types). Cell intensity encodes `journalist_only_count / journalist_count` for that topic-entity combination. This reveals whether omissions cluster around specific topics (e.g., are fishing-related topics disproportionately omitted?).

### Interactions

- Click a topic row in the heatmap to filter both the coverage table and detail panel to that topic.
- Click a cell in the heatmap to jump to the specific entity type for that topic.
- Hover on any record in the detail panel to see the full reason text.

### Data pipeline

```python
# For each pair of comparable CSVs:
for table_name in COMPARABLE_TABLES:
    jour_df = load_csv("Collected_by_the_Journalist", table_name)
    gov_df = load_csv("Collected_by_the_Government", table_name)
    merged = jour_df.merge(gov_df, on=pk_cols, how="left", indicator=True)
    coverage[table_name] = {
        "jour_count": len(jour_df),
        "gov_count": len(gov_df),
        "jour_only": merged[merged._merge == "left_only"],
        "both": merged[merged._merge == "both"],
    }

# For the heatmap, group jour_only records by topic:
# join through discussion_topics / plan_topics to get topic_id per omitted record
```

### SVG approach

Consistent with the existing app's hand-coded SVG approach using `svg.py`:
- Summary bar: `<rect>` badges with text overlays.
- Coverage table: `<rect>` grid with `<text>` labels. No HTML tables — keep it SVG for visual consistency.
- Heatmap: `<rect>` grid with fill color on a white-to-red scale.
- Detail panel: Scrollable HTML/marimo `mo.ui` element (this is the one exception — a data table with many rows is better as scrollable HTML than an SVG element). Use `mo.ui.table` or a styled HTML list.

---

## Dashboard 5 — Meeting Timeline & Plan Lifecycle

### Question it answers

> "How did topics, discussions, and plans evolve across the 16 meetings? Which plans progressed and which stalled?"

### Layout

```
+--------------------------------------------------------------+
|  CONTROLS                                                     |
|  [Topic filter: All / Fishing / Tourism / ...]               |
|  [Color by: plan_status / sentiment / plan_type]             |
|  [Show gov omissions: toggle]                                |
+--------------------------------------------------------------+
|  MEETING TIMELINE (main panel)                                |
|                                                               |
|  Topic A  ----[D1]---[D2]--------[D3]---[D4]------          |
|                 |      |           |                          |
|               [P1:introduced]  [P1:in_progress]  [P1:done]   |
|                                                               |
|  Topic B  ---------[D5]---[D6]-------[D7]--------           |
|                      |                 |                      |
|                   [P2:intro]       [P2:planned]  (stalled)   |
|                                                               |
|  Topic C  --[D8]--[D9]------[D10]-----[D11]---[D12]---      |
|              |      |         |                               |
|           [P3:intro][P3:prog][P3:done]  [P4:intro][P4:prog]  |
|                                                               |
|           M1  M2  M3  M4  M5  M6  ... M13  M14  M15  M16    |
+--------------------------------------------------------------+
|  PLAN LIFECYCLE SUMMARY (bottom panel)                        |
|                                                               |
|  Stacked bar per topic:                                       |
|  [intro | planned | in_progress | completed]                 |
|  + plan_type breakdown as sub-color                          |
|                                                               |
|  Status funnel (right side):                                  |
|  introduced: 74 plans                                         |
|  planned:    52 plans  (22 never advanced)                    |
|  in_progress: 38 plans (14 stalled at planned)               |
|  completed:   29 plans (9 stalled at in_progress)            |
+--------------------------------------------------------------+
```

### Components

1. **Controls** — Topic filter dropdown, color mode selector, government omission toggle (when on, journalist-only records get a dashed border or red outline reusing the omission flags from Dashboard 4's data layer).

2. **Meeting timeline** (main panel) — Horizontal axis: 16 meetings, sorted by numeric suffix of `meeting_id`. Vertical axis: topics (one swim lane per topic). Within each lane:
   - **Discussion markers**: circles placed at the meeting(s) where the discussion appeared on the agenda. Color encodes average sentiment of participants at that discussion in that meeting.
   - **Plan progression arcs**: lines connecting a plan's first appearance to its latest appearance, with status badges at each transition point. Color encodes `plan_type` or status depending on the control setting.
   - **Gov-omission markers**: if the toggle is on, discussions or plans present only in the journalist source get a distinct visual treatment (dashed outline, red dot).

3. **Plan lifecycle summary** (bottom panel):
   - **Left**: stacked horizontal bar per topic showing how many plans reached each status level. Segments colored by status (`introduced` = light gray, `planned` = yellow, `in_progress` = blue, `completed` = green).
   - **Right**: a funnel or waterfall showing the global drop-off: how many plans were introduced total, how many advanced to each stage, how many stalled. This answers "what fraction of plans actually got done?"

### Data pipeline

```python
# Build per-meeting agenda:
meeting_disc = load("meeting_discussions.csv")  # meeting_id, discussion_id
meeting_plans = load("meeting_plans.csv")        # meeting_id, plan_id
disc_topics = load("discussion_topics.csv")      # discussion_id, topic_id
plan_topics = load("plan_topics.csv")            # plan_id, topic_id
disc_plans = load("discussion_plans.csv")        # discussion_id, plan_id, status

# For each topic, collect all meetings where it appeared (via its discussions):
topic_timeline = (
    meeting_disc
    .merge(disc_topics, on="discussion_id")
    .merge(discussions[["discussion_id", "title"]], on="discussion_id")
)

# For plan lifecycle, determine first and last meeting per plan:
plan_meetings = (
    meeting_plans
    .merge(plan_topics, on="plan_id")
    .merge(plans[["plan_id", "plan_type", "title"]], on="plan_id")
)

# Status is in discussion_plans — get the highest status per plan:
STATUS_ORDER = {"introduced": 0, "planned": 1, "in_progress": 2, "completed": 3}
plan_status = (
    disc_plans
    .assign(status_rank=lambda d: d.status.str.lower().map(STATUS_ORDER))
    .groupby("plan_id")
    .agg(max_status=("status_rank", "max"), n_discussions=("discussion_id", "count"))
)
```

### Sorting

Meetings are sorted by the numeric suffix of `meeting_id`, **not** by the `date` column (which contains labels like "Meeting 16", not actual dates). Extract with:

```python
meetings["meeting_order"] = meetings["meeting_id"].str.extract(r"(\d+)").astype(int)
meetings = meetings.sort_values("meeting_order")
```

### SVG approach

- Timeline swim lanes: horizontal `<line>` elements per topic, with `<circle>` markers for discussions and `<rect>` badges for plan status transitions.
- Plan arcs: `<path>` elements connecting status transition points.
- Lifecycle bars: `<rect>` stacked horizontally, same technique as Dashboard 3's trip bars.
- Funnel: trapezoid `<polygon>` elements or simple stacked `<rect>` with decreasing widths.

---

## Dashboard 6 — Organization Stakeholder Analysis

### Question it answers

> "Which organizations pushed which topics, how polarized are they, and do any board members' positions suspiciously mirror an organization's stance?"

### Layout

```
+--------------------------------------------------------------+
|  CONTROLS                                                     |
|  [Filter by topic: All / specific topic]                     |
|  [Filter by org: All / specific organization]                |
|  [Show: discussions / plans / both]                          |
+--------------------------------------------------------------+
|                              |                                |
|  ORG-TOPIC SENTIMENT MATRIX  |  REASON TEXT PANEL             |
|  (left, ~55% width)         |  (right, ~45% width)           |
|                              |                                |
|  Rows: 8 organizations      |  Selected org + topic:         |
|  Cols: 16 topics             |  - Discussion participations   |
|  Cell: avg sentiment         |    with reason text            |
|  Size: participation count   |  - Plan participations         |
|  Color: polarity             |    with reason text            |
|  (green pos / red neg)       |  - Sentiment distribution      |
|                              |    (sparkline or small hist)   |
|                              |                                |
+--------------------------------------------------------------+
|  PERSON-ORG ALIGNMENT (bottom panel)                          |
|                              |                                |
|  Left: bar chart per person  |  Right: alignment details      |
|  showing correlation between |  For selected person:          |
|  their sentiment profile and |  - Person sentiment by topic   |
|  each org's sentiment        |  - Most-aligned org profile    |
|  profile (Pearson r)         |  - Key reason text comparisons |
|                              |                                |
+--------------------------------------------------------------+
```

### Components

1. **Org-Topic sentiment matrix** — Bubble matrix. Rows: 8 organizations. Columns: 16 topics. Each cell is a circle whose **size** encodes participation count (how many discussions + plans the org participated in for that topic) and whose **color** encodes average sentiment (green = positive, red = negative, gray = unknown/null). Empty cells mean the org did not participate in that topic.

2. **Reason text panel** — When a cell in the matrix is clicked, this panel shows the actual participation records: discussion title, plan title, sentiment score, and the full `reason` text from the CSV. This directly addresses the review's #2 priority (make reason text visible) in the context where it's most useful — understanding *why* an organization holds a position.

3. **Person-Org alignment panel** (bottom):
   - **Left**: horizontal bar chart. One row per board member. Bar length = Pearson correlation between the person's sentiment vector (across topics) and the most-aligned organization's sentiment vector. Color = which organization they most align with. This surfaces suspicious alignment (e.g., a board member who votes exactly like High Seas Fishing Inc. on every topic).
   - **Right**: on click, shows side-by-side comparison of the person's topic sentiments vs. the aligned org's topic sentiments, with key reason text from both.

### Data pipeline

```python
# Organization participation (discussions):
org_disc = load("discussion_org_participations.csv")  # org_id, discussion_id, sentiment, reason
disc_topics = load("discussion_topics.csv")
org_disc_topics = org_disc.merge(disc_topics, on="discussion_id")

# Organization participation (plans):
org_plan = load("plan_org_participations.csv")  # org_id, plan_id, sentiment, reason
plan_topics = load("plan_topics.csv")
org_plan_topics = org_plan.merge(plan_topics, on="plan_id")

# Combined org-topic sentiment:
org_sentiment = pd.concat([
    org_disc_topics[["org_id", "topic_id", "sentiment", "reason"]].assign(type="discussion"),
    org_plan_topics[["org_id", "topic_id", "sentiment", "reason"]].assign(type="plan"),
])

# Matrix aggregation (excluding null sentiment from averages):
org_topic_matrix = (
    org_sentiment[org_sentiment.sentiment.notna()]
    .groupby(["org_id", "topic_id"])
    .agg(avg_sentiment=("sentiment", "mean"), count=("sentiment", "size"))
    .reset_index()
)

# Person-Org alignment:
# Build person sentiment vector (from person participation CSVs):
person_topics = ...  # similar aggregation from discussion_people_participations
# For each person, compute correlation with each org's sentiment vector:
for person in persons:
    for org in orgs:
        shared_topics = ...  # topics where both have sentiment
        if len(shared_topics) >= 3:
            r = pearsonr(person_vec[shared_topics], org_vec[shared_topics])
```

### Null sentiment handling

Per the review: blank sentiment values (especially around deep fishing dock rows) are preserved as `None`. The matrix shows these as **gray cells** with a "?" label. They are excluded from averages and correlation calculations but are **counted separately** so the user can see that data is missing, not neutral.

### SVG approach

- Bubble matrix: `<circle>` elements in a grid, radius scaled by count, fill by sentiment.
- Reason panel: scrollable HTML via `mo.ui.table` or styled `<div>` (same exception as Dashboard 4's detail panel — long text lists are better in HTML).
- Alignment bars: horizontal `<rect>` elements, same visual language as Dashboard 3.
- Side-by-side comparison: paired `<circle>` elements (person vs. org) per topic, connected by thin lines.

---

## Cross-cutting enhancement — Reason text on Dashboard 1

### What changes

The existing radial sentiment map (Dashboard 1) shows per-person sentiment but gives no explanation. Add hover tooltips showing aggregated reason texts from `participation_reasons` DataFrame.

### Implementation

When the user hovers over a person node or a discussion/plan edge in Dashboard 1:
- Look up all participation records for that person + topic (or specific discussion/plan).
- Show a tooltip with: sentiment score, participation type (discussion or plan), and the first ~200 characters of the `reason` text.
- If multiple reason texts exist, show the top 3 by absolute sentiment magnitude.

This uses the same `participation_reasons` DataFrame built in the shared data preparation layer.

### Effort

Low. The existing Dashboard 1 already has hover JavaScript for highlighting edges. Extend the `onmouseover` handler to populate a tooltip `<div>` with the reason text.

---

## Implementation Sequence

### Phase 1 — Shared data layer + Dashboard 4

**Why first**: Dashboard 4's data layer (the left-join coverage computation) is the foundation. Dashboards 5 and 6 both optionally consume the `in_gov` flags. Building Dashboard 4 also validates that the CSV loading and normalization pipeline works.

Steps:
1. Add CSV loading functions with normalization (lowercase plan_type, status; null-safe sentiment).
2. Build `source_coverage_entities` and `source_coverage_links` DataFrames.
3. Implement Dashboard 4 SVG components: summary bar, coverage table, omission detail panel, topic heatmap.
4. Add as new tab in `index.py`.

### Phase 2 — Dashboard 5

**Why second**: Uses the `meeting_agenda` and `topic_lifecycle` DataFrames. These are self-contained joins that don't depend on Dashboard 4's coverage data (but optionally annotate with it via the gov-omission toggle).

Steps:
1. Build `meeting_agenda` and `topic_lifecycle` DataFrames.
2. Implement meeting timeline SVG with swim lanes.
3. Implement plan lifecycle summary (stacked bars + funnel).
4. Wire up controls (topic filter, color mode, gov-omission toggle).
5. Add as new tab.

### Phase 3 — Dashboard 6 + Dashboard 1 enhancement

**Why third**: Organization data is the smallest dataset and benefits from the pattern established in Dashboards 4-5. The Dashboard 1 tooltip enhancement uses `participation_reasons`, which is already built by this point.

Steps:
1. Build `org_participation` DataFrame.
2. Implement org-topic bubble matrix.
3. Implement reason text panel (reused from `participation_reasons`).
4. Compute person-org alignment correlations.
5. Implement alignment bar chart.
6. Add as new tab.
7. Extend Dashboard 1 hover handlers with reason text tooltips.

### Phase 4 — Polish

1. Visual consistency pass: ensure new dashboards match the existing color palette, glyph style, and interaction patterns.
2. Performance check: the CSV loading adds startup cost — verify it stays under 2-3 seconds.
3. Export check: verify the marimo WASM export still works with the added data.
4. Update `docs/` static build.

---

## Constraints & Guidelines

- **No new visualization libraries.** Stick with `svg.py` + hand-coded JavaScript, matching the existing approach.
- **Journalist is canonical.** Always left-join government onto journalist, never the reverse.
- **Entity vs. link omissions tracked separately.** A plan existing in both sources but missing a participation row is a different kind of omission than a plan being entirely absent from government data.
- **Null sentiment = unknown, not zero.** Display as gray/`?`. Exclude from averages.
- **Sort meetings by numeric ID suffix**, not by the `date` column.
- **Normalize case at load time** before any grouping or comparison.
- **Augment before adding.** Where possible, add overlays and badges to existing views rather than duplicating content. The gov-omission toggle in Dashboard 5 is an example.
- **Keep data prep and rendering in separate marimo cells** so the dependency graph stays clean and cells rerun efficiently.
