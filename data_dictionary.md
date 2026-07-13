# Data Dictionary

**Project:** How do GDP and healthcare spending affect child mortality rates across different countries?
**Group:** DIT 2B, Group 3 · **Source:** World Bank Open Data (World Development Indicators), accessed 13 July 2026 via the `wbgapi` Python package.

---

## 1. `data/clean/country_year_panel.csv` — main analysis file (one row per country per year)

| Column | Type | Description | World Bank code |
|---|---|---|---|
| `iso3c` | text | ISO-3166 alpha-3 country code (e.g. `GHA` = Ghana). Unique country identifier — use this for joins in Power BI. | — |
| `country` | text | Official World Bank country name, standardized (whitespace trimmed). | — |
| `region` | text | World Bank geographic region (7 values): East Asia & Pacific; Europe & Central Asia; Latin America & Caribbean; Middle East, North Africa, Afghanistan & Pakistan; North America; South Asia; Sub-Saharan Africa. | — |
| `income_group` | text | World Bank FY2026 income classification: Low income, Lower middle income, Upper middle income, High income. Blank = not classified (e.g. Venezuela). | — |
| `year` | integer | Calendar year of the observation, 2000–2023. | — |
| `gdp_per_capita_usd` | decimal | GDP per capita in **current US dollars** (not inflation-adjusted). GDP divided by midyear population. | `NY.GDP.PCAP.CD` |
| `health_exp_pct_gdp` | decimal | Current health expenditure as a **percentage of GDP** (public + private + external, excludes capital investment). | `SH.XPD.CHEX.GD.ZS` |
| `health_exp_per_capita_usd` | decimal | Current health expenditure **per person in current US dollars**. | `SH.XPD.CHEX.PC.CD` |
| `under5_mortality_per_1000` | decimal | **Under-5 mortality rate**: probability per 1,000 live births that a newborn dies before reaching age 5. Our outcome ("child mortality") variable. | `SH.DYN.MORT` |

Blank cells mean the World Bank did not report a value for that country-year; we did **not** impute them (see `methodology_log.md`).

## 2. `data/clean/country_latest.csv` — latest snapshot (one row per country)

Same columns as the panel, except `year` is replaced by:

| Column | Type | Description |
|---|---|---|
| `latest_year` | integer | Most recent year (≤ 2023) for which that country has an under-5 mortality value. Other indicator values in the row come from that same year and may be blank. |

Used for the choropleth map and the GDP-vs-mortality scatter.

## 3. `data/clean/region_year_summary.csv` — regional aggregates (one row per region per year)

| Column | Type | Description |
|---|---|---|
| `region` | text | World Bank region (7 categories). |
| `year` | integer | 2000–2023. |
| `gdp_per_capita_usd` … `under5_mortality_per_1000` | decimal | **Unweighted mean** across countries in the region with data that year (each country counts equally; not population-weighted). |
| `n_countries` | integer | Number of countries contributing a mortality value to that region-year mean. |

## 4. `data/clean/income_year_summary.csv` — income-group aggregates (one row per income group per year)

| Column | Type | Description |
|---|---|---|
| `income_group` | text | Low income / Lower middle income / Upper middle income / High income. |
| `year` | integer | 2000–2023. |
| indicator columns | decimal | Unweighted mean across classified countries in the group that year. |

---

## Derived variables created inside `analysis.ipynb` (not stored in CSVs)

| Variable | Description |
|---|---|
| `log_gdp_per_capita` | Natural log of `gdp_per_capita_usd`. GDP is heavily right-skewed; the log makes its relationship with mortality approximately linear for Pearson correlation and plotting. |
| `global_mortality_ma3` | 3-year centered moving average of the global mean under-5 mortality trend (smooths year-to-year noise). |

## Units cheat-sheet
- Mortality: deaths per **1,000 live births** (so 50 = 5% of children die before age 5).
- GDP & health spend per capita: **current US$** — comparable across countries in a given year, but inflated over time.
- Health spend % GDP: share of the whole economy spent on health (0–100 scale).
