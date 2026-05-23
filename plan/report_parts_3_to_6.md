# COOTEFOO Board Investigation — Report (Parts 3–6)

VAST Challenge 2025 MC2

---

## Part 3. Visual Design

### 3.1 Design Process

Our design followed a **diverge-emerge-converge** cycle over three iterations:

1. **Data investigation** (diverge): Exploratory analysis in a Jupyter notebook (`notebook/data_investigation.ipynb`) mapped the relational schema (21 tables, two parallel sources), revealed coverage gaps between government and journalist records, and identified clear pro-fishing vs. pro-tourism sentiment clusters among the six board members.

2. **First-round sketches** (diverge): We independently produced sketches exploring different encodings — radial sentiment networks, geographic trip maps, heatmaps, Sankey flows, timelines, and bubble matrices. Priority went to designs that expose **bias patterns** rather than summarize data, and that leverage the **dual-source comparison** as a forensic layer.

3. **Critique and clustering** (emerge): We grouped sketches by analytical question (sentiment polarity, geographic behavior, participation volume, temporal dynamics, relational alignment, action vs. rhetoric) and identified the strongest encoding per question. Three initial custom dashboards (D4: sentiment timeline, D5: person-topic heatmap, D6: plan lifecycle) were built and peer-reviewed. The review found them "mostly static summaries, not investigative tools," triggering a major rebuild.

4. **Consolidation** (converge): We recognized that the three separate dashboards (timeline, heatmap, plan tracker) fragmented the investigative story across tabs. We designed a single integrated view — **The Committee, Charted** — as a sentiment constellation with a trip ribbon, placing the full relational structure (who said what about which topic, and where they actually went) in one interactive page. This became the final Dashboard 4, replacing D4–D6.

### 3.2 Sketches — Design Path

**Sketch 1 — Radial Sentiment Network (diverge)**
Board members on an outer ring, topic clusters at the center, edges colored by sentiment. Became Dashboard 1.
*Encoding:* Radial position = person; edge hue = sentiment; edge presence = participation; node shape = discussion vs. plan.
*Rationale:* Shows the complete person-topic structure at a glance, making polarization visible immediately.

**Sketch 2 — Geographic Trip Map (diverge)**
Island map with colored dots for visited locations, sized by frequency, with a shoreline bias chart. Became Dashboard 2.
*Encoding:* Geographic position = place; dot color = zone type; dot size = frequency; sidebar bars = zone bias per person.
*Rationale:* Travel behavior proxies undisclosed allegiances — a board member claiming neutrality who only visits fishing docks is newsworthy.

**Sketch 3 — Participation Bubble Matrix (diverge)**
Person x metric grid where each cell is a pie chart (area = count, slices = focus type). Became Dashboard 3.
*Encoding:* Row = person; column = metric; area = count; slice angle = proportion; slice hue = fishing/tourism/both/other.
*Rationale:* Reveals who is most active and where activity concentrates.

**Sketch 4 — Meeting Timeline with Sentiment Lines (diverge)**
Horizontal M1–M16 timeline, one line per person, Y = sentiment, shaded band = committee range. Early version used bar charts; revised to connected lines.
*Encoding:* X = meeting; Y = avg sentiment; line color = person; point size = participation count.
*Rationale:* D1 collapses all meetings into averages. A person going from -1.0 to +1.0 looks the same as one always at 0.0. The timeline reveals *who shifted and when*.

**Sketch 5 — Person-Topic Heatmap + Agreement Matrix (emerge)**
6x15 heatmap with cells colored by sentiment, grouped columns by industry. Below: 6x6 Pearson correlation grid.
*Encoding:* Row = person; column = topic; cell fill = diverging sentiment; column grouping = industry; lower grid = pairwise correlation.
*Rationale:* Makes row-vs-row comparison trivial and surfaces alliance structures invisible in the radial network.

**Sketch 6 — Plan Lifecycle Swim Lanes + Funnel (emerge)**
Topic rows with plan-lifespan bars colored by final status, plus a cumulative funnel showing introduction-to-completion drop-off.
*Encoding:* Y = topic; X span = meeting range; bar color = status; funnel width = count reaching stage.
*Rationale:* Answers "which proposals become reality?" — the action-vs-rhetoric layer missing from D1–D3.

**Sketch 7 — Consolidated Constellation (converge, pivotal)**
After the peer review revealed that sketches 4, 5, and 6 produced three separate "dashboard islands," we redesigned them as a single integrated view: a **sentiment constellation** with people on an inner ring and topics on an outer arc, edges encoding sentiment, a contextual side panel, and a trip ribbon at the bottom. This sketch combined the relational structure of sketch 5, the temporal depth of sketch 4 (via the rail panel's per-topic drill-down), and the trip patterns of sketch 2 into one page.
*Encoding:* Inner ring = people (halo size = opinion count); outer arc = topics (grouped by cluster); edge color = oklch sentiment gradient (red-opposed to green-in-favor); edge weight = conviction; right rail = dynamic detail panel; bottom ribbon = trip timeline.
*Rationale:* Eliminates tab-switching. A journalist can hover one person, see all their stances, their alignment with colleagues, a representative quote, *and* their travel pattern — in one view.

**Sketch 8 — Trip Ribbon (converge)**
Horizontal dot-per-trip timeline, one lane per person sorted by trip count, dot size = stops on trip. Designed as the bottom panel of sketch 7.
*Encoding:* X = date; Y lane = person; dot radius = stop count; filtering = linked to constellation hover (hover a person dims other lanes).
*Rationale:* The visit map (D2) shows *where*; the ribbon shows *when and how often*, linking the temporal pattern to the sentiment constellation above.

### 3.3 Designs Selected for Implementation

**Design A — Board Sentiment Bias Map (Dashboard 1)**
Radial network from sketch 1. Interactive hover/click on person nodes reveals topic connections and sentiment reasons. Red-glowing nodes flag journalist-only data.
*Analytical value:* Answers "is the board biased?" by showing the complete sentiment structure in a single view.

**Design B — Board Visit Map and Time Spent (Dashboard 2)**
Geographic map from sketch 2 with KNN-based zone reclassification, shoreline bias chart, and radial trip timeline.
*Analytical value:* Answers "do travel patterns reveal undisclosed allegiances?" by mapping physical behavior against claimed neutrality.

**Design C — The Committee, Charted (Dashboard 4)**
The consolidated constellation from sketches 7–8. A dark-themed editorial layout with a sentiment constellation (people-to-topic edges), a contextual right rail (dynamic person/topic panels with stats, quotes, and alignment scores), and a trip ribbon (536 field trips). Replaces the earlier D4–D6 trio.
*Analytical value:* Answers "who said what, who agrees with whom, and where did they go?" — combining sentiment alignment, relational structure, and travel patterns in one interactive page. The design helps the journalist persona (Marta Kowalska) build a narrative by letting her pin a person and immediately see their stance, allies, opponents, a direct quote, and their field activity.

---

## Part 4. Implementation

We implemented three custom interactive dashboards as marimo reactive notebooks. Each is both a standalone app (`dashboard_N.py`) and a tab within an integrated application (`index.py`). D1–D3 use hand-coded SVG with embedded JavaScript. D4 uses a React-based design rendered via `mo.iframe()`.

**Technology stack:** Python 3.13+, marimo >= 0.23.3, pandas 3.0.2, numpy 2.4.4, React 18 + Babel standalone (D4 only). No external charting libraries — all charts are custom.

**Running instance:** [TODO: Insert HuggingFace / deployment URL]

**Video demonstration:** [TODO: Insert YouTube URL]

---

### 4.1 Dashboard 1 — Board Sentiment Bias Map

**Intended design:**

> [TODO: Insert sketch/mock-up image]

A radial network with board members arranged around topic clusters. Edges connect members to topics they participated in, colored by sentiment. A detail panel shows participation reasons. Nodes with journalist-only data receive a red-glow treatment.

**Actual design — visual encoding:**

- **Marks:** Circles (person nodes, topic nodes), pentagons (discussions), squares (plans), curved edges.
- **Channels:**
  - *Radial position* = identity (inner ring: people, outer clusters: topics grouped by fishing/tourism)
  - *Edge color* = sentiment (green = support, red = oppose, gray = neutral)
  - *Edge presence* = participation link
  - *Node glow/dash* = journalist-only data (red glow + dashed border)
  - *Halo size* = participation count
- **Background:** Warm cream (#FDF8F4) with Anthropic-inspired palette.

**Interactions:**

1. **Hover person:** Dims all other nodes, reveals edges to connected topics, updates a bottom reason panel with the person's stated positions.
2. **Click person:** Locks the selection. Click again or empty space to unlock.
3. **Hover discussion/plan node:** Shows which people participated.

**Gap analysis:**

The implementation closely matches the intended design. Minor gap: the reason panel could support keyword search or filtering by topic, but the hover-driven workflow is sufficient for the investigative use case.

---

### 4.2 Dashboard 2 — Board Visit Map and Time Spent

**Intended design:**

> [TODO: Insert sketch/mock-up image]

Three-panel view: a shoreline bias chart showing each person's affinity for fishing vs. tourism zones, a geographic map with KNN-based zone classification, and a radial trip timeline.

**Actual design — visual encoding:**

- **Marks:** Dots on map (visit locations), person figures on shoreline chart, dots on radial timeline.
- **Channels:**
  - *Geographic position* = place lat/lon
  - *Dot color* = zone classification (fishing/tourism/government/commercial/residential)
  - *Dot size / opacity* = visit count or time spent (toggleable)
  - *Shoreline bar* = fishing-vs-tourism zone ratio per person
  - *KNN parameters* = adjustable distance and neighbor count for zone reclassification
- **Background:** Custom map rendering from GeoJSON.

**Interactions:**

1. **Click person figure** on shoreline chart to filter map and timeline to that person.
2. **Scroll-wheel zoom** on map, drag to pan.
3. **Hover dots** for formatted tooltip (place name, zone, visit details).
4. **Sidebar sliders:** KNN distance/neighbors, visit-count vs. time-spent mode toggle, date range slider.

**Gap analysis:**

| Intended | Actual | Gap |
|----------|--------|-----|
| Animated trip playback | Static dot positions | Low priority: the date range slider achieves temporal filtering without animation. |
| Zone boundary polygons | Dot-based display | Minor: KNN reclassification is shown via dot colors, not drawn zone boundaries. |

---

### 4.3 Dashboard 4 — The Committee, Charted

**Intended design:**

> [TODO: Insert sketch/mock-up image — the consolidated constellation from sketch 7]

A full-page editorial layout with three integrated panels: (1) a sentiment constellation connecting people to topics via sentiment-colored edges, (2) a contextual right rail that dynamically shows stats, stances, alignment scores, and quotes for the hovered/selected entity, and (3) a trip ribbon showing all 536 field trips as a dot timeline.

**Actual design — visual encoding:**

**Constellation (main panel):**
- **Marks:** Circles with animated halos (people), small circles (topics), quadratic bezier curves (edges).
- **Channels:**
  - *Inner ring position* = person identity (6 nodes at radius 92px from center)
  - *Outer arc position* = topic identity (15 nodes at radius 335px, spanning -0.55pi to +0.55pi)
  - *Halo radius* = number of topics the person opined on
  - *Edge color* = sentiment via oklch interpolation: `oklch(L C H)` where L=0.62+t*0.18, C=0.08+|s|*0.14, H=25 (negative) or 150 (positive). Red = opposed, straw = neutral, sage green = in favor.
  - *Edge stroke width* = conviction (0.6 + |sentiment| * 3.0)
  - *Edge visibility* = hidden by default; appears only on hover/click (reduces clutter)
  - *Edge curvature* = quadratic bezier with 18px perpendicular bend (visual elegance, reduces edge overlap)
  - *Node dimming* = unrelated nodes fade to 25% opacity on hover/select
  - *Halo animation* = subtle CSS pulse (3.6s period, staggered delays per person)

**Right rail (contextual panel):**
- **Default state:** Briefing text, legend explanation, global stats (members, topics, opinions, trips, discussions, meetings).
- **Person panel:** Name, role, opinion count, trip count, average sentiment (color-coded), pro/against ratio, flagship quote with sentiment-colored left border, ranked stance list (colored swatches + values), alignment with other members (horizontal bars showing Pearson correlation from -1 to +1).
- **Topic panel:** Topic name, cluster label, voice count, meeting count, average sentiment, discussion count, industry tags, representative quote, per-member stance list with role annotations, silent member count.

**Trip ribbon (bottom panel):**
- **Marks:** Circles (one per trip).
- **Channels:**
  - *X position* = date (linear scale, Mar 25 – Aug 5, 2040)
  - *Y lane* = person (sorted by trip count, descending)
  - *Dot radius* = number of stops on trip (1.2 + min(stops, 12) * 0.7)
  - *Dot opacity* = dimmed (0.12) for non-focused persons when a person is selected
  - *Month tick marks* = vertical dashed lines at month boundaries
- **Tooltip:** Traveler name, date, time range, stop count, first 5 places visited.

**Interactions:**

1. **Hover person node:** Shows all edges from that person (others hidden), dims unrelated nodes, updates rail to person panel, dims other persons' trip lanes.
2. **Hover topic node:** Shows all edges to that topic, dims unrelated nodes, updates rail to topic panel.
3. **Click node:** Pins the selection. Click again or click empty space to release.
4. **Click stance row in rail:** Navigates to the related person/topic (cross-linking between person and topic views).
5. **Hover trip dot:** Shows tooltip with date, time, stops, and place names.
6. **Click trip dot:** Focuses the constellation on that traveler.
7. **Escape key:** Clears all selections and restores default state.
8. **Constellation / Cluster toggle:** Switches topic layout between arc mode and grouped-column mode.

**Gap analysis:**

| Intended | Actual | Gap |
|----------|--------|-----|
| Government omission markers on edges | Not implemented | The constellation uses journalist data only. A future enhancement could add dashed edges or glow markers for government-absent participation records. |
| Topic-level temporal drill-down | Rail shows aggregate sentiment per person-topic | Adding a small sparkline in the rail showing meeting-by-meeting sentiment for the hovered person-topic pair would recover the temporal depth of the old D4 timeline. |
| Plan lifecycle information | Not visualized | The old D6 swim lanes and funnel are not included. This is a deliberate scope trade-off: the constellation prioritizes relational structure over plan lifecycle tracking. Plan data could be added as a secondary panel or tooltip layer. |
| Responsive layout | Fixed 1520px iframe | The dark-themed grid requires minimum 1460px width. Responsive reflow would require significant CSS restructuring. |

---

## Part 5. Findings

### Finding 1: Clear Fishing-Tourism Polarization with a Moderate Center

Hovering each member in **The Committee (D4)** constellation reveals a stark two-bloc structure:

- **Pro-fishing:** Teddy Goldstein's edges to fishing topics (fish vacuum, new crane, affordable housing) glow sage green (+0.50 to +1.00), while his edges to tourism topics (tourist wharf, marine life deck) are red (-0.50). His rail panel shows 6 pro / 3 against with avg sentiment +0.10.
- **Pro-tourism:** Simone Kat mirrors this — green edges to heritage walking tour (+1.00), marine life deck (+1.00), seafood festival (+0.75), but red to affordable housing (-1.00) and new crane (-0.50). Her rail shows avg +0.32 but high variance across the fishing-tourism divide.
- **Moderate bridge:** Carol Limpet shows uniformly green edges (all four opinions are positive: +0.50 to +1.00). Her alignment scores are positive with almost everyone, confirming she acts as a bridging figure.

The **alignment bars** in the person rail quantify this: Simone Kat and Teddy Goldstein have a correlation near -0.95 (structural opponents). Simone aligns most with Seal (+0.96), while Teddy's strongest ally would need more shared topics to compute reliably.

> [TODO: Insert annotated D4 screenshot with Simone Kat selected, showing red edges to fishing topics and green to tourism]

### Finding 2: Travel Patterns Contradict Claimed Neutrality

The **Visit Map (D2)** and **trip ribbon (D4 bottom panel)** together reveal mismatches between stated positions and physical behavior:

- **Tante Titan** has 8 opinions (all positive, avg +0.81) concentrated on tourism and civic topics — yet the trip ribbon shows relatively few trips compared to Simone Kat (134 trips) or Carol Limpet. Her travel is focused on government and ferry terminals rather than the tourism sites she vocally supports.
- **Ed Helpsford** shows 6 opinions averaging +0.58, focused on housing and small-vessel topics. His 61 journalist-recorded trips (0 in government records) represent the **largest government tracking gap** of any member.

Clicking Ed Helpsford in D4's constellation dims all other trip lanes, making his 61-trip dot pattern clearly visible — a pattern entirely invisible in government data.

> [TODO: Insert annotated D4 screenshot showing Ed Helpsford's trip ribbon with the constellation focused on him]

### Finding 3: The Committee's Hidden Consensus

The constellation's **default (unselected) state** — edges hidden, only halos and topic dots visible — is itself informative. The halo sizes immediately show that Simone Kat (10 opinions) and Tante Titan (8 opinions) are the most vocal members, while Seal (4 opinions, Committee Chair) is notably quiet.

Clicking through each topic via the rail's stance list reveals that several topics enjoy **unanimous support** despite the fishing-tourism divide: waterfront market, seafood festival, and heritage walking tour all show positive sentiment from every member who weighed in. The polarization concentrates on just 3-4 infrastructure topics (affordable housing, new crane, fish vacuum, marine life deck).

This nuance — that the board agrees on ~60% of topics and clashes on ~25% — is difficult to see in per-topic or per-person views alone. The constellation's edge-hiding default forces the viewer to actively explore, discovering consensus as a surprise rather than seeing conflict as the default framing.

> [TODO: Insert two annotated screenshots: (1) topic "waterfront market" selected showing all-green edges, (2) topic "affordable housing" selected showing red-green split]

---

## Part 6. Reflections

**Most proud of:** The consolidation of three separate dashboards into the single constellation view (D4). The earlier D4–D6 approach fragmented the investigation across tabs; the constellation lets a journalist hover one person and immediately see their stances, allies, opponents, a direct quote, and their travel pattern — all without switching views. The edge-hiding default was a deliberate design choice that rewards exploration over passive consumption.

**Least proud of:** Losing the plan lifecycle analysis (old D6's swim lanes and funnel) in the consolidation. The "which proposals stall?" question from the brief is no longer directly answered by the current dashboard set. A future iteration could add plan status as a secondary layer within the constellation — for example, encoding plan completion as topic-node size or adding a plan timeline to the rail panel.
