# Peer Review: Latest Three Dashboards in `index.py`

Date: 2026-04-28

Scope reviewed:
- `Source coverage gap` / `Source coverage gap detector`
- `Meeting timeline & plan lifecycle`
- `Organization stakeholder analysis`
- Implementation range: `index.py:3076-3786`
- Comparison target: `plan/improvement_plan_v2.md`

## Findings

### Critical - The delivered dashboards are mostly static summaries, not the planned investigative tools

The largest issue is that the implementation does not deliver the interaction model described in `improvement_plan_v2.md`. The plan called for detail panels, controls, filters, omission drilldowns, lifecycle transitions, reason text panels, and person-organization comparison details. The code mostly adds three static SVG panels with browser-native `<title>` hover text.

Evidence:
- Dashboard 4 renders only an aggregate coverage bar chart plus a heatmap: `index.py:3206-3338`.
- Dashboard 5 renders topic-level meeting dots plus final-status bars: `index.py:3389-3550`.
- Dashboard 6 renders an org-topic bubble matrix plus an alignment bar chart: `index.py:3616-3774`.
- The final tabs wire these static outputs directly: `index.py:3778-3786`.

What is bad:
- There are no click handlers, selected states, dropdowns, toggles, or detail panels in the new dashboards.
- The user cannot inspect actual omitted records, reason text, plan transitions, or supporting rows.
- The visualizations answer much weaker questions than their titles imply.

What should improve:
- Treat the current work as a rough visual sketch, not a finished dashboard implementation.
- Add the missing interactive analysis layers before spending time on cosmetic polish.
- Split data preparation from rendering and expose reusable derived dataframes that can drive detail views.

### High - `Source coverage gap` omits major tables and does not show the actual gaps

Dashboard 4 only compares six entity tables and six relationship tables. It loads more tables than it uses, then drops several important omission sources from the coverage summary and heatmap.

Evidence:
- Loaded tables include `discussion_topics`, `plan_topics`, `discussion_plans`, `refers_to`, and `travel_links`: `index.py:3086-3093`.
- Coverage definitions exclude those tables: `index.py:3121-3136`.
- The heatmap only includes `Discussions`, `Plans`, `Disc-People`, and `Plan-People`: `index.py:3172`.

Tables with known missing government coverage that are not surfaced in the coverage dashboard:

| Table | Journalist rows | Government rows | Missing by row count |
|---|---:|---:|---:|
| `discussion_topics` | 102 | 76 | 26 |
| `plan_topics` | 73 | 54 | 19 |
| `discussion_plans` | 96 | 70 | 26 |
| `refers_to` | 43 | 30 | 13 |
| `travel_links` | 22 | 16 | 6 |

What is bad:
- A dashboard named "Source coverage gap" hides several source-coverage gaps.
- It does not distinguish "entity missing" from "relationship missing" deeply enough.
- It does not show actual omitted rows, joined labels, reason text, or affected meetings/plans/topics.
- It only gives aggregate counts, so the investigative claim cannot be audited from the UI.

What should improve:
- Add all comparable entity and link tables to the coverage model.
- Build `source_coverage_entities` and `source_coverage_links` as real dataframes, not only count rows.
- Add a detail panel listing journalist-only records with joined labels: topic, meeting, discussion, plan, person, organization, place, sentiment, and reason.
- Include organization participation in the heatmap, even if it turns out to have zero omissions, because that itself is useful evidence.

### High - `Source coverage gap` uses fragile comparison logic

The comparison logic uses `set(...)` over selected primary-key columns instead of explicit left joins with `_merge` indicators.

Evidence:
- Entity comparison: `index.py:3139-3143`.
- Link comparison: `index.py:3144-3148`.
- Percent missing calculation: `index.py:3150-3151`.

What is bad:
- Set comparison silently collapses duplicate rows. If duplicate relationship rows ever carry distinct reasons, statuses, or sentiments, this method loses information.
- It does not retain the omitted records, so later panels cannot reuse the coverage flags.
- It does not compute or report government-only rows, which would be important if future data changes break the "government is subset" assumption.
- It does not compare shared-row field equality, so it cannot detect changed status, reason, sentiment, or label values.

What should improve:
- Use the left-join strategy from the plan:

```python
merged = journalist_df.merge(
    government_df,
    on=primary_key_columns,
    how="left",
    indicator=True,
    suffixes=("_jour", "_gov"),
)
```

- Keep `left_only`, `both`, and optionally `right_only` flags.
- Preserve omitted rows as data, not only as counts.
- Add validation checks for shared rows where non-key columns differ.

### High - `Meeting timeline & plan lifecycle` does not actually show plan lifecycle over time

The timeline only shows topic presence by meeting and discussion count. Plans are not placed on the meeting timeline, and there are no plan progression arcs or status markers.

Evidence:
- Timeline data groups only by topic, meeting, and discussion count: `index.py:3342-3349`.
- Rendering draws topic swim lanes with circles sized by `n_discussions`: `index.py:3420-3459`.
- Plan status is rendered only in a separate aggregate bar section: `index.py:3461-3500`.

What is bad:
- The title promises a meeting timeline and plan lifecycle, but the timeline does not show plans.
- There is no plan-level path from introduction to completion.
- The implementation ignores `meeting_plans` for plan placement across meetings.
- The user cannot tell which plan advanced, stalled, disappeared, or completed in which meeting.

What should improve:
- Build a `topic_lifecycle` dataframe with `plan_id`, `topic_id`, `plan_type`, `status`, `meeting_id_introduced`, `meeting_id_latest`, and source-coverage flags.
- Draw plan paths/arcs across the meeting axis.
- Show status badges at the meetings where status changes happen.
- Add tooltips/detail rows with plan title, status, meeting, and related discussion.

### High - The lifecycle funnel is mislabeled and analytically misleading

The "Status funnel (all plans)" is not a funnel. It is a final-status distribution.

Evidence:
- Code computes each plan's maximum status rank: `index.py:3351-3359`.
- `funnel_df` groups plans by that final status only: `index.py:3370-3373`.
- The rendered label says "Status funnel (all plans)": `index.py:3506-3508`.

Current final-status distribution from the implementation logic:

| Final status | Count |
|---|---:|
| completed | 46 |
| in_progress | 7 |
| introduced | 2 |
| planned | 18 |

But the actual cumulative "reached this stage" counts are:

| Reached stage | Count |
|---|---:|
| introduced | 74 |
| planned | 72 |
| in_progress | 53 |
| completed | 46 |

What is bad:
- Calling final-status distribution a funnel makes the user read "introduced: 2" as only two plans were introduced, when all 74 plans reached introduction.
- It obscures drop-off between stages.
- It does not answer the plan's intended question: "what fraction of plans actually got done?"

What should improve:
- Rename the current chart to "Final status distribution" if keeping it.
- Add a real cumulative funnel: introduced -> planned -> in_progress -> completed.
- Show drop-off counts and percentages between stages.

### High - Organization alignment uses the wrong metric

Dashboard 6 claims to show board member alignment with organizations, but the implementation uses mean product of sentiment values, not Pearson correlation. It also allows alignments based on only one shared topic.

Evidence:
- Shared-topic threshold is `>= 1`: `index.py:3598-3599`.
- Score is `np.mean(_pvals * _ovals)`: `index.py:3600-3602`.
- The plan called for Pearson correlation with enough shared topics, not a dot-product agreement score.

Observed output from the current implementation:

| Person | Best organization | Score | Shared topics |
|---|---|---:|---:|
| Ed Helpsford | Builders Association | 1.000 | 1 |
| Teddy Goldstein | Builders Association | 1.000 | 1 |
| Simone Kat | Saltwater Serenades | 0.750 | 2 |
| Tante Titan | Daughters of Port Grove | 0.500 | 3 |
| Seal | Daughters of Port Grove | 0.200 | 1 |
| Carol Limpet | PTA | 0.000 | 1 |

What is bad:
- A one-topic overlap can appear as the strongest alignment.
- The score is not normalized for each person or organization profile.
- It rewards matching sign and magnitude, but it is not a correlation.
- It cannot support the plan's stronger claim about suspicious mirroring.

What should improve:
- Use Pearson correlation only when there are at least three shared topics.
- If the data is too sparse for reliable correlation, say so in the dashboard rather than forcing a weak metric.
- Show shared-topic count prominently and de-emphasize any result below the threshold.
- Consider cosine similarity as a fallback, but label it correctly and keep the threshold.

### High - Null sentiment handling is incomplete

The plan explicitly said blank sentiment should be shown as unknown, not hidden or coerced to neutral. The implementation parses blank sentiment as `NaN`, but then drops those rows from several views without rendering unknown counts.

Evidence:
- Sentiment conversion correctly uses `pd.to_numeric(..., errors="coerce")`: `index.py:3105-3110`.
- Organization sentiment aggregation filters to `sentiment.notna()`: `index.py:3565-3568`.
- Person and organization vectors also filter to `sentiment.notna()`: `index.py:3587-3590`.
- Missing sentiment exists in the data:
  - `discussion_people_participations`: 5 of 99 rows.
  - `plan_people_participations`: 4 of 75 rows.
  - `discussion_org_participations`: 4 of 23 rows.
  - `plan_org_participations`: 2 of 17 rows.

What is bad:
- Unknown sentiment becomes invisible in Dashboard 6.
- Empty org-topic matrix cells can mean either "no participation" or "participated but sentiment unknown."
- The user loses a data-quality signal that the plan explicitly required.

What should improve:
- Track `unknown_sentiment_count` separately in org-topic and person-topic aggregates.
- Render unknown-only cells as gray with a `?`.
- Include unknown sentiment counts in tooltips and detail panels.
- Exclude unknowns from averages, but do not remove them from participation counts.

### Medium - Reason text is technically present but practically unusable

The plan emphasized reason text as a high-impact improvement. The implementation only puts short reason snippets inside SVG `<title>` elements.

Evidence:
- Organization reasons are grouped with `head(3)`: `index.py:3569-3573`.
- Tooltip text truncates each reason to 80 characters: `index.py:3704-3705`.
- Dashboard 1 still has no participation reason enhancement; searches show no `participation_reasons` dataframe.

What is bad:
- Native SVG title tooltips are hard to read, not searchable, not persistent, and not suitable for multi-sentence explanations.
- The implementation drops discussion title, plan title, status, and participation type from the reason context.
- The promised reason text panel was not implemented.
- Dashboard 1 was not enhanced with reason text even though the plan listed it as a cross-cutting improvement.

What should improve:
- Build a reusable `participation_reasons` dataframe.
- Add an HTML detail panel beside the org matrix and coverage dashboard.
- Show full reason text with source row context.
- Add reason text to Dashboard 1 hover/click behavior as originally planned.

### Medium - Data loading fallback can hide real failures and create non-reproducible results

The CSV loader catches any exception and falls back to GitHub raw URLs.

Evidence:
- Broad exception handler and fallback: `index.py:3077-3084`.

What is bad:
- A local schema error, bad path, parse failure, or data issue can silently switch the app to remote data.
- The remote branch may not match this repository checkout.
- In offline or restricted environments the fallback will fail late and unclearly.

What should improve:
- Only fall back for file-not-found conditions where remote loading is intentional.
- Surface parse/schema errors directly.
- Add a visible data-source indicator: local files vs remote fallback.
- Prefer bundled local data for reproducible review and static export.

### Medium - The dashboards are visually dense and not responsive

All three dashboards use fixed `1100` pixel SVG widths with small text, truncated labels, and no responsive layout.

Evidence:
- Dashboard 4 fixed width: `index.py:3211`.
- Dashboard 5 fixed width: `index.py:3403`.
- Dashboard 6 fixed width: `index.py:3632`.
- Labels are truncated throughout, for example `[:32]`, `[:30]`, `[:18]`, `[:28]`: `index.py:3283`, `index.py:3432`, `index.py:3677`, `index.py:3684`.

What is bad:
- Long topic and organization names lose meaning.
- On smaller screens the dashboards will likely overflow.
- The dense SVGs provide no table/detail fallback for careful inspection.

What should improve:
- Add responsive containers or smaller per-panel layouts.
- Use detail panels instead of forcing every label into the SVG.
- Keep short labels in the chart, but show full labels in accessible tooltips/details.

### Low - Syntax passes, but no runtime/export verification was documented

`python -m py_compile index.py` passes. That confirms Python syntax only.

What is still unverified:
- Marimo runtime behavior.
- Static export behavior under `docs/`.
- Remote fallback behavior.
- Tooltip and SVG rendering in browser.
- Whether the published `docs/` build includes the new dashboards.

What should improve:
- Run the Marimo app locally after dashboard changes.
- Rebuild `docs/` if the repository expects static output.
- Add a small smoke-test checklist for the six tabs.

## Dashboard-by-Dashboard Assessment

### Dashboard 4: Source coverage gap

Good parts:
- Uses journalist data as the canonical superset.
- Sorts and normalizes some source data before use.
- Correctly highlights the high-level government coverage gap for several major tables.

Bad parts:
- Missing many comparable tables.
- No actual omission records.
- No detail panel.
- No filters.
- No click interactions.
- No reason text.
- No reusable omission flags for the later dashboards.

Priority fix:
- Replace the count-only implementation with a real coverage dataframe and a detail panel. The chart should be a gateway into the omitted rows, not the whole dashboard.

### Dashboard 5: Meeting timeline & plan lifecycle

Good parts:
- Meetings are sorted by numeric meeting ID, which avoids the known `date` label problem.
- The top timeline gives a quick overview of topic recurrence.

Bad parts:
- It does not show plan lifecycle on the timeline.
- It does not show individual plan transitions.
- It ignores government omission overlays.
- The funnel is mislabeled and analytically wrong.
- No topic filter, color mode, or omission toggle.

Priority fix:
- Put plans on the meeting axis. The central visual should answer "which plan moved when?", not only "which topic had discussions?"

### Dashboard 6: Organization stakeholder analysis

Good parts:
- The org-topic matrix is a reasonable starting shape for the organization data.
- Average sentiment and participation count are useful encodings.

Bad parts:
- The reason text panel is missing.
- Unknown sentiment is hidden.
- The person-organization alignment metric is invalid for the claim being made.
- One-topic alignments are displayed as strong evidence.
- No filters by topic, organization, or participation type.

Priority fix:
- Remove or relabel the alignment section until a statistically defensible metric can be computed. The current output risks creating false stakeholder-influence claims.

## Suggested Remediation Sequence

1. Fix the data layer first.
   - Implement `source_coverage_entities`, `source_coverage_links`, `topic_lifecycle`, `meeting_agenda`, `org_participation`, and `participation_reasons`.
   - Keep row-level records and source flags.
   - Add checks for missing tables, missing columns, duplicate keys, and shared-row mismatches.

2. Repair Dashboard 4.
   - Add all comparable tables.
   - Add omitted-record detail tables.
   - Add topic/entity filters.
   - Show entity omissions and link omissions separately.

3. Repair Dashboard 5.
   - Add plan paths across the meeting axis.
   - Replace the final-status "funnel" with a real cumulative funnel.
   - Add government-missing markers using the coverage flags.
   - Add a topic filter before adding more visual density.

4. Repair Dashboard 6.
   - Add a persistent reason text panel.
   - Render unknown sentiment explicitly.
   - Replace the alignment score with Pearson correlation only when there are enough shared topics.
   - If the data is too sparse, show "insufficient overlap" rather than a misleading score.

5. Add Dashboard 1 reason text enhancement.
   - This was part of the approved plan and has not been delivered.
   - It should reuse the same `participation_reasons` dataframe.

6. Verify the app.
   - Run syntax check.
   - Run the Marimo app.
   - Smoke-test all six tabs.
   - Rebuild `docs/` if this repo expects the static site to reflect `index.py`.

## My Suggestions

1. Make Dashboard 4 the anchor story.
   The strongest investigative narrative is still government omission. Put the row-level omission detail front and center, then let the other dashboards reuse those flags.

2. Do less in each SVG and more in linked details.
   The data has rich text explanations. SVG is good for overview, but it is poor for reading reasons, comparing rows, and auditing omissions. Use SVG for patterns and HTML tables/panels for evidence.

3. Rename weak metrics honestly.
   If a chart shows final status, call it final status. If a score is mean sentiment agreement, call it that. Do not label these as lifecycle funnel or correlation until the data logic matches.

4. Add reliability thresholds.
   Any person-org alignment should require at least three shared topics and should show overlap count. Sparse results should be hidden or marked as insufficient evidence.

5. Preserve unknowns as first-class data.
   Unknown sentiment is not noise here. It may indicate incomplete source collection, especially around sensitive plans. Show it explicitly.

6. Create a small validation cell near the data prep.
   A compact summary of row counts, missing counts, duplicate key counts, and shared-row mismatches would make future dashboard changes safer and easier to review.

7. Prioritize auditability over visual novelty.
   The current dashboards look like summaries, but the project needs evidence trails. Every aggregate should let the user answer: "Which records caused this number?"

