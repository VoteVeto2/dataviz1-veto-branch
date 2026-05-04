# VAST Challenge 2025 MC2 - Data Investigation & Merging Summary

## 1. Data Sources & Schema

Two parallel datasets collected by different actors about the same committee process: **Government** (`Collected_by_the_Government`) and **Journalist** (`Collected_by_the_Journalist`). Both share an identical relational schema of 21 tables (8 entity + 13 junction).

### Dimensions

| Table | Gov Rows | Jour Rows | Diff |
|-------|----------|-----------|------|
| meetings | 13 | 16 | +3 |
| people | 6 | 6 | 0 |
| organizations | 8 | 8 | 0 |
| topics | 15 | 15 | 0 |
| discussions | 75 | 101 | +26 |
| plans | 55 | 74 | +19 |
| places | 93 | 172 | +79 |
| trips | 194 | 342 | +148 |
| trip_places | 234 | 1363 | +1129 |

### Identical entities

People (6), Organizations (8), Topics (15) are byte-for-byte identical across both sources. No source-exclusive entities.

## 2. Coverage Gaps

### Meetings

Government covers Meetings 1-12 and 16. Journalist covers 1-16. Meetings 13, 14, 15 are journalist-only. Meetings 13 and 15 carry date-format labels (`07-03-40`, `07-17-40`) instead of `Meeting N`.

### Discussions & Plans

Discussions: 75 shared, 26 journalist-only. Plans: 55 shared, 19 journalist-only. Zero government-only in either. The extra items correspond to the 3 journalist-only meetings and additional travel-related activity.

### Trips

Government: 194 trips (Mar-Aug 2040). Journalist: 342 trips (same range). All 194 government trip IDs are a subset of the journalist's. Date bug: some dates use year prefix `0040` instead of `2040` (normalized during cleaning).

| Month | Gov | Jour |
|-------|-----|------|
| 2040-03 | 1 | 1 |
| 2040-04 | 46 | 79 |
| 2040-05 | 44 | 85 |
| 2040-06 | 52 | 90 |
| 2040-07 | 48 | 82 |
| 2040-08 | 3 | 5 |

### Places

Government: 93, Journalist: 172 (79 journalist-only). Journalist has much broader coverage of residential (32 vs 3) and commercial (91 vs 55) zones.

### Trip frequency by person

| Person | Gov | Jour |
|--------|-----|------|
| Carol Limpet | 69 | 69 |
| Simone Kat | 67 | 67 |
| Seal | 53 | 53 |
| Ed Helpsford | 0 | 61 |
| Tante Titan | 4 | 49 |
| Teddy Goldstein | 1 | 43 |

Government tracks only 3 people's trips extensively; Journalist captures all 6.

## 3. Sentiment & Stakeholders

### Person sentiment

| Person | Mean | Count | Std |
|--------|------|-------|-----|
| Seal | 0.108 | 24 | 0.050 |
| Teddy Goldstein | 0.344 | 32 | 0.689 |
| Simone Kat | 0.469 | 84 | 0.659 |
| Carol Limpet | 0.655 | 42 | 0.199 |
| Ed Helpsford | 0.700 | 40 | 0.405 |
| Tante Titan | 0.819 | 54 | 0.277 |

### Source divergence

For all 29 overlapping (person, topic) pairs, mean absolute sentiment divergence is **0.000**. Both sources record identical sentiments for shared records.

### Organization stances

- **Saltwater Serenades**: opposes affordable housing (-1.0) and new crane at Lomark (-1.0)
- **Tours Central Ticketing**: opposes new crane (-1.0), supports tourist wharf expansion (+1.0)
- **Paackland Container Inc.**: opposes tourist wharf expansion (-0.5)
- **Builders Association** and **Industrial Shipping**: support affordable housing (+1.0)

## 4. Topic Timeline & Plan Types

### Temporal phases

- **Early** (Meetings 1-3): fish_vacuum, seafood_festival, deep_fishing_dock
- **Mid** (Meetings 4-9): renaming_park_himark, new_crane_lomark, low_volume_crane, affordable_housing, waterfront_market, heritage_walking_tour, concert, statue_john_smoth, name_inspection_office
- **Late** (Meetings 10-16): marine_life_deck, name_harbor_area, expanding_tourist_wharf, concert (Meeting 16)

### Plan type distribution

| Type | Gov | Jour |
|------|-----|------|
| travel | 16 | 22 |
| report | 10 | 12 |
| proposal | 10 | 14 |
| feedback | 6 | 9 |
| discussion | 5 | 5 |
| presentation | 4 | 6 |
| take action | 4 | 6 |

### Status inconsistency

Both `completed` and `Completed` appear in `discussion_plans.status` (case mismatch).

## 5. Merge Strategy & Cleaned Output

### Strategy

- **Entity tables** (people, organizations, topics): used as-is (identical)
- **Meetings**: union of both sources
- **Discussions, plans, places**: union, deduplicated by primary key
- **Junction tables**: union with `source` column, deduplicated on natural key
- **Participation tables**: union with `source` column, deduplicated on all non-source columns
- **Trip tables**: union with `source` column, date normalization (`0040` -> `2040`)

### Output inventory (`data/cleaned_data/`)

| File | Rows | Cols |
|------|------|------|
| people.csv | 6 | 3 |
| organizations.csv | 8 | 2 |
| topics.csv | 15 | 3 |
| meetings.csv | 16 | 3 |
| discussions.csv | 101 | 3 |
| plans.csv | 74 | 4 |
| places.csv | 172 | 6 |
| trips.csv | 536 | 5 |
| trip_people.csv | 536 | 4 |
| trip_places.csv | 1597 | 4 |
| discussion_people_participations.csv | 99 | 6 |
| discussion_org_participations.csv | 23 | 6 |
| plan_people_participations.csv | 75 | 6 |
| plan_org_participations.csv | 17 | 6 |
| meeting_discussions.csv | 101 | 3 |
| meeting_plans.csv | 74 | 3 |
| discussion_topics.csv | 102 | 4 |
| discussion_plans.csv | 96 | 4 |
| plan_topics.csv | 73 | 3 |
| travel_links.csv | 22 | 3 |
| refers_to.csv | 43 | 3 |
| wide_discussions.csv | 101 | 8 |
| wide_plans.csv | 74 | 9 |
| wide_trips.csv | 536 | 9 |
| person_topic_sentiment_matrix.csv | 6 | 15 |
| topic_industry_summary.csv | 14 | 4 |

---

# VAST Challenge 2025 MC2 - 数据调查与合并摘要

## 1. 数据来源与结构

两个平行数据集，由不同主体针对同一委员会流程采集：**政府**（`Collected_by_the_Government`）和**记者**（`Collected_by_the_Journalist`）。两者共享完全一致的关系型模式，共 21 张表（8 张实体表 + 13 张关联表）。

### 维度对比

| 表名 | 政府行数 | 记者行数 | 差异 |
|------|---------|---------|------|
| meetings | 13 | 16 | +3 |
| people | 6 | 6 | 0 |
| organizations | 8 | 8 | 0 |
| topics | 15 | 15 | 0 |
| discussions | 75 | 101 | +26 |
| plans | 55 | 74 | +19 |
| places | 93 | 172 | +79 |
| trips | 194 | 342 | +148 |
| trip_places | 234 | 1363 | +1129 |

### 相同实体

People（6）、Organizations（8）、Topics（15）在两个来源中逐字节一致，无来源独有实体。

## 2. 覆盖差异

### 会议

政府覆盖会议 1-12 和 16。记者覆盖 1-16。会议 13、14、15 仅记者有。会议 13 和 15 使用日期格式标签（`07-03-40`、`07-17-40`）而非 `Meeting N`。

### 讨论与计划

讨论：75 共有，26 仅记者有。计划：55 共有，19 仅记者有。两者均无政府独有项。额外条目对应记者独有的 3 场会议及额外的出行相关活动。

### 出行

政府：194 次出行（2040 年 3-8 月）。记者：342 次（同期）。政府的 194 个出行 ID 全部是记者数据的子集。日期缺陷：部分日期使用年份前缀 `0040`（清洗时统一为 `2040`）。

| 月份 | 政府 | 记者 |
|------|------|------|
| 2040-03 | 1 | 1 |
| 2040-04 | 46 | 79 |
| 2040-05 | 44 | 85 |
| 2040-06 | 52 | 90 |
| 2040-07 | 48 | 82 |
| 2040-08 | 3 | 5 |

### 地点

政府：93 个，记者：172 个（79 个仅记者有）。记者对居住区（32 vs 3）和商业区（91 vs 55）覆盖更广。

### 各人出行频次

| 人物 | 政府 | 记者 |
|------|------|------|
| Carol Limpet | 69 | 69 |
| Simone Kat | 67 | 67 |
| Seal | 53 | 53 |
| Ed Helpsford | 0 | 61 |
| Tante Titan | 4 | 49 |
| Teddy Goldstein | 1 | 43 |

政府仅大量追踪 3 人出行，记者覆盖全部 6 人。

## 3. 情感倾向与利益相关者

### 个人情感

| 人物 | 均值 | 次数 | 标准差 |
|------|------|------|--------|
| Seal | 0.108 | 24 | 0.050 |
| Teddy Goldstein | 0.344 | 32 | 0.689 |
| Simone Kat | 0.469 | 84 | 0.659 |
| Carol Limpet | 0.655 | 42 | 0.199 |
| Ed Helpsford | 0.700 | 40 | 0.405 |
| Tante Titan | 0.819 | 54 | 0.277 |

### 来源间差异

29 对重叠的（人物，议题）组合中，平均绝对情感偏差为 **0.000**。两个来源对共有记录的情感评分完全一致。

### 组织立场

- **Saltwater Serenades**：反对经济适用房（-1.0）和 Lomark 新起重机（-1.0）
- **Tours Central Ticketing**：反对新起重机（-1.0），支持旅游码头扩建（+1.0）
- **Paackland Container Inc.**：反对旅游码头扩建（-0.5）
- **Builders Association** 和 **Industrial Shipping**：支持经济适用房（+1.0）

## 4. 议题时间线与计划类型

### 时间阶段

- **前期**（会议 1-3）：fish_vacuum、seafood_festival、deep_fishing_dock
- **中期**（会议 4-9）：renaming_park_himark、new_crane_lomark、low_volume_crane、affordable_housing、waterfront_market、heritage_walking_tour、concert、statue_john_smoth、name_inspection_office
- **后期**（会议 10-16）：marine_life_deck、name_harbor_area、expanding_tourist_wharf、concert（会议 16）

### 计划类型分布

| 类型 | 政府 | 记者 |
|------|------|------|
| travel | 16 | 22 |
| report | 10 | 12 |
| proposal | 10 | 14 |
| feedback | 6 | 9 |
| discussion | 5 | 5 |
| presentation | 4 | 6 |
| take action | 4 | 6 |

### 状态不一致

`discussion_plans.status` 中同时出现 `completed` 和 `Completed`（大小写不统一）。

## 5. 合并策略与清洗输出

### 策略

- **实体表**（people、organizations、topics）：直接使用（两源一致）
- **会议**：两源取并集
- **讨论、计划、地点**：取并集，按主键去重
- **关联表**：添加 `source` 列后取并集，按自然键去重
- **参与表**：添加 `source` 列后取并集，按非 source 列去重
- **出行表**：添加 `source` 列后取并集，日期标准化（`0040` -> `2040`）

### 输出文件清单（`data/cleaned_data/`）

| 文件 | 行数 | 列数 |
|------|------|------|
| people.csv | 6 | 3 |
| organizations.csv | 8 | 2 |
| topics.csv | 15 | 3 |
| meetings.csv | 16 | 3 |
| discussions.csv | 101 | 3 |
| plans.csv | 74 | 4 |
| places.csv | 172 | 6 |
| trips.csv | 536 | 5 |
| trip_people.csv | 536 | 4 |
| trip_places.csv | 1597 | 4 |
| discussion_people_participations.csv | 99 | 6 |
| discussion_org_participations.csv | 23 | 6 |
| plan_people_participations.csv | 75 | 6 |
| plan_org_participations.csv | 17 | 6 |
| meeting_discussions.csv | 101 | 3 |
| meeting_plans.csv | 74 | 3 |
| discussion_topics.csv | 102 | 4 |
| discussion_plans.csv | 96 | 4 |
| plan_topics.csv | 73 | 3 |
| travel_links.csv | 22 | 3 |
| refers_to.csv | 43 | 3 |
| wide_discussions.csv | 101 | 8 |
| wide_plans.csv | 74 | 9 |
| wide_trips.csv | 536 | 9 |
| person_topic_sentiment_matrix.csv | 6 | 15 |
| topic_industry_summary.csv | 14 | 4 |
