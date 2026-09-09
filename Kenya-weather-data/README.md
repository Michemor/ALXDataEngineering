# Kenya Grain Belt Climate Risk Dashboard

**Sprint 1 · Kenya County Weather & Climate Analytics**
Part of a Data Engineering Track built during the ALX Data Engineering program.

## Overview

This project builds an end-to-end climate analytics pipeline for four counties in Kenya's grain belt — **Uasin Gishu, Trans Nzoia, Nakuru, and Bungoma** — to answer a practical question: *which counties carry the most climate risk for grain farming, and why?*

Rather than a generic weather dashboard, this project is scoped specifically around agricultural risk signals relevant to maize and grain production: rainfall predictability, seasonal patterns, growing-season suitability, and fungal disease risk driven by temperature and humidity.

The four counties were chosen deliberately for their relevance to Kenya's wheat and maize belt.

## Data Source

- **NASA POWER API** — agroclimatology community endpoint (no API key required)
- Daily records: temperature (avg/max/min), precipitation, relative humidity, solar radiation, wind speed, soil moisture
- Coverage: 4 counties, January 2023 – July 2026

## Architecture

```
NASA POWER API → Python ETL (extract/transform/load) → PostgreSQL (Neon, cloud-hosted) → Power BI Service
```

- **Extract**: pulls daily records per county from the NASA POWER agroclimatology endpoint
- **Transform**: renames NASA parameter codes to readable columns (e.g. `T2M` → `temp_avg_c`), validates against NASA's `-999` missing-value sentinel
- **Load**: batched upserts (500 rows/batch) into Neon-hosted PostgreSQL — see [Query Performance](#query-performance) for why this matters

See `/diagrams` for the full ER diagram.

## Data Model

| Table | Purpose |
|---|---|
| `counties` | Lookup: county name, ID, coordinates |
| `seasons` | Lookup: dry_season_1, dry_season_2, long_rains, short_rains date windows |
| `daily_weather` | Core fact table — one row per county per day |
| `county_monthly_summary` | Pre-aggregated monthly rollups (avg temp/humidity, total precip) |
| `daily_weather_view` | Denormalized view joining county and season names into `daily_weather` |
| `monthly_summary_view` | Denormalized view joining county and season names into `county_monthly_summary` |

## Dashboard

Four-page Power BI report, [link to live dashboard once published].

**1. KPI Overview** — headline numbers (avg temp, total rainfall, county/year coverage), a Kenya county map, plus a county-by-year crop suitability matrix, color-coded against maize growing-season rainfall thresholds.

**2. Trends** — seasonal rainfall and temperature by county across all four defined seasons (long-rains, short-rains, and two dry seasons), plus a monthly fungal disease risk heatmap based on temperature/humidity co-occurrence.

**3. County Comparison** — rainfall variability (coefficient of variation) by county, shown both as a year-over-year trend and a ranked average — the project's core risk-comparison view.

**4. Data Quality** — completeness checks and validation against NASA POWER's missing-value sentinel.

## Key Findings

- **Rainfall variability**: Nakuru shows the highest year-to-year rainfall variability of the four counties; Trans Nzoia the lowest and most predictable. A meaningful distinction for drought/flood risk that raw rainfall totals alone don't surface.
- **Fungal disease risk**: Using a daily proxy (humidity + temperature co-occurrence, thresholds grounded in published plant pathology research — see [Methodology](#methodology-notes)), Bungoma shows materially higher fungal risk exposure than the other three counties (29% of days flagged, vs. 1–5% for Trans Nzoia and Uasin Gishu). This is driven by temperature, not humidity — Bungoma's lower altitude keeps it consistently within the 20–30°C range fungal pathogens require, while **Nakuru shows zero qualifying risk days across the entire dataset** — not a data gap, but a genuine climate signal: its higher-altitude average temperature (~15°C) keeps it below the fungal risk threshold band almost year-round, confirmed directly against daily temperature and humidity records.
- **Crop suitability**: Applying a Kenya-specific maize growing-season rainfall band of 600–1,200mm (see [Methodology](#methodology-notes)) to Long Rains totals, Bungoma, Nakuru, and Trans Nzoia land within the suitable range in every year of the dataset. **Uasin Gishu is the consistent outlier**, exceeding 1,200mm in three of the four years (2023: 1,225mm, 2024: 1,315mm, 2026: 1,321mm), indicating recurring waterlogging risk rather than drought risk for this county. This aligns with independent field reporting: FAO's GIEWS Kenya brief (May 2026) documents that Kenya's high-potential maize basket counties — including Uasin Gishu — received long-rains precipitation more than three times the long-term average in early 2026, explicitly flagging waterlogging risk in poorly drained areas.
- **Data quality**: Zero instances of NASA POWER's `-999` missing-value sentinel across all four counties and the full date range (5,232 total daily records, 100% completeness) — confirmed on the Data Quality dashboard page.

## Methodology Notes

**Fungal risk proxy**: Real fungal infection (e.g. gray leaf spot, northern corn leaf blight on maize) depends on *sustained* leaf wetness and humidity above 90%, typically for 10+ consecutive hours — this project uses a simplified daily-average threshold (humidity + temperature co-occurrence, 20–30°C) as a directional proxy, since hourly leaf-wetness data isn't available in this dataset. Treat this as a risk *indicator*, not a validated epidemiological model.

**Crop suitability thresholds**: Maize growing-season rainfall bands (600mm drought-risk floor, 1,200mm waterlogging-risk ceiling) are informed by Kenya-specific agronomic guidance stating that regions best suited to maize (900–2,500m altitude) receive 600–1,200mm of well-distributed rainfall during the growing season ([GreenLife Kenya, Expert Guide to Maize Farming in Kenya](https://www.greenlife.co.ke/expert-guide-to-maize-farming-in-kenya/)). This range is broadly consistent with the [KCEP Maize Extension and Training Manual](https://www.kcepcral.go.ke/wp-content/uploads/2017/04/KCEP-Maize-Extension-and-Training-Manual.pdf) (Kenya Cereal Enhancement Programme, citing KALRO guidance), which places the suitable range at 600–900mm — the 900–1,200mm portion of this project's upper band should be read as a more permissive estimate than KALRO's own figure, not a directly KALRO-sourced number. The qualitative waterlogging finding for Uasin Gishu is independently corroborated by [FAO GIEWS Kenya Country Brief](https://www.fao.org/giews/countrybrief/country.jsp?code=KEN) (May 2026 edition), which reports above-average long-rains precipitation and associated waterlogging risk in the same counties.

## Query Performance

Initial load used row-by-row upserts, requiring one round-trip to Neon per row — this was a significant performance bottleneck at scale. Switching to batched inserts (500 rows per batch) resolved it. This is a pattern worth carrying into every future sprint's ETL design rather than rediscovering per project.

## AI Tool Transparency

This project's ETL pipeline, SQL schema, and initial dashboard structure were built independently. Claude (Anthropic) was used throughout as a debugging and design-review collaborator — diagnosing DAX and Power BI issues (e.g. a broken table relationship caused by mismatched county-name text values, a `DIVIDE` function silently returning blank instead of zero), sourcing and validating agronomic and plant pathology thresholds against published references, and structuring this documentation. All final logic, data validation, and interpretation decisions were reviewed and made by me.

## Repository Structure

```
kenya-county-weather-analytics/
├── src/etl/          # extract.py, transform.py, load.py
├── sql/              # schema, views
├── diagrams/          # ER diagram
├── data_quality/      # validation queries/results
└── docs/              # this README and supporting docs
```

## Reproducing This Project

1. Clone the repo
2. Set up a `.env` file with your Neon PostgreSQL connection string
3. `pip install -r requirements.txt`
4. Run `src/etl/extract.py` → `transform.py` → `load.py` in sequence
5. Connect Power BI to the resulting tables/views.