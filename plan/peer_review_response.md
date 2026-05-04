# Response to Peer Review of Dashboards 4-6

Date: 2026-04-28

Addresses findings in `plan/claude_code_latest_dashboards_peer_review.md`.

---

## Changes made

### Critical — Static summaries upgraded to interactive tools

| Dashboard | Before | After |
|---|---|---|
| 4 (Coverage gap) | SVG-only aggregate bars + heatmap | SVG + `mo.ui.table` with 200+ omission detail rows, sortable/filterable by column |
| 5 (Timeline) | Discussion circles only, empty topic filter | Discussion circles + plan arcs (diamond markers with status colors), populated topic filter dropdown, show-plans and show-gov-gaps checkboxes |
| 6 (Org analysis) | SVG tooltips only, crashed on render | SVG + `mo.ui.table` of full organization participation reasons (40 rows, sortable), unknown sentiment markers |

Detail panel outputs now show joined labels: discussion title, plan title, person name, organization name, topic name, sentiment, and reason text where available.

### High — All 18 comparable tables now in coverage

Added to both the coverage summary bars and the heatmap (where applicable):

| Table | Status in previous version | Now |
|---|---|---|
| `discussion_topics` | Loaded but excluded from coverage | Included as "Disc-Topics" |
| `plan_topics` | Loaded but excluded | Included as "Plan-Topics" |
| `discussion_plans` | Loaded but excluded | Included as "Disc-Plans" |
| `refers_to` | Loaded but excluded | Included as "Refers-To" |
| `travel_links` | Loaded but excluded | Included as "Travel-Links" |
| `discussion_org_participations` | In coverage but not in heatmap | Now in heatmap ("Disc-Org") |
| `plan_org_participations` | In coverage but not in heatmap | Now in heatmap ("Plan-Org") |

The coverage computation now uses **left joins with `_in_gov` flags** instead of set comparison, preserving the full journalist-only rows for the detail table.

### High — Comparison logic replaced with left joins

Previous: `set(df[cols].apply(tuple, axis=1))` for both sides, then set difference.

Now:
```python
_merged = jour[_table].merge(
    gov[_table][_pks].drop_duplicates().assign(_in_gov=True),
    on=_pks, how="left", indicator=False,
)
_merged["_in_gov"] = _merged["_in_gov"].fillna(False)
_jour_only = _merged[~_merged["_in_gov"]]
```

This preserves all columns of omitted rows (sentiment, reason, status, etc.) for the detail panel.

### High — Plan lifecycle now shown on timeline

Dashboard 5 timeline now has two layers:
1. **Circles** — discussion presence at each meeting (as before)
2. **Diamonds** — plan status transitions at each meeting (new)

Plan status at each meeting is computed by joining `discussion_plans` through `meeting_discussions` to `meetings`, then tracking the highest status rank per plan per meeting. Diamond color encodes the plan status at that meeting point (gray=introduced, yellow=planned, blue=in-progress, green=completed).

A connecting line between first and last meeting shows the plan's span. Government-missing plans get dashed outlines when the "Mark gov-missing plans" checkbox is on.

### High — Funnel is now cumulative

Previous "funnel" showed final-status distribution (misleading: "introduced: 2" looked like only 2 plans were ever introduced).

Now shows **cumulative counts — plans reaching each stage**:

| Stage | Reached | Previous display |
|---|---:|---|
| introduced | 73 | 2 (final status only) |
| planned | 71 | 18 (final status only) |
| in_progress | 53 | 7 (final status only) |
| completed | 46 | 46 |

Drop-off counts between stages are shown as red arrows (e.g., "↓ 2" between introduced and planned).

Label changed from "Status funnel (all plans)" to "Cumulative funnel — plans reaching each stage".

### High — Organization alignment metric fixed

Previous: `np.mean(person_sentiment * org_sentiment)` with threshold ≥ 1 shared topic. Labeled "agreement score".

Now: **Cosine similarity** (`np.dot(p, o) / (||p|| * ||o||)`) with threshold ≥ 3 shared topics. Labeled "cosine similarity (≥3 shared topics)".

For persons below the threshold (< 3 shared topics with any organization), the dashboard now shows:
- Grayed-out bar (opacity 0.3)
- Label: "insufficient overlap: Nt < 3"
- Tooltip: "⚠ Below 3-topic threshold — unreliable"

This prevents false stakeholder-influence claims from sparse data.

### High — Null sentiment handling completed

Dashboard 6 bubble matrix now distinguishes three states:
1. **Colored circle** — known sentiment (green positive, red negative)
2. **Gray circle with "?"** — organization participated but sentiment is unknown
3. **Empty cell** — no participation

Unknown counts are tracked via `unknown_count` column in `org_topic_agg` (computed from `_sent_unknown` group). Tooltips show "Known: N, Unknown: M" when both exist.

Legend updated to include "unknown" entry.

### Medium — Reason text panels added

**Dashboard 6**: Full `mo.ui.table` below the SVG showing all 40 organization participation rows with: Organization, Topic, Type (discussion/plan), Sentiment, and complete Reason text. Sortable and filterable.

**Dashboard 1** (cross-cutting enhancement): 
- Built `participation_reasons` DataFrame joining all person participation CSVs with topic mappings (165 unique person-target pairs with reasons)
- Embedded reason text as a JSON lookup (`REASONS` variable) in Dashboard 1's iframe
- Added a floating `#reason-panel` div with CSS styling
- Modified `showPersonHighlight()` JS function to extract target IDs and display matching reason text from the lookup
- Panel auto-hides on deselect, persists on click-lock

### Medium — Data loading narrowed and labeled

Exception handler changed from `except Exception` to `except (FileNotFoundError, OSError)`. The `nonlocal` bug that crashed marimo's cell wrapper was fixed by using a mutable list `_csv_data_source = ["local"]` instead.

A data-source indicator dot (green = local, orange = remote) appears in the top-right of Dashboard 4's SVG.

### Medium — Topic filter wired up

Dashboard 5's topic filter dropdown is now:
- Populated with all 15 topic names from the data
- Default: "All topics"
- When a topic is selected, both the timeline swim lanes and the lifecycle bars filter to that single topic
- Filter cell depends on `topic_label_map` (reactive to data changes)

### Bug — Critical KeyError fixed

Dashboard 6 SVG cell referenced `_pr["agreement"]` but the org computation cell produces `cosine_sim`. This caused a crash (KeyError) every time the dashboard rendered. Fixed to `_pr["cosine_sim"]`.

---

## What was NOT changed (and why)

### Responsive layout
The review noted fixed 1100px SVG widths. Kept as-is because the existing Dashboards 1-3 use fixed sizes (1200px, 1020px, 800px). Responsive SVG layout would require refactoring all six dashboards for visual consistency — better done as a separate pass.

### Click-through from heatmap to detail
The review suggested clicking a heatmap cell to filter the detail table. The `mo.ui.table` is already filterable by column headers (type column filters to specific entity types). SVG click → reactive marimo state would require converting the SVG to an iframe with JS message passing, which adds complexity without changing the data story.

### Shared-row field equality checks
The review suggested checking whether shared rows have different sentiment/reason/status values across sources. The peer review of v1 confirmed that "for checked shared participation and lifecycle rows, values match exactly." Equality checks are deferred until the data changes.

### `docs/` static build
The `docs/` folder contains a pre-built HTML export. Rebuilding it is a deployment step, not a code fix. The user can run `python -m marimo export html index.py --no-sandbox -o docs/index.html` to update it.
