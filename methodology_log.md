# Methodology Log

**Project:** How do GDP and healthcare spending affect child mortality rates across different countries?
**Group:** DIT 2B, Group 3 · **Date of data access:** 13 July 2026

This log records every data acquisition and cleaning step so the analysis is fully reproducible. Run order: `scripts/01_download_data.py` → `scripts/02_clean_data.py` → `analysis.ipynb`.

---

## 1. Data acquisition (`scripts/01_download_data.py`)

- **Source:** World Bank Open Data — World Development Indicators, via the public REST API v2 (`https://api.worldbank.org/v2`). We first tried the `wbgapi` Python package, but its many small API calls were repeatedly reset on our connection, so we switched to direct bulk API requests (one request per indicator, JSON format, with automatic retry/back-off — this is the "direct API" option permitted by the brief).
- **Indicators downloaded (2000–2023, all economies):**
  | World Bank code | Our column name |
  |---|---|
  | `NY.GDP.PCAP.CD` | `gdp_per_capita_usd` |
  | `SH.XPD.CHEX.GD.ZS` | `health_exp_pct_gdp` |
  | `SH.XPD.CHEX.PC.CD` | `health_exp_per_capita_usd` |
  | `SH.DYN.MORT` | `under5_mortality_per_1000` |
- **Metadata:** the `/country` endpoint supplied each economy's region, income group, and whether it is an *aggregate* (the API marks aggregates with region = "Aggregates").
- **Download verification (before any analysis):** 6,360 rows per indicator (260 economies × 24 years + territories with codes); non-null counts — GDP 6,170; health % GDP 5,668; health per capita 5,665; under-5 mortality 5,832. Spot-checked Ghana 2020 against the World Bank website: GDP per capita ≈ $2,195, health expenditure ≈ 4.43 % of GDP, under-5 mortality 42.2 — all matched.
- Raw files saved untouched to `data/raw/` so cleaning is always re-runnable from the originals.

## 2. Cleaning (`scripts/02_clean_data.py`) — steps in execution order

| # | Step | What we did & why | Rows/countries affected |
|---|---|---|---|
| 1 | Load raw data | 6,360 indicator rows (260 economies × 24 years). | — |
| 2 | Drop blank country codes | Removed rows whose ISO3 code was empty (cannot be joined to metadata or mapped). | 120 rows |
| 3 | **Drop aggregates** | Removed rollup "economies" such as *World*, *Sub-Saharan Africa*, *European Union*, *High income* — keeping them would double-count countries in every average. Identified via the API's aggregate flag. | 43 aggregates removed; 217 real countries/territories kept |
| 4 | **Standardize country names/codes** | ISO3 code is the canonical key; the country **name** is taken from the World Bank metadata table (one spelling per code, whitespace trimmed). 0 name conflicts found. | 0 |
| 5 | Income group hygiene | Any economy classified as "Not classified" would be set to missing so it can't form a fake cohort. In this download: none. | 0 rows |
| 6 | **Deduplicate** | Enforced uniqueness on the key `(iso3c, year)`. | 0 duplicates found |
| 7 | **Missing values (a)** | Dropped country-years where **all four** indicators were missing — they carry no information. | 72 rows |
| 8 | **Missing values (b)** | Dropped 20 small territories with **zero** under-5 mortality observations (our outcome variable), e.g. Aruba, Bermuda, Guam, Hong Kong SAR, Greenland. | 20 territories |
| 9 | **Missing values (c) — no imputation** | Remaining gaps left as blank: GDP 94, health % GDP 175, health per capita 178, mortality **0**. We deliberately did **not** impute across countries (a guessed GDP for North Korea would be misleading); statistics in the notebook use pairwise-complete observations instead. | — |
| 10 | Sort & save | Sorted by country, year → `data/clean/country_year_panel.csv`. | Final: **4,704 rows, 196 countries, 2000–2023** |

## 3. Derived output files (also produced by `02_clean_data.py`)

- `country_latest.csv` — each country's most recent year with a mortality value (all 196 countries reach 2023). Used for the map and scatter chart.
- `region_year_summary.csv` / `income_year_summary.csv` — **unweighted** mean of each indicator per region-year / income-group-year (each country counts equally; we note in the report that this differs from population-weighted global figures).

## 4. Analysis decisions (`analysis.ipynb`)

- **Log transform:** GDP per capita is heavily right-skewed (a few very rich countries), so Pearson correlation and the scatter plot use `log(GDP per capita)`. Spearman is computed on raw values (rank-based, so unaffected).
- **Correlations** use pairwise-complete country-year observations, and are also shown for the latest-year cross-section to avoid the same country appearing 24 times.
- **Trend smoothing:** global mortality trend uses a 3-year centered moving average.
- **Cohorts:** income groups use the World Bank's current (FY2026) classification, held fixed across all years — cohort membership does not change over time, which keeps the comparison interpretable but means "High income in 2000" reflects today's classification.

## 5. Data quality observations (verified against the live API, not pipeline errors)

- The `SH.DYN.MORT` series contains **crisis-year spikes** for a few conflict/famine-affected countries — e.g. Central African Republic 2009 (489.3), 2019 (254.7) and 2022 (424.6); Somalia 2011 famine (363.1); South Sudan 2014–2017 civil war (183–292). We re-queried the API directly and confirmed these are the published source values, so we kept them unchanged. They explain the jagged shape of the low-income cohort line in the trend chart.
- South Sudan's mortality is a carried-forward constant (96.7) for 2019–2023 — the source has not updated it.
- 29 of the 196 countries (all microstates/small islands, plus Kosovo) have no polygon in the world map geometry and appear gray on the choropleth; they are still in every statistic.

## 6. Known limitations

1. Current-US$ series are not inflation-adjusted; cross-year dollar comparisons overstate growth.
2. Unweighted country means treat Tuvalu and India equally; global KPI figures are country averages, not population averages.
3. Health expenditure data effectively start in 2000 and lag ~2 years (sparser in 2022–2023).
4. Correlation ≠ causation: education, sanitation, vaccination coverage and conflict all confound the GDP–mortality relationship.
