"""
Step 2: Clean the raw World Bank data.

Every transformation here is documented in methodology_log.md.

Inputs  (data/raw/):  wb_indicators_raw.csv, wb_economies_raw.csv
Outputs (data/clean/):
  country_year_panel.csv   - tidy panel: one row per country-year (main analysis file)
  country_latest.csv       - latest-year snapshot per country (for maps/scatter)
  region_year_summary.csv  - aggregated means by region-year
  income_year_summary.csv  - aggregated means by income-group-year
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "data", "raw")
CLEAN = os.path.join(HERE, "..", "data", "clean")
os.makedirs(CLEAN, exist_ok=True)

VALUE_COLS = [
    "gdp_per_capita_usd",
    "health_exp_pct_gdp",
    "health_exp_per_capita_usd",
    "under5_mortality_per_1000",
]

log = []  # cleaning notes, printed at the end (source for methodology_log.md)

df = pd.read_csv(os.path.join(RAW, "wb_indicators_raw.csv"))
econ = pd.read_csv(os.path.join(RAW, "wb_economies_raw.csv"))
log.append(f"Loaded raw indicators: {df.shape[0]} rows covering {df['iso3c'].nunique()} economies x {df['year'].nunique()} years (2000-2023).")

# --- 1. Drop rows with no usable country code --------------------------------
n_blank = df["iso3c"].isna().sum() + (df["iso3c"].astype(str).str.strip() == "").sum()
df = df[df["iso3c"].notna() & (df["iso3c"].astype(str).str.strip() != "")].copy()
log.append(f"Dropped {int(n_blank)} rows with a blank ISO3 code (unusable for joins).")

# --- 2. Drop aggregates (World, Sub-Saharan Africa, EU, income groups...) ----
agg_ids = set(econ.loc[econ["is_aggregate"], "iso3c"])
n_before = df["iso3c"].nunique()
df = df[~df["iso3c"].isin(agg_ids)].copy()
log.append(f"Dropped {n_before - df['iso3c'].nunique()} aggregate 'economies' "
           f"(World, regional and income-group rollups); {df['iso3c'].nunique()} real countries/territories remain.")

# --- 3. Merge metadata; standardize names ------------------------------------
countries = econ[~econ["is_aggregate"]][["iso3c", "country", "region", "income_group"]]
df = df.merge(countries, on="iso3c", how="left")
# Use the metadata name as the single canonical country name; drop the per-request name
mismatch = (df["country"].str.strip() != df["country_api"].str.strip()).sum()
df = df.drop(columns=["country_api"])
df["country"] = df["country"].str.strip()
log.append(f"Standardized country names to the World Bank metadata name keyed on ISO3 code ({int(mismatch)} rows had a differing name variant in the indicator download).")

# 'Not classified' income group (e.g. Venezuela) -> missing so it stays out of income cohorts
n_nc = int((df["income_group"] == "Not classified").sum())
df.loc[df["income_group"] == "Not classified", "income_group"] = pd.NA
log.append(f"Set income_group to missing for 'Not classified' economies ({n_nc} rows).")

# --- 4. Deduplicate -----------------------------------------------------------
n_dup = int(df.duplicated(subset=["iso3c", "year"]).sum())
df = df.drop_duplicates(subset=["iso3c", "year"], keep="first")
log.append(f"Checked uniqueness on (iso3c, year): removed {n_dup} duplicate rows.")

# --- 5. Missing values ---------------------------------------------------------
# Strategy:
#  a) Drop country-years where ALL four indicators are missing (no information).
#  b) Keep partially-missing rows; analyses use pairwise-complete observations.
#  c) Drop countries/territories with NO under-5 mortality data at all (outcome variable).
#  d) No cross-country imputation - values differ too much for that to be honest.
all_missing = df[VALUE_COLS].isna().all(axis=1)
df = df[~all_missing].copy()
log.append(f"Dropped {int(all_missing.sum())} country-year rows where all 4 indicators were missing.")

no_mort = df.groupby("iso3c")["under5_mortality_per_1000"].transform(lambda s: s.notna().sum()) == 0
dropped_countries = sorted(df.loc[no_mort, "country"].dropna().unique())
df = df[~no_mort].copy()
log.append(f"Dropped {len(dropped_countries)} territories with zero mortality observations: "
           + (", ".join(dropped_countries) if dropped_countries else "none") + ".")
log.append("Remaining missing values left as NaN (no imputation): "
           + ", ".join(f"{c}={int(df[c].isna().sum())}" for c in VALUE_COLS))

# --- 6. Sort & save the tidy panel ---------------------------------------------
df = df.sort_values(["country", "year"]).reset_index(drop=True)
df = df[["iso3c", "country", "region", "income_group", "year"] + VALUE_COLS]
df.to_csv(os.path.join(CLEAN, "country_year_panel.csv"), index=False)
log.append(f"Saved country_year_panel.csv: {df.shape[0]} rows, {df['iso3c'].nunique()} countries, years {df['year'].min()}-{df['year'].max()}.")

# --- 7. Latest-year snapshot ----------------------------------------------------
snap = (df.dropna(subset=["under5_mortality_per_1000"])
          .sort_values("year")
          .groupby("iso3c", as_index=False)
          .tail(1)
          .sort_values("country")
          .reset_index(drop=True)
          .rename(columns={"year": "latest_year"}))
snap.to_csv(os.path.join(CLEAN, "country_latest.csv"), index=False)
log.append(f"Saved country_latest.csv: {snap.shape[0]} countries; latest year with mortality data ranges {snap['latest_year'].min()}-{snap['latest_year'].max()}.")

# --- 8. Region / income-group yearly summaries ----------------------------------
grp = df.groupby(["region", "year"])
reg = grp[VALUE_COLS].mean(numeric_only=True).round(2)
reg["n_countries"] = grp["under5_mortality_per_1000"].count()
reg = reg.reset_index()
reg.to_csv(os.path.join(CLEAN, "region_year_summary.csv"), index=False)

inc = (df.dropna(subset=["income_group"])
         .groupby(["income_group", "year"], as_index=False)[VALUE_COLS]
         .mean(numeric_only=True).round(2))
inc.to_csv(os.path.join(CLEAN, "income_year_summary.csv"), index=False)
log.append("Saved region_year_summary.csv and income_year_summary.csv (unweighted country means per group-year).")

print("\n=== CLEANING LOG ===")
for i, line in enumerate(log, 1):
    print(f"{i}. {line}")

print("\n=== FINAL PANEL PREVIEW ===")
print(df.head(3).to_string(index=False))
print("\nIncome groups:", sorted(df["income_group"].dropna().unique()))
print("Regions:", sorted(df["region"].dropna().unique()))
