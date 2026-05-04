# COOTEFOO Board Investigation Dashboard — Project Report

VAST Challenge 2025 MC2

---

## Part 1. Metadata

- **Students:** [Student 1 name, student number], [Student 2 name, student number], [Student 3 name, student number]
- **Group number:** [group_x]
- **Dataset:** Oceanus
- **User:** Journalist

---

## Part 2. Project Description

This project investigates the **Commission on Overseeing the Economic Future of Oceanus (COOTEFOO)**, a local government board navigating a growing conflict between the island's traditional fishing industry and a booming tourism sector. Two opposing lobby groups — **FILAH** (Fishing is Living and Heritage) and **TROUT** (Tourism Raises OceanUs Together) — each accuse the board of bias in favor of the other side.

**Dataset.** The Oceanus dataset comprises two parallel relational databases collected by different actors about the same committee process: one by the **government** (13 meetings, 75 discussions, 55 plans, 194 trips) and one by an independent **journalist** (16 meetings, 101 discussions, 74 plans, 342 trips). Both share an identical schema of 21 tables (8 entity + 13 junction), covering 6 board members, 8 organizations, and 15 debate topics spanning fishing infrastructure, tourism expansion, housing, and community matters. Entity tables (people, organizations, topics) are byte-for-byte identical across sources; the government dataset is a strict subset of the journalist data. Where records overlap, sentiment values match exactly — the difference lies purely in **coverage gaps** (the government omits 3 meetings, 26 discussions, 19 plans, and 148 trips).

**Persona.** We adopt the perspective of **Marta Kowalska**, a journalist seeking evidence-based patterns, inconsistencies, and conflicts of interest to communicate a balanced story. Her core questions: Is the board biased toward fishing or tourism? Do members' travel patterns reveal undisclosed allegiances? Which proposals stall and why? Where do government records diverge from independent observation?

---

## Part 3. Visual Design

### 3.1 Design Process

Our design process followed a structured **diverge-emerge-converge** workflow:

1. **Data investigation** (diverge): We began with an exploratory Jupyter notebook (`notebook/data_investigation.ipynb`) to understand the relational schema, coverage gaps between government and journalist sources, sentiment distributions, and trip patterns. Key findings at this stage: the government under-tracks 3 of 6 members' trips, sentiment is consistent where records overlap, and there are clear pro-fishing vs. pro-tourism clusters among board members.

2. **First-round sketches** (diverge): Each team member independently produced 3-4 rough sketches exploring different visual encodings. Ideas ranged from radial sentiment networks and geographic trip maps to heatmaps, Sankey flows, and small-multiples timelines. We prioritized designs that could expose **bias patterns** (not just summarize data) and that could leverage the **dual-source comparison** as an analytical layer.

3. **Critique and clustering** (emerge): We consolidated sketches on a shared board, grouped them by analytical question (sentiment polarity, geographic behavior, participation volume, temporal dynamics, relational structure, action vs. rhetoric), and identified the strongest encoding for each question. Three analytical gaps emerged that existing designs could not cover: temporal sentiment evolution, person-to-person alignment, and plan outcome tracking.

4. **Refinement** (converge): We selected 6 designs for implementation — 3 addressing foundational questions (D1: sentiment polarity, D2: geographic bias, D3: participation volume) and 3 addressing the identified gaps (D4: temporal dynamics, D5: relational structure, D6: action vs. rhetoric). The latter three went through three formal improvement iterations (v1 -> v2 -> v3), including a peer review that identified the v2 implementations as "mostly static summaries, not investigative tools," leading to a substantial rebuild.

### 3.2 Selected Sketches (Design Path)

> **Note:** Insert actual sketch images here. The descriptions below document the encoding rationale for each sketch in our design journey.

**Sketch 1 — Radial Sentiment Network (diverge)**
A radial layout with 6 board members arranged on the outer ring and topic clusters at the center. Edges connect people to topics, colored by sentiment polarity (green = support, red = oppose). This sketch became Dashboard 1.
*Encoding:* Position (radial) = person identity; edge color (hue) = sentiment; edge presence = participation link; node shape (pentagon/square) = discussion vs. plan.
*Why chosen:* Shows the complete person-topic sentiment structure in a single view, making polarization visible at a glance.

**Sketch 2 — Geographic Trip Map (diverge)**
An island map with colored dots for visited locations, sized by visit frequency. A sidebar shows fishing vs. tourism zone tallies per person.
*Encoding:* Position (geographic) = place location; dot color = zone type (fishing/tourism/other); dot size = frequency; sidebar bar length = zone bias.
*Why chosen:* Travel behavior is a proxy for undisclosed allegiances — if a board member claiming neutrality only visits fishing docks, that is newsworthy.

**Sketch 3 — Participation Bubble Matrix (diverge)**
A grid of person x metric (topics, meetings, discussions, plans) where each cell is a pie chart sized by total count with slices colored by focus type.
*Encoding:* Position (row) = person; position (column) = metric; area = total count; slice angle = proportion by focus type; slice hue = fishing/tourism/both/other.
*Why chosen:* Quickly reveals who is most active and where their activity concentrates — a participation-volume complement to the sentiment-polarity view.

**Sketch 4 — Meeting Timeline with Sentiment Bands (emerge)**
Horizontal timeline (M1-M16) with one line per person, Y-axis = sentiment, shaded band = committee range. Early version used bar charts per meeting; revised to connected line chart for trend visibility.
*Encoding:* Position X = meeting sequence; position Y = avg sentiment; line color = person identity; point size = participation count; band fill = committee min-max range.
*Why chosen:* D1's radial map collapses all meetings into one average. A person who went from -1.0 to +1.0 looks the same as one who was always 0.0. The timeline reveals **who shifted, who hardened, and when**.

**Sketch 5 — Person-Topic Heatmap (emerge)**
Full 6x15 grid with cell color = avg sentiment, grouped columns by topic category (fishing/tourism/neutral). Early version was a plain heatmap; emerged into a dual-panel design adding a pairwise agreement matrix below.
*Encoding:* Position (row) = person; position (column) = topic; cell fill (sequential diverging) = sentiment; cell border = participation count; topic column grouping = industry category.
*Why chosen:* The radial network (D1) shows connections but makes systematic comparison difficult. A heatmap's grid alignment makes row-vs-row comparison trivial — and adding Pearson correlation reveals alliance structures invisible in individual views.

**Sketch 6 — Plan Lifecycle Funnel (emerge)**
Trapezoid funnel showing how many plans reached each status stage (introduced -> planned -> in_progress -> completed). Initial version showed final-status counts only; peer review noted this was misleading, so we redesigned as a cumulative funnel with drop-off annotations.
*Encoding:* Funnel stage = status rank; bar width = count reaching that stage; color = status; annotation text = drop-off between stages.
*Why chosen:* The participation matrix (D3) counts plans but cannot distinguish completed from stalled. A funnel directly answers "what fraction of proposals actually become reality?"

**Sketch 7 — Swim Lane Timeline (converge)**
Topic rows with horizontal bars spanning each plan's lifespan (first to last meeting), colored by final status. Discussion presence shown as circles above the lane.
*Encoding:* Position Y = topic row; position X = meeting range (bar start to end); bar color = final status; bar length = lifespan; circle size = discussion count per meeting; small circles on bar = status transition points.
*Why chosen:* Combines temporal span, topic grouping, and outcome status in a single view — the "action vs. rhetoric" layer missing from D1-D3.

**Sketch 8 — Plan Type x Status Cross-Tab (converge)**
Small matrix appended to the swim lane view showing plan type (proposal, report, travel, take action, etc.) vs. final status, with cell intensity = count.
*Encoding:* Position (row) = plan type; position (column) = final status; cell fill intensity = count relative to maximum; cell color = status color.
*Why chosen:* Answers whether certain plan types (e.g., "take action" vs. "proposal") have systematically different completion rates — a structural bias indicator.

**Sketch 9 — Government Omission Overlay (converge, cross-cutting)**
Rather than a separate dashboard, we designed a visual layer that could be toggled across D4-D6: dashed coral borders on data points where government records are missing. This makes the "coverage gap" story visible within the analytical context where it matters, rather than in an isolated summary.
*Encoding:* Dashed stroke = journalist-only record; stroke color = coral (#C4776A); toggle control = checkbox.
*Why chosen:* The most newsworthy finding is not just "what happened" but "what the government chose not to record." Embedding this in every view makes it impossible to ignore.

### 3.3 Three Designs Selected for Implementation

From the sketches above, we selected three designs addressing the analytical gaps identified in section 3.1:

**Design A — Sentiment Evolution Timeline (Dashboard 4)**
Tracks how each person's stance changed meeting-by-meeting. Combines the line chart (sketch 4) with the gov-omission overlay (sketch 9). Interactive topic filter allows drilling into any single topic. Detail table below shows every underlying participation record.
*Visual encoding:* Connected line chart with person-colored lines, sized points, sentiment band, dashed gov-missing markers.
*Interaction:* Hover points for tooltip; topic dropdown filters all views; scrollable detail table with sortable columns.
*Analytical value:* Answers "who shifted, who hardened, and on which topics?" — the temporal dimension missing from D1-D3.

**Design B — Person-Topic Sentiment Fingerprint (Dashboard 5)**
Full heatmap of all sentiment data plus a pairwise agreement matrix. Combines the heatmap (sketch 5) with column grouping by industry and the agreement matrix.
*Visual encoding:* 6x15 heatmap with diverging color scale, topic group headers, border thickness for activity, dashed for gov gaps. Below: 6x6 Pearson correlation grid.
*Interaction:* Hover cell for cross-hair highlight and tooltip; click to lock highlight; hover agreement cell to highlight both persons' rows in heatmap; person/topic dropdowns filter the detail table.
*Analytical value:* Answers "who aligns with whom?" — the relational structure missing from D1-D3.

**Design C — Plan Outcome Tracker (Dashboard 6)**
Swim lane timeline + cumulative funnel + type-status cross-tab. Combines sketches 6, 7, and 8 into a three-panel layout.
*Visual encoding:* Swim lanes (bar color = final status, circles = discussions/transitions), cumulative funnel (stage width = count, drop-off annotations), small heatmap (type x status).
*Interaction:* Hover plan bars for tooltip with expansion animation; topic and type dropdowns; gov-missing toggle; detail table with participant sentiment and reasons.
*Analytical value:* Answers "which plans completed vs. stalled?" — the action-vs-rhetoric layer missing from D1-D3.

---

## Part 4. Implementation

We implemented three custom interactive dashboards (D4, D5, D6) as marimo reactive notebooks. Each dashboard is both a standalone app (`dashboard_N.py`) and a tab within the integrated 6-tab application (`index.py`). All visualizations use hand-coded SVG with embedded JavaScript for interactivity, rendered via `mo.iframe()`.

**Technology stack:** Python 3.13+, marimo >= 0.23.3, pandas 3.0.2, numpy 2.4.4. No external charting library — all charts are custom SVG with embedded CSS/JS for tooltips, highlights, and animations.

**Running instance:** [TODO: Insert HuggingFace or deployment URL here]

**Video demonstration:** [TODO: Insert YouTube URL here]

---

### 4.1 Dashboard 4 — Sentiment Evolution Timeline

**Intended design:**

> [TODO: Insert hand-drawn mock-up or wireframe image here]

The intended design (documented in `plan/improvement_plan_v3.md`) was a connected line chart tracking each board member's average sentiment per meeting across M1-M16, with:
- One colored line per person (6 lines max)
- Point size encoding participation count
- A shaded committee-range band (min/max sentiment per meeting)
- Dashed borders on points where government data is missing
- A topic dropdown to isolate individual topics or view the aggregate
- A scrollable detail table below showing every underlying participation record

**Actual design — visual encoding:**

The implemented dashboard (`dashboard_4.py`, 383 lines) matches the intended design closely:

- **Marks:** Lines (polylines connecting meeting points per person) and circles (one per person-meeting data point).
- **Channels:**
  - *X position* = meeting sequence (M1-M16), evenly spaced across the chart width
  - *Y position* = average sentiment (-1.0 to +1.0), linearly mapped
  - *Line color / circle stroke* = person identity (6-color palette: Carol Limpet #D4956B, Ed Helpsford #7B9BAF, Seal #8A7E74, Simone Kat #B87D9E, Tante Titan #5B8FA8, Teddy Goldstein #9B8C5B)
  - *Circle fill* = sentiment value on a diverging warm scale (green-positive to coral-negative, cream at zero, gray for unknown)
  - *Circle radius* = participation count (sqrt-scaled, clamped 4-10px)
  - *Stroke dash pattern* = government data presence (solid = present, dashed = journalist-only)
  - *Stroke color shift* = #C4776A (coral) when gov data missing
  - *Band fill* = committee range polygon (#D4956B at 8% opacity)
  - *Dashed line overlay* = committee mean (gray, 60% opacity)
- **Grid:** Y-axis gridlines at -1.0, -0.5, 0.0, +0.5, +1.0 with a heavier zero line. X-axis meeting labels (M1-M16).
- **Background:** Warm cream (#FDF8F4) with soft tan borders (#E8DDD4).

**Interactions:**

1. **Topic dropdown** (`mo.ui.dropdown`): Selects a specific topic or "All topics (aggregate)." When a single topic is selected, the chart and detail table filter to participations on that topic only; the committee band recalculates for that subset.
2. **Hover tooltip:** Hovering a data point enlarges it (1.4x radius) and adds a drop-shadow. A floating tooltip shows: person name, meeting number, sentiment value (color-coded), record count, and government-missing count.
3. **Detail table** (`mo.ui.table`): Below the chart, a scrollable, sortable, filterable table shows all participation records for the selected topic with columns: Meeting, Person, Topic, Type (discussion/plan), Title, Sentiment, Reason, In Gov?.

**Gap analysis:**

| Intended | Actual | Gap |
|----------|--------|-----|
| Person multiselect filter | Topic dropdown only | Minor: could add person filter, but all 6 lines are visible and distinguishable. Topic filter is the higher-value control. |
| Click point to populate detail panel | Detail table shows all records for selected topic | Shift: rather than click-to-filter, the table shows all records, which is more comprehensive. Could add click-to-scroll-to-row. |
| Sentiment band with labeled min/max persons | Band is unlabeled polygon | Minor: adding min/max person labels at band edges would improve readability. |
| SVG fixed at 1100x520 | Not responsive | Low priority: matches all other dashboards. |

---

### 4.2 Dashboard 5 — Person-Topic Sentiment Fingerprint

**Intended design:**

> [TODO: Insert hand-drawn mock-up or wireframe image here]

The intended design was a two-panel view:
- **Top panel:** 6-row x 15-column heatmap with cell color = avg sentiment, columns grouped by topic industry (fishing/tourism/neutral), border thickness = participation count, dashed border = gov gap
- **Bottom panel:** 6x6 pairwise Pearson correlation matrix showing agreement/disagreement between persons
- Interactive highlights linking the two panels (hovering an agreement cell highlights both persons' heatmap rows)
- Person and topic dropdown filters for the detail table

**Actual design — visual encoding:**

The implemented dashboard (`dashboard_5.py`, 614 lines) delivers both panels:

**Heatmap panel:**
- **Marks:** Rounded rectangles (58x38 px each) in a 6x15 grid.
- **Channels:**
  - *Cell fill* = average sentiment on a diverging warm scale: green tones for positive (`rgb(107,155,123)` at +1.0), coral tones for negative (`rgb(196,119,106)` at -1.0), warm cream at zero, gray (#D5CFC8) for unknown sentiment, lightest (#F5F0EB) for no data
  - *Cell text* = numeric sentiment value (+0.XX format) or "?" for unknown
  - *Cell border thickness* = participation count (1px to 3px, scaled by count/3)
  - *Cell border dash* = dashed (#C4776A) when government records are missing
  - *Column group header* = colored bar above columns: blue (#5B8FA8) for fishing topics, orange (#D4956B) for tourism, gray (#B8AFA7) for neutral
  - *Row label* = person name (bold, 11px)
  - *Column label* = topic short name (rotated -45 degrees)

**Agreement matrix panel:**
- **Marks:** Rounded rectangles (42x42 px) in a 6x6 symmetric grid.
- **Channels:**
  - *Cell fill* = Pearson correlation on a diverging scale: green for positive (allies), coral for negative (opponents), gray for insufficient data
  - *Cell text* = correlation value (e.g., "0.72", "-0.31") or "n/a"
  - *Diagonal cells* = gray with "—" marker

**Interactions:**

1. **Heatmap hover:** Cross-hair highlight dims all cells except the hovered cell's row and column. A tooltip shows person, topic, sentiment (with color badge), participation count, and gov-missing count.
2. **Heatmap click:** Locks the cross-hair highlight on the clicked cell. Click again or click empty space to unlock.
3. **Agreement matrix hover:** Highlights both persons' entire rows in the heatmap above, making aligned and clashing topics immediately visible.
4. **Person dropdown** (`mo.ui.dropdown`): Filters the detail table to one person.
5. **Topic dropdown** (`mo.ui.dropdown`): Filters the detail table to one topic.
6. **Detail table** (`mo.ui.table`): Shows all participation records with: Person, Topic, Type, Title, Sentiment, Reason. Sortable and filterable.

**Gap analysis:**

| Intended | Actual | Gap |
|----------|--------|-----|
| Click agreement cell to lock both rows highlighted | Only hover highlights (no click lock on agreement cells) | Minor: the hover effect is sufficient for comparison. Click lock on agreement cells would be a nice addition. |
| Organization-level agreement | Person-level only | By design: v3 scoped the fingerprint to persons. Organization analysis is in D6 (earlier versions) or could be a separate view. |
| Responsive layout | Fixed SVG dimensions | Low priority: consistent with all dashboards. |

---

### 4.3 Dashboard 6 — Plan Outcome Tracker

**Intended design:**

> [TODO: Insert hand-drawn mock-up or wireframe image here]

The intended design was a three-panel view:
- **Swim lane timeline:** Topic rows with plan lifespan bars (colored by final status), discussion presence circles, and status transition markers
- **Cumulative funnel:** Trapezoid visualization showing plan progression (introduced -> planned -> in_progress -> completed) with drop-off annotations
- **Type x status matrix:** Cross-tab heatmap of plan type vs. final status
- Topic filter, plan type filter, and government-missing toggle

**Actual design — visual encoding:**

The implemented dashboard (`dashboard_6.py`, 473 lines) delivers all three panels:

**Swim lane timeline:**
- **Marks:** Horizontal rounded rectangles (plan bars, 8px height), circles (discussion presence, 3-8px radius), and small circles (status transition dots on bars, 3px radius).
- **Channels:**
  - *Bar X span* = meeting range (first meeting to last meeting of the plan)
  - *Bar Y position* = topic row, stacked within row for multiple plans
  - *Bar color* = final status: gray (#B8AFA7) for introduced, orange (#D4956B) for planned, blue (#5B8FA8) for in_progress, green (#6B9B7B) for completed
  - *Bar stroke* = coral (#C4776A) dashed when gov-missing toggle is on and plan is absent from government data
  - *Discussion circle size* = sqrt-scaled discussion count per meeting
  - *Discussion circle position* = above the plan bar lane, at the meeting's X coordinate
  - *Transition dot color* = status color at that specific meeting

**Cumulative funnel:**
- **Marks:** Centered rounded rectangles, one per status stage.
- **Channels:**
  - *Bar width* = count of plans reaching that stage (proportional to max)
  - *Bar color* = status color (matching swim lanes)
  - *Text overlay* = stage name + count + percentage
  - *Annotation* = red "drop-off" count between stages (e.g., "↓ 2 dropped")

**Type x status matrix:**
- **Marks:** Small rounded rectangles in a grid.
- **Channels:**
  - *Row* = plan type (proposal, report, travel, feedback, etc.)
  - *Column* = final status (introduced, planned, in_progress, completed)
  - *Cell fill opacity* = count relative to maximum
  - *Cell fill color* = status color
  - *Cell text* = count value

**Interactions:**

1. **Hover plan bar:** Bar expands (8px -> 12px height), darkens, gains drop-shadow. Tooltip shows: plan title, type, topic, final status (with colored badge), meeting range, and gov-data flag.
2. **Topic dropdown** (`mo.ui.dropdown`): Filters swim lanes to one topic (or all).
3. **Plan type dropdown** (`mo.ui.dropdown`): Filters to one plan type (or all).
4. **Gov-missing toggle** (`mo.ui.checkbox`): When enabled, plans absent from government data get dashed coral outlines and full opacity.
5. **Detail table** (`mo.ui.table`): Shows plan participation records: Plan title, Type, Topic, Status, Meetings, Participant, Sentiment, Reason, In Gov?.

**Gap analysis:**

| Intended | Actual | Gap |
|----------|--------|-----|
| Click plan bar to filter detail table | Detail table shows all plans for selected filters | Could add click-to-filter, but dropdown filtering is already effective. |
| Discussion-to-plan linking (which discussions led to which plans) | Not visualized as explicit edges | The `discussion_plans` table with status is used for lifecycle computation, but the visual connection between discussion dots and plan bars is implicit (same topic row) rather than explicit (drawn edges). Adding hover-to-highlight-related-discussions would strengthen the "action vs. rhetoric" story. |
| Animated transitions on filter change | Static re-render | Marimo's `mo.iframe()` replaces the entire SVG on filter change. Smooth transitions would require a persistent DOM (e.g., D3.js). |
| Responsive layout | Fixed 1100px width | Consistent with all dashboards. |

---

## Part 5. Findings

### Finding 1: Clear Fishing-Tourism Polarization with a Moderate Center

The **Sentiment Fingerprint heatmap (D5)** reveals a clear two-bloc structure among board members:

- **Pro-fishing bloc:** Teddy Goldstein shows consistently positive sentiment on fishing-related topics (fish vacuum, deep fishing dock, low-volume crane) and negative or neutral sentiment on tourism proposals. His average sentiment of +0.344 with a high variance (0.689) indicates strong, polarized positions.
- **Pro-tourism bloc:** Simone Kat shows the mirror pattern — positive on tourism topics (expanding tourist wharf, heritage walking tour, seafood festival) and skeptical of fishing infrastructure.
- **Moderate center:** Carol Limpet emerges as the most consistently positive member across both sectors (avg +0.655, lowest variance at 0.199), acting as a bridging figure. Ed Helpsford (+0.700) is similarly positive but with a housing/small-vessel focus.

The **pairwise agreement matrix** quantifies this: Teddy Goldstein and Simone Kat have one of the lowest Pearson correlations, confirming they are structural opponents. Carol Limpet correlates positively with most members, confirming her bridging role.

> [TODO: Insert annotated D5 screenshot highlighting the Teddy-Simone opposition and Carol's moderate profile]

### Finding 2: Sentiment Shifts Reveal Strategic Position Changes

The **Sentiment Timeline (D4)** adds a temporal dimension that the static heatmap cannot capture. Key observations:

- **Teddy Goldstein on affordable housing:** His sentiment drops from +1.0 (Meeting 6) to -1.0 (Meeting 9) — a complete reversal. Drilling into the detail table reveals this shift coincides with the proposal being linked to tourism infrastructure development, suggesting his opposition is strategic rather than principled.
- **Committee convergence on neutral topics:** Topics like "concert" and "renaming park himark" show all members clustering near +1.0, with the sentiment band narrowing to near-zero width. This confirms these are consensus items.
- **Late-meeting divergence:** In meetings 13-15 (journalist-only, not in government records), sentiment variance increases for fishing topics, suggesting contentious discussions that the government chose not to document.

> [TODO: Insert annotated D4 screenshot showing Teddy's affordable housing reversal]

### Finding 3: High Proposal Introduction Rate, Low Completion — Especially for Fishing

The **Plan Outcome Tracker (D6)** cumulative funnel shows:

| Stage | Plans reaching | % of introduced |
|-------|---------------|-----------------|
| Introduced | 73 | 100% |
| Planned | 71 | 97% |
| In progress | 53 | 73% |
| Completed | 46 | 63% |

Most plans clear the "introduced -> planned" gate easily (only 2 drop), but **27% of plans stall between "planned" and "completed."** The type-status cross-tab reveals that "take action" type plans have the highest completion rate, while "proposal" and "report" types are more likely to stall.

Filtering by topic shows fishing-related plans have a notably lower completion rate than tourism plans for the "in_progress -> completed" transition — potentially supporting FILAH's claim that the board deprioritizes fishing outcomes. However, the swim lane view also shows that fishing plans tend to span fewer meetings (shorter bars), suggesting they may be less complex rather than deliberately stalled.

> [TODO: Insert annotated D6 screenshot showing the funnel and topic-filtered swim lanes]

### Finding 4: Systematic Government Data Omissions Follow a Pattern

Across all three dashboards, the **government omission overlay** (dashed coral borders) reveals a non-random pattern:

- **Trip tracking:** Government records only 3 of 6 members' trips extensively (Carol Limpet: 69, Simone Kat: 67, Seal: 53). Ed Helpsford (0 vs. 61 in journalist data), Tante Titan (4 vs. 49), and Teddy Goldstein (1 vs. 43) are severely under-tracked.
- **Meeting coverage:** Meetings 13, 14, 15 are entirely absent from government records. The Sentiment Timeline (D4) shows these meetings contain some of the most divergent sentiment scores on fishing topics.
- **Discussion coverage:** 26 journalist-only discussions cluster around the later meetings and contentious topics, suggesting the government selectively reduced documentation as debates intensified.

This is the strongest finding for the journalist persona: the **pattern of omission itself is evidence of bias**, independent of the sentiment data.

> [TODO: Insert annotated screenshots showing dashed borders clustering on D4 and D6]

---

## Part 6. Reflections (Optional)

**Most proud of:** The dual-source comparison design. Rather than treating government omissions as missing data to impute, we made them a first-class visual element (dashed coral borders) woven into every dashboard. This transforms a data quality issue into the central analytical finding — the pattern of what the government chose not to record is itself the story.

**Least proud of:** The fixed-width SVG layouts. All dashboards use hardcoded 1100px widths, which limits usability on different screen sizes. A responsive approach (using viewBox or percentage-based sizing) would have made the dashboards more accessible, but we prioritized analytical depth over responsive polish given the time constraints.

---

## Part 7. Individual Contributions

[TODO: Fill in based on actual team contributions]

| Member | Contribution |
|--------|-------------|
| [Student 1] | Data investigation, cleaning, and merging. Dashboards 1-3 design and implementation. |
| [Student 2] | Dashboards 4-6 design, improvement plan iterations (v1-v3), peer review responses. |
| [Student 3] | Visual design sketches, user testing, report writing, video production. |

---

## Appendix A. Sketches Overview

> [TODO: Insert a single composite image showing all sketches created during the design process]

The following sketches were produced during the diverge-emerge-converge design process:

| # | Sketch | Phase | Outcome |
|---|--------|-------|---------|
| 1 | Radial sentiment network | Diverge | Implemented as D1 |
| 2 | Geographic trip map with zone classification | Diverge | Implemented as D2 |
| 3 | Participation bubble matrix with pie charts | Diverge | Implemented as D3 |
| 4 | Meeting timeline with sentiment lines | Diverge | Refined -> D4 |
| 5 | Person-topic heatmap (plain) | Diverge | Refined -> D5 |
| 6 | Plan status Sankey flow | Diverge | Rejected: too complex for 4 stages |
| 7 | Sentiment evolution timeline with bands | Emerge | Merged into D4 |
| 8 | Heatmap + pairwise agreement matrix | Emerge | Merged into D5 |
| 9 | Plan lifecycle funnel (final-status) | Emerge | Revised to cumulative funnel in D6 |
| 10 | Swim lane timeline with status bars | Emerge | Merged into D6 |
| 11 | Type x status cross-tab | Emerge | Added to D6 |
| 12 | Government omission dashed overlay | Converge | Applied across D4-D6 |
| 13 | Final D4: Sentiment Evolution Timeline | Converge | Implemented |
| 14 | Final D5: Person-Topic Sentiment Fingerprint | Converge | Implemented |
| 15 | Final D6: Plan Outcome Tracker | Converge | Implemented |

Sketches 1-6 represent the diverge phase (broad exploration), 7-11 represent the emerge phase (clustering and combining), and 12-15 represent the converge phase (final designs). The three implemented custom dashboards (D4, D5, D6) each combine elements from 2-3 emerge-phase sketches.
