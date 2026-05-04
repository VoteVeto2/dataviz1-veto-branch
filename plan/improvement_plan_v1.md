# Improvement Plan v1 — Leveraging Unused Data

## Current State

### What `index.py` currently visualizes (3 dashboards)

| # | Dashboard | Data source | What it shows |
|---|-----------|-------------|---------------|
| 1 | **Board Sentiment Biases Map** | `bias_persons.json`, `nodes.json` | Radial SVG: per-person avg sentiment (fishing-centric), colored by polarity, with topic/discussion/plan breakdown |
| 2 | **Participation Bubble Chart** | `people_participation_summary.json`, `people_participation_total.json` | Pie-chart matrix: # of topics, meetings, discussions, plans per person, split by focus (fishing/tourism/both/other) |
| 3 | **Visit & Time Spend Bias** | `time_trip_spend.json`, `places_edited.json`, `oceanus_map.geojson` | Shoreline scene + geographic map + trip splits: where board members physically traveled, industrial vs tourism zones |

### Data files loaded (7 of ~55)

`bias_persons.json`, `nodes.json`, `people_participation_summary.json`, `people_participation_total.json`, `places_edited.json`, `oceanus_map.geojson`, `time_trip_spend.json`

### Data sitting entirely unused

| Category | Files | What's in them |
|----------|-------|----------------|
| **Organizations** | `organizations.csv`, `discussion_org_participations.csv`, `plan_org_participations.csv` (×2 sources) | 8 organizations (High Seas Fishing Inc., Tours Central Ticketing, etc.) with sentiment scores and reasons for every discussion/plan they participated in |
| **Meeting timeline** | `meetings.csv`, `meeting_discussions.csv`, `meeting_plans.csv` (×2 sources) | 16 meetings in chronological order, which discussions and plans were on the agenda at each meeting |
| **Plan lifecycle** | `discussion_plans.csv` | Linkage with status progression: `introduced → planned → in_progress → completed` |
| **Plan types** | `plans.csv` | Each plan has a `plan_type`: Travel, Report, Proposal, Presentation, Feedback, Take Action |
| **Discussion–Place links** | `refers_to.csv`, `travel_links.csv` | Which discussions and plans reference which physical locations |
| **Reason text** | `reason` column in all participation CSVs | Free-text justification for every sentiment score (e.g., "Seen as prioritizing tourism over fishing-related infrastructure") |
| **Gov vs Journalist divergence** | All 21 CSVs exist in both `Collected_by_the_Government/` and `Collected_by_the_Journalist/` | Two parallel data collections — differences between them are a core analytical angle but currently only exposed as a binary `in_gov_data` flag |
| **GeoJSON fish species** | `oceanus_map.geojson` → `fish_species_present` | Present per-region in the map data but never read or displayed |
| **SQLite databases** | `database_gov.db`, `database_jour.db` | Full relational databases (code to use them is commented out) |

### Partially unused columns in loaded files

- `bias_persons.json`: `sentiment_raw`, `industry` — loaded but never accessed
- `nodes.json`: `description` — loaded but never referenced

---

## Improvement Ideas

### Idea 1 — Organization Influence Network

**Unused data**: `organizations.csv`, `discussion_org_participations.csv`, `plan_org_participations.csv`

**What it reveals**: Organizations have strong, polarized sentiments (e.g., Tours Central Ticketing = +1.0 on tourism, Paackland Container Inc. = −0.5 on tourism, Industrial Shipping = +1.0 on fishing). Currently, only *people* appear in the sentiment map. Organizations are the *stakeholders behind the people* and are completely invisible.

**Visualization concept**: A bipartite network or Sankey-style flow diagram:
- Left side: 8 organizations, color-coded by industry alignment
- Right side: 16 topics
- Edges: weighted by sentiment strength, colored by polarity
- Overlay: which board members' positions align with which organizations (correlation)

**Key insight it surfaces**: Which organizations are exerting influence over which topics, and whether any board member's voting pattern suspiciously mirrors a specific organization's interests.

**Difficulty**: Medium. Data is already clean in CSVs. Needs a new SVG layout.

---

### Idea 2 — Meeting Timeline: How Sentiment Evolved

**Unused data**: `meetings.csv`, `meeting_discussions.csv`, `meeting_plans.csv`, `discussion_plans.csv` (status column)

**What it reveals**: Discussions happen across multiple meetings. Plans go through status transitions (`introduced → planned → in_progress → completed`). Currently, all of this temporal progression is flattened into a single average. We lose the story of *how opinions shifted over time*.

**Visualization concept**: A horizontal timeline (Meeting 1 → Meeting 16):
- Each meeting is a column
- Rows: topics (or board members)
- Cells: sentiment heatmap at that point in time
- Plan lifecycle badges: small icons showing when a plan was introduced, progressed, completed
- Optional animation: scrub through meetings to see sentiment shift

**Key insight it surfaces**: Did someone flip their position after a site visit? Did a plan stall for multiple meetings? Are there suspicious patterns where sentiment changes right after a travel trip?

**Difficulty**: Medium-High. Need to reconstruct per-meeting sentiment from the discussion-level data by joining `meeting_discussions` → `discussion_people_participations`.

---

### Idea 3 — Government vs. Journalist Data Discrepancy Detector

**Unused data**: All 42 CSVs across both `Collected_by_the_Government/` and `Collected_by_the_Journalist/` directories

**What it reveals**: The project already has a `in_gov_data` boolean flag in `nodes.json` but never highlights *what's different*. The two data sources can disagree on:
- Which people participated in which discussions (missing rows)
- Sentiment scores for the same person on the same discussion
- Reason text differences
- Which organizations participated
- Which plans exist or their status

**Visualization concept**: A diff-view table or overlay:
- Side-by-side comparison grid: Journalist vs. Government
- Highlighted cells where values diverge (red = major disagreement, yellow = minor)
- Summary statistics: "Government data is missing X% of participation records" or "Sentiment disagrees on Y discussions"
- Click-through: shows the `reason` text from each source for the same participation

**Key insight it surfaces**: Is the government data sanitized or incomplete? Are there discussions that only appear in one source? This directly supports the project's investigative angle (the "honesty" flag on Tante Titan suggests this is a corruption/bias investigation).

**Difficulty**: Medium. Pure data comparison — the schema is identical between sources. Main work is the diff logic and a clear visual representation.

---

### Idea 4 — Sentiment Reason Word Cloud / Text Analysis

**Unused data**: `reason` column from all `*_participations.csv` files

**What it reveals**: Every sentiment score has a human-written justification. Examples:
- "Seen as prioritizing tourism over fishing-related infrastructure"
- "Feels committee should be doing more for blue-collar workers"
- "Loves ceremonial gestures and believes they can have a positive impact"

Currently these rich text explanations are completely invisible in the visualization.

**Visualization concept**: Two options:
1. **Tooltip enrichment** (low effort): When hovering over a node in Dashboard 1, show the aggregated reason texts that contributed to that sentiment score
2. **Keyword analysis** (higher effort): Extract recurring themes from reason text. Show a word cloud or grouped bar chart: what concepts (e.g., "tourism", "workers", "environment", "efficiency") dominate each person's reasoning

**Key insight it surfaces**: The *why* behind the numbers. Two people might both have -0.5 sentiment but for completely different reasons — one cares about resource allocation, the other about environmental impact.

**Difficulty**: Low (tooltips) to Medium (keyword extraction).

---

### Idea 5 — Topic–Place Geographic Overlay

**Unused data**: `refers_to.csv`, `travel_links.csv`, `places_edited.json`, `oceanus_map.geojson`

**What it reveals**: Dashboard 3 already shows where people *traveled*, but not *why*. The `refers_to.csv` links discussions to physical places, and `travel_links.csv` links plans to destinations. This means we know which topics are geographically anchored (e.g., "deep fishing dock" discussions reference High Seas Fishing Inc. in Himark).

**Visualization concept**: Enhance the existing geographic map (Dashboard 3) with:
- Topic pins: place markers colored by topic, showing which locations are under discussion
- Sentiment halos: rings around locations colored by the average sentiment of discussions that reference them
- Travel routes: animated paths showing who traveled where for which topic

**Key insight it surfaces**: Geographic concentration of conflict. Are all the contentious (negative sentiment) topics concentrated in one area? Does travel correlate with changed opinions?

**Difficulty**: Low-Medium. Builds on existing map infrastructure. Main work is joining `refers_to` → places and overlaying.

---

### Idea 6 — Plan Type Distribution & Completion Analysis

**Unused data**: `plans.csv` (plan_type column), `discussion_plans.csv` (status column)

**What it reveals**: Plans have types: Travel, Report, Proposal, Presentation, Feedback, Take Action. They also have tracked statuses. Currently none of this is visible.

**Visualization concept**: A stacked bar chart or waffle chart:
- X axis: topics
- Y axis: count of plans
- Color: plan type
- Opacity or badge: completion status
- Summary: which topics got all the way to "Take Action" vs. stuck at "Proposal"

**Key insight it surfaces**: Topics where lots of plans were introduced but nothing reached completion (bureaucratic stalling). Topics that jumped straight to action (rubber-stamped?). Asymmetry in plan types — are fishing topics getting more "Reports" while tourism topics get more "Take Action"?

**Difficulty**: Low. Small, well-structured dataset. Straightforward bar/waffle chart.

---

## Recommended Priority Order

| Priority | Idea | Impact | Effort | Rationale |
|----------|------|--------|--------|-----------|
| **1** | Idea 3 — Gov vs. Journalist Diff | High | Medium | This is the project's core investigative angle. The data infrastructure is already there (two parallel sets). Biggest bang for the buck. |
| **2** | Idea 4 (tooltips) — Reason Text | High | Low | Near-zero effort to add tooltips showing reason text on existing Dashboard 1 nodes. Dramatically improves interpretability. |
| **3** | Idea 1 — Organization Network | High | Medium | Organizations are major stakeholders currently invisible. Adds a completely new analytical dimension. |
| **4** | Idea 2 — Meeting Timeline | Medium-High | Medium-High | Temporal evolution is the most complex new insight but also the hardest to build. |
| **5** | Idea 6 — Plan Lifecycle | Medium | Low | Quick win. Small chart, clear insight about which topics progressed vs. stalled. |
| **6** | Idea 5 — Topic-Place Overlay | Medium | Low-Medium | Builds on existing map. Nice-to-have but lower priority than the analytical insights above. |

---

## Summary

The current `index.py` uses roughly **13%** of available data files and leaves several high-value analytical dimensions untapped:
- **Organizations** (who are the real stakeholders?)
- **Temporal evolution** (how did opinions shift meeting-to-meeting?)
- **Data source reliability** (government vs. journalist — who's hiding what?)
- **Qualitative reasoning** (why, not just how much?)
- **Plan lifecycle** (which topics actually went somewhere?)
- **Geographic context** (which places are at the center of controversy?)

Addressing even the top 3 priorities would transform the project from a sentiment snapshot into a multi-dimensional investigation tool.
