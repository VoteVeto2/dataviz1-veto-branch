# Review of `improvement_plan_v1.md`

## Verdict

The plan is a good idea overall. It correctly identifies the main missed opportunity: the project has enough relational data to move beyond static sentiment summaries into source reliability, timelines, stakeholder influence, and geographic context.

The priority order should change slightly. The strongest story in the data is not broad "government vs journalist disagreement"; it is that the government dataset appears to be a subset of the journalist dataset. Shared rows match, while the journalist source contains many additional meetings, plans, places, discussions, and participation records.

## Database Cross-Check

Observed data shape:

- `data/` contains 59 files total, including `database_gov.db` and `database_jour.db`.
- Each source folder has 21 CSV files with matching schemas.
- The SQLite databases mirror the relational shape and add useful derived/location tables: `loc_travel` exists in both databases, and `loc_topic` exists in `database_jour.db`.
- The app currently loads precomputed JSON/GeoJSON files rather than querying the CSVs or SQLite databases directly.

Important source differences:

- Journalist has 16 meetings; government has 13.
- Journalist has 101 discussions; government has 75.
- Journalist has 74 plans; government has 55.
- Journalist has 99 discussion-person participation rows; government has 71.
- Journalist has 75 plan-person participation rows; government has 49.
- Journalist has 172 places; government has 93.
- For checked shared participation and lifecycle rows, values match exactly. The difference is missing coverage, not changed sentiment/reason values.

## Corrections to the Existing Plan

- Keep the government vs journalist idea, but rename it to a coverage gap or omission detector. Do not frame the first version around sentiment disagreements unless later checks find examples.
- The plan says "16 meetings" as general timeline data, but the government source has only 13. Use journalist as the complete timeline and mark government-missing items.
- `meetings.csv` does not contain real dates; its `date` values are labels like `Meeting 16`. Sort by the numeric suffix in `meeting_id`, not by the `date` column.
- Organization participation is useful, but it does not drive source discrepancy. Org participation rows are identical across government and journalist for the checked CSVs.
- Plan type and status values need normalization before visualization. Examples include `Report` vs `report`, `Feedback` vs `feedback`, and `Completed` vs `completed`.
- Some sentiment values are blank, especially around deep fishing dock rows. Treat missing sentiment explicitly instead of coercing to neutral.

## Recommended Priority

1. Build a government omission overlay.
   This is the clearest investigative angle. Show which journalist records are absent from government data across meetings, discussions, plans, people participation, places, and travel links.

2. Add reason text to existing sentiment interactions.
   This is the cheapest high-impact improvement. Existing participation CSVs already contain readable explanations, and the current radial sentiment view lacks the "why" behind scores.

3. Add a compact plan lifecycle view.
   This is low effort and well supported by `plans.csv`, `discussion_plans.csv`, `meeting_plans.csv`, and `plan_topics.csv`. Normalize case first.

4. Add a meeting timeline after the lifecycle data is clean.
   Timeline is valuable, but it needs careful joins and ordering. It should reuse the omission flags from priority 1.

5. Add organization influence as an overlay, not a standalone first pass.
   The organization data is small enough to work well as filters, badges, or side panels connected to topics/plans. A full network could be useful later, but it is more design work than the data size justifies initially.

6. Add topic-place geography after the data narrative is stable.
   The map data supports this, but it should come after the source-difference and lifecycle story are clear.

## Practical Guidelines

- Use the journalist dataset as the canonical superset, then left-join government data to create `in_gov_data` flags.
- Track omission separately for entities and relationships. Missing a plan is different from having the plan but missing a person participation row.
- Normalize categorical fields at load time: lowercase `plan_type`, lowercase `status`, and map known display labels afterward.
- Preserve null sentiment as "unknown". Do not average it as zero.
- Keep source comparison metrics simple: count missing rows, percentage missing, and top missing topics/plans.
- Start with reusable derived tables rather than drawing logic. Suggested tables:
  - `source_coverage_entities`
  - `source_coverage_links`
  - `topic_lifecycle`
  - `participation_reasons`
  - `topic_place_links`
- Prefer augmenting the existing dashboards before adding a fourth major dashboard. The current app already has dense visuals; small overlays and tooltips will land faster.
- If using marimo, keep data preparation in separate cells from UI controls and visual rendering so the dependency graph stays readable.

## Suggested First Implementation Slice

Create one coverage dataset from the CSVs or SQLite databases:

- For each comparable table, compute `journalist_count`, `government_count`, `journalist_only_count`, and `government_only_count`.
- For key relationship tables, list journalist-only records with joined labels: meeting label, topic, discussion title, plan title, person, organization, and place.
- Display the result as a source coverage panel plus small badges in the existing sentiment map where `in_gov_data` is false.

This gives the project a stronger investigative claim with limited UI risk.
