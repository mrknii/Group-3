# How do GDP and healthcare spending affect child mortality rates across different countries?

**Healthcare Analytics — Midsemester Project · DIT 2B, Group 3 · July 2026**

**Data:** World Bank World Development Indicators, 2000–2023, 196 countries (aggregates removed). Methods and cleaning steps: `methodology_log.md`. Column definitions: `data_dictionary.md`. Full analysis: `analysis.ipynb`. Figures: `figures/`. Power BI–ready CSVs: `data/clean/`.

---

## 1. Headline numbers (2023)

| KPI | Value |
|---|---|
| Global average under-5 mortality (mean of 196 countries) | **25.0 deaths per 1,000 live births** (↓ 55% since 2000) |
| Average health expenditure | **6.8% of GDP** |
| Countries analysed | **196** |

## 2. Findings

### GDP is the strongest single predictor of child survival
Across the 2023 cross-section, log GDP per capita and under-5 mortality correlate at **Pearson r = −0.77** and **Spearman ρ = −0.87** (both p < 10⁻³⁸). On a log-GDP scale the scatter (`figures/gdp_vs_mortality_scatter.png`) falls along a clean downward curve: every step up the income ladder buys child survival. The extremes tell the story — Nigeria (GDP/capita ≈ $1,600) loses 117 children per 1,000; Norway (≈ $90,000) loses 2.

### It is the *amount* of health spending that matters, not the *share* of GDP
Health expenditure **per capita** correlates with mortality almost as strongly as GDP (r = −0.76), but health expenditure **as % of GDP** is only weakly related (r = −0.22). A low-income country devoting a large share of a small economy still spends almost nothing per child: in 2022 the average low-income country spent **$43 per person** on health, versus **$3,424** in high-income countries — a **79× gap**. GDP and health spending per capita are themselves nearly collinear (r ≈ 0.97 log-log), so "wealth" and "health investment capacity" are largely the same constraint.

### Everyone improved — but the gap did not close
Global mean under-5 mortality fell **55%** between 2000 and 2023 (55.2 → 25.0), a steady ≈1.3 deaths/1,000 fewer each year (`figures/global_mortality_trend.png`). Low-income countries actually improved fastest in relative terms (151 → 66, −57%). Yet because rich countries also kept improving, a child born in a low-income country in 2023 is still **~10× more likely to die before age 5** than one born in a high-income country (13× in 2000) — see `figures/mortality_trend_by_income.png`.

### The remaining burden is geographically concentrated
All **13 countries above 75 deaths per 1,000 are in Sub-Saharan Africa** (regional mean 58.4 vs global 25.0). The distribution is heavily right-skewed: 120 of 196 countries are already below 25, while a long tail — almost entirely one region — remains above 75 (`figures/mortality_distribution.png`, `figures/mortality_choropleth.png`).

### Data caution
The mortality series includes **crisis-year estimates** (e.g. Central African Republic 2009/2022, Somalia's 2011 famine, South Sudan's civil war) which cause visible spikes in the low-income trend line; we verified these against the live API and kept them unchanged. Correlation here is **not causation** — education, sanitation, vaccination coverage and conflict all travel together with GDP.

## 3. Actionable Insight — the "So What?"

**Child mortality is no longer a global problem — it is a concentrated, purchasable one.**

1. **Target dollars, not percentages.** Since absolute per-capita spending — not the % of GDP — tracks survival, policy advice like "spend 15% of your budget on health" (Abuja target) is insufficient for low-income countries. External financing and pooled procurement that raise *dollars per child* (vaccines, skilled birth attendance, oral rehydration) are the levers with the strongest observed association with survival.
2. **Prioritise the 13-country tail.** Every country still above 75/1,000 is in Sub-Saharan Africa, and several are fragile/conflict states. A donor or NGO allocating a marginal dollar gets the most expected lives saved in this short, named list (Nigeria, Niger, Somalia, Chad, DR Congo, …) — Nigeria alone, with its large birth cohort and 117/1,000 rate, is the single highest-impact target.
3. **The middle of the curve is proof it works.** Dozens of lower-middle-income countries (Ghana at 42, India at ~30) have already cut mortality 50–70% since 2000 without becoming rich first — showing that the GDP–mortality link is *bendable* with well-directed health spending. Their program mix is a template for the tail.
4. **For our national context:** the data argue for protecting *per-capita* health spending in real dollar terms during budget cuts, since it — not the budget share — is what correlates with children surviving to age 5.

## 4. Ethics note

This analysis uses **aggregate, country-level, de-identified data** published openly by the World Bank. No individual-level or personally identifiable health records were accessed, and no individual can be re-identified from national mortality rates or expenditure totals, so the analysis poses no privacy risk to data subjects. Remaining ethical considerations are interpretive: (a) national averages hide within-country inequality (rural/urban, income deciles); (b) crisis-year estimates for conflict-affected states carry wide uncertainty and should not be quoted as precise; and (c) correlational findings must not be presented as causal claims when informing policy. Data are used under the World Bank's open data terms (CC BY 4.0) with the source credited.

---
*Reproducibility: `python scripts/01_download_data.py` → `python scripts/02_clean_data.py` → run `analysis.ipynb` (the choropleth is rendered by `scripts/04_make_choropleth.py`).*
