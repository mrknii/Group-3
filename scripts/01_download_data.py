"""
Step 1: Download World Bank indicators (2000-2023) for all countries.

Uses the World Bank REST API v2 directly (https://api.worldbank.org/v2) with
retries - one bulk request per indicator instead of the many small calls the
wbgapi package makes (which were being reset by the network here).

Indicators:
  NY.GDP.PCAP.CD      - GDP per capita (current US$)
  SH.XPD.CHEX.GD.ZS   - Current health expenditure (% of GDP)
  SH.XPD.CHEX.PC.CD   - Current health expenditure per capita (current US$)
  SH.DYN.MORT         - Under-5 mortality rate (per 1,000 live births)

Outputs (data/raw/):
  wb_indicators_raw.csv - long->wide country-year table, incl. aggregate rows
  wb_economies_raw.csv  - economy metadata (region, income group, aggregate flag)
"""
import os
import time
import requests
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "..", "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

BASE = "https://api.worldbank.org/v2"
INDICATORS = {
    "NY.GDP.PCAP.CD": "gdp_per_capita_usd",
    "SH.XPD.CHEX.GD.ZS": "health_exp_pct_gdp",
    "SH.XPD.CHEX.PC.CD": "health_exp_per_capita_usd",
    "SH.DYN.MORT": "under5_mortality_per_1000",
}

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (student project; healthcare analytics)"


def get_json(url, params, tries=6):
    for attempt in range(1, tries + 1):
        try:
            r = session.get(url, params=params, timeout=90)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == tries:
                raise
            wait = 3 * attempt
            print(f"  attempt {attempt} failed ({type(e).__name__}); retrying in {wait}s...")
            time.sleep(wait)


def fetch_all_pages(url, params):
    """World Bank API is paginated: [meta, rows]."""
    rows, page = [], 1
    while True:
        js = get_json(url, {**params, "page": page})
        meta, data = js[0], js[1] or []
        rows.extend(data)
        if page >= int(meta.get("pages", 1)):
            return rows
        page += 1


# --- indicator data ----------------------------------------------------------
frames = []
for code, name in INDICATORS.items():
    print(f"Downloading {code} ({name})...")
    rows = fetch_all_pages(
        f"{BASE}/country/all/indicator/{code}",
        {"format": "json", "date": "2000:2023", "per_page": 20000},
    )
    df = pd.DataFrame(
        {
            "iso3c": [r["countryiso3code"] for r in rows],
            "country_api": [r["country"]["value"] for r in rows],
            "year": [int(r["date"]) for r in rows],
            name: [r["value"] for r in rows],
        }
    )
    print(f"  {len(df)} rows, {df[name].notna().sum()} non-null values")
    frames.append(df.set_index(["iso3c", "country_api", "year"]))

wide = pd.concat(frames, axis=1).reset_index()
out_ind = os.path.join(RAW_DIR, "wb_indicators_raw.csv")
wide.to_csv(out_ind, index=False)
print(f"\nSaved {out_ind}: {wide.shape[0]} rows x {wide.shape[1]} cols")

# --- economy metadata --------------------------------------------------------
print("Downloading economy metadata (region, income group)...")
rows = fetch_all_pages(f"{BASE}/country", {"format": "json", "per_page": 400})
econ = pd.DataFrame(
    {
        "iso3c": [r["id"] for r in rows],
        "country": [r["name"] for r in rows],
        "region": [r["region"]["value"].strip() for r in rows],
        "income_group": [r["incomeLevel"]["value"] for r in rows],
        "capital_city": [r["capitalCity"] for r in rows],
    }
)
# The API marks aggregates (World, Sub-Saharan Africa, EU, ...) with region == "Aggregates"
econ["is_aggregate"] = econ["region"].eq("Aggregates")
out_econ = os.path.join(RAW_DIR, "wb_economies_raw.csv")
econ.to_csv(out_econ, index=False)
print(f"Saved {out_econ}: {econ.shape[0]} economies ({econ['is_aggregate'].sum()} aggregates)")

# --- verification ------------------------------------------------------------
print("\n--- VERIFICATION ---")
print("Distinct economies in indicator data:", wide["iso3c"].nunique())
print("Year range:", wide["year"].min(), "-", wide["year"].max())
print("Non-null counts:")
print(wide[list(INDICATORS.values())].notna().sum().to_string())
gha = wide[(wide.iso3c == "GHA") & (wide.year == 2020)]
print("\nSample (Ghana 2020):")
print(gha.to_string(index=False))
