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
- Coverage: 4 counties, [January 2023 - July 2026]

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
| `seasons` | Lookup: long-rains / short-rains date windows |
| `daily_weather` | Core fact table — one row per county per day |
| `county_monthly_summary` | Pre-aggregated monthly rollups (avg temp/humidity, total precip) |
| `daily_weather_view` | Denormalized view joining county and season names into `daily_weather` |
| `monthly_summary_view` | Denormalized view joining county and season names into `county_monthly_summary` |

## Dashboard

Four-page Power BI report, [link to live dashboard once published].

**1. KPI Overview** — headline numbers (avg temp, total rainfall, county/year coverage) plus a county-by-year crop suitability matrix, color-coded against maize growing-season rainfall thresholds.

**2. Trends** — seasonal rainfall and temperature by county (long-rains vs. short-rains), plus a monthly fungal disease risk heatmap based on temperature/humidity co-occurrence.

**3. County Comparison** — rainfall variability (coefficient of variation) by county, shown both as a year-over-year trend and a ranked average — the project's core risk-comparison view.

**4. Data Quality** — completeness checks and validation against NASA POWER's missing-value sentinel.

## Key Findings

- **Rainfall variability**: 
    Nakuru shows the highest year-to-year rainfall variability of the four counties; Trans Nzoia the lowest and most predictable. A meaningful distinction for drought/flood risk that raw rainfall totals alone don't surface.
- **Fungal disease risk**: 
    Using a daily proxy (humidity + temperature co-occurrence, thresholds grounded in published plant pathology research — see [Methodology](#methodology-notes)), Bungoma shows materially higher fungal risk exposure than the other three counties. This is majorly driven by temperature, not humidity — Bungoma's lower altitude keeps it consistently within the 20–30°C range fungal pathogens require, while Nakuru's cooler Rift Valley climate rarely reaches that range regardless of humidity.
- **Data quality**: 
    Zero instances of NASA POWER's `-999` missing-value sentinel across all four counties and the full date range — confirmed and documented on the Data Quality dashboard page.

## Methodology Notes

**Fungal risk proxy**: Real fungal infection (e.g. gray leaf spot, northern corn leaf blight on maize) depends on *sustained* leaf wetness and humidity above 90%, typically for 10+ consecutive hours — this project uses a simplified daily-average threshold (humidity + temperature co-occurrence) as a directional proxy, since hourly leaf-wetness data isn't available in this dataset. Treat this as a risk *indicator*, not a validated epidemiological model.

**Crop suitability thresholds**: Maize growing-season rainfall bands (drought risk / suitable / waterlogging risk) are sourced from KALRO[https://kalrotimps.com/timps/11] FAO[https://www.fao.org/giews/countrybrief/country.jsp?code=KEN].

## Query Performance

Initial load used row-by-row upserts, requiring one round-trip to Neon per row — this was a significant performance bottleneck at scale. Switching to batched inserts (500 rows per batch) resolved it. This is a pattern worth carrying into every future sprint's ETL design rather than rediscovering per project.

## AI Tool Transparency

This project's ETL pipeline, SQL schema, and initial dashboard structure were built independently. Claude (Anthropic) was used throughout as a debugging and design-review collaborator — diagnosing DAX and Power BI issues (e.g. a broken table relationship caused by mismatched county-name text values, a `DIVIDE` function silently returning blank instead of zero), validating fungal-risk threshold assumptions against published plant pathology literature, and structuring this documentation. All final logic, data validation, and interpretation decisions were reviewed and made by the me.

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