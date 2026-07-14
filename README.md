# Group 3 — Healthcare Analytics

**Research question:** How do GDP and healthcare spending affect child mortality rates across different countries?

**Course:** DIT 2B, Group 3 · Midsemester Project · July 2026

## Definition

This project is a cross-country analysis of the relationship between **economic
wealth (GDP)**, **healthcare investment**, and **child mortality**. Using World
Bank World Development Indicators for 196 countries from 2000–2023, it
measures how strongly GDP per capita and health expenditure (both as a share
of GDP and in per-capita dollar terms) correlate with the under-5 mortality
rate, and tracks how that relationship has changed over time and across
regions and income groups.

## Repository structure

| Path | Contents |
|---|---|
| `report.md` | Main findings, headline numbers, and actionable insights |
| `data_dictionary.md` | Column-by-column definitions for every dataset |
| `methodology_log.md` | Data sourcing, cleaning, and analysis methodology |
| `analysis.ipynb` | Full analysis notebook |
| `data/raw/`, `data/clean/` | Raw and cleaned datasets (Power BI–ready CSVs) |
| `figures/` | Generated charts used in the report |
| `scripts/` | Data download, cleaning, notebook-build, and choropleth scripts |
| `GlobalHealthEquity/` | Power BI project (PBIP) built on the cleaned data |

## Getting started

```
python scripts/01_download_data.py
python scripts/02_clean_data.py
```

Then open `analysis.ipynb` for the full analysis, or `report.md` for a summary
of findings. See `GlobalHealthEquity/README.md` for the Power BI dashboard.
