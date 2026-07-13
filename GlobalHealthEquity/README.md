# GlobalHealthEquity — Power BI Project (PBIP / TMDL / PBIR)

Power BI project for the DIT 2B Group 3 healthcare analytics midsem: GDP, health
spending and under-5 mortality across 196 countries (World Bank, 2000–2023).
Generated from the cleaned CSVs in `../data/clean/` (see `../methodology_log.md`).

```
GlobalHealthEquity.pbip                  <- open THIS file in Power BI Desktop
GlobalHealthEquity.SemanticModel/        <- data model (TMDL format)
  definition/expressions.tmdl            <- the DataPath parameter lives here
  definition/tables/*.tmdl               <- one table per CSV + measures
GlobalHealthEquity.Report/               <- report (PBIR format), 3 pages
validate.py                              <- re-run integrity checks
_validation/schemas/                     <- offline copies of Microsoft's JSON schemas
```

## 1. Where to change DataPath (do this first on a new machine)

The model loads the four CSVs from a single folder parameter, currently:

```
C:\Users\HP\OneDrive\Desktop\pharma\data\clean
```

Change it **one** of two ways:

- **In Power BI Desktop (recommended):** open the project → *Transform data ▾ →
  Edit parameters* → set **DataPath** to your folder containing the 4 CSVs → OK →
  *Apply changes* (or *Refresh*).
- **In a text editor (before opening):** edit
  `GlobalHealthEquity.SemanticModel/definition/expressions.tmdl` — the folder
  path is the quoted string on the `expression DataPath = "..."` line. No
  trailing backslash.

## 2. How to open

1. Install a **recent Power BI Desktop** (December 2025 or later recommended;
   the report uses current PBIR schema versions — if you get a "newer version"
   error, update Desktop via Microsoft Store).
2. Double-click **`GlobalHealthEquity.pbip`** (or File → Open in Desktop).
3. The report opens with empty visuals first — click **Refresh** on the Home
   ribbon to load the CSVs through the DataPath parameter.
4. If asked about privacy levels for the folder, choose *Ignore privacy levels
   for this file* or set the folder source to *Organizational* — it's local CSVs.

## 3. Preview features / settings that may be needed

- **Older Desktop versions (before ~mid-2024):** File → Options and settings →
  Options → *Preview features* → enable **"Power BI Project (.pbip) save option"**
  and restart Desktop. On current versions PBIP is GA and no toggle exists.
- The PBIR report format (`definition/` folder with visual.json files) is GA
  since 2025; no toggle needed on a current Desktop.
- **Filled map:** if the map on page 2 shows an error, enable File → Options →
  *Security* → **"Use Map and Filled Map visuals"** (and, in organizations, the
  tenant admin setting of the same name).

## 4. What's in the report

| Page | Contents |
|---|---|
| **KPI Overview** | 4 cards (Avg Mortality, Avg Health Spend Pct, Avg GDP per Capita, Countries) · year/region/income_group slicers · mortality-by-income-group line chart · region bar chart (visual-level filter `year = 2023`) |
| **Geography & Distribution** | Filled map (country → Avg Mortality 2023 color) · column chart of countries per mortality band (calculated column `Mortality Band`: 0-10, 10-25, 25-50, 50-75, 75+, sorted by a hidden order column) |
| **Relationships** | Scatter: X = GDP per capita 2023 (**log scale**), Y = Avg Mortality 2023, size = health spend per capita, legend = region, detail = country · correlation text box |

Model notes:
- `country` columns carry `dataCategory: Country` for mapping.
- All aggregation is via explicit measures (mortality/spend formatted to 1
  decimal, GDP with thousands separator); raw columns are set to *don't summarize*.
- The scatter/map use the `country_latest` table, which **is** the 2023 snapshot
  (one row per country, `latest_year = 2023` also enforced by a visual filter).
- Visuals are deliberately default-styled: restyle in Desktop as you like (e.g.
  set the map's fill to a green→red diverging scale via Format → Fill colors →
  fx → Gradient with `Avg Mortality 2023`).

## 5. Validation

```
cd GlobalHealthEquity
python validate.py        # needs: pip install jsonschema
```

Checks: every JSON file parses; every file validates against its declared
Microsoft schema (offline copies in `_validation/schemas/`); every visual
queryRef / field / filter / sort binding exists in the TMDL model
(case-sensitive); CSV headers match the model's `sourceColumn`s at the current
DataPath; page folders match `pages.json`. Last run: **ALL CHECKS PASSED**.

*(`validate.py`, `_validation/` and this README are not part of the PBIP format;
Power BI Desktop ignores them.)*
