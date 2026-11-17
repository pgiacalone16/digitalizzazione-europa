"""
build_dataset.py
Builds a country-year panel dataset from the DESI / Digital Decade data.

Input : data/raw/desi-data.csv  (main file, DESI editions 2018-2026)
Output: data/processed/desi_panel.csv  (27 EU countries x 3 years = 81 rows)

Usage:  python build_dataset.py
"""
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/desi-data.csv")
OUT = Path("data/processed/desi_panel.csv")

# Reference years in which ALL the chosen indicators are available
# (the skills and enterprise surveys are biennial).
YEARS = [2021, 2023, 2025]

# Chosen indicators: readable_name -> (indicator code, breakdown)
# The "breakdown" selects the sub-group; here we always take the total.
INDICATORS = {
    # People
    "skills_basic":    ("desi_dsk_bab", "ind_total"),   # % with at least basic digital skills
    "skills_above":    ("desi_dsk_ab", "ind_total"),    # % with above-basic digital skills
    "ict_specialists": ("desi_ict_spec", "total"),      # % of employed who are ICT specialists
    # Infrastructure
    "fttp":            ("desi_fttp", "total_pophh"),    # % of households with fibre to the premises
    "vhcn":            ("desi_vhcn", "total_pophh"),    # % of households with very high capacity networks
    "gbit5g":          ("desi_5gcov", "total_pophh"),   # % 5G coverage
    # Business
    "sme_digital_intensity": ("desi_sme_di3_gelo", "ent_sm_xfin"),  # % SMEs with at least basic digital intensity
    "cloud":           ("desi_cloud", "ent_all_xfin"),  # % of enterprises using cloud
    "ai":              ("desi_ai", "ent_all_xfin"),     # % of enterprises using AI
    "erp":             ("desi_erp", "ent_all_xfin"),    # % of enterprises using ERP
    "unicorns":        ("desi_unicorns", "total"),      # number of unicorns (per country)
    # Public services
    "egov_citizens":   ("desi_dps_cit", "egov_le_cit"),   # digital public services score for citizens
    "egov_business":   ("desi_dps_biz", "egov_le_biz"),   # digital public services score for businesses
}


def load_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # 1) Keep only the edition rows (drops rows with period == "2030", which are targets)
    df = df[df["period"].str.startswith("desi_")].copy()
    # 2) Drop the "EU" aggregate: it is not a country and would distort analysis and clustering
    df = df[df["country"] != "EU"].copy()
    # 3) "period" is the report EDITION; the actual year of the data is in "reference_period"
    df["edition"] = df["period"].str[5:].astype(int)
    return df


def extract_indicator(df: pd.DataFrame, code: str, breakdown: str) -> pd.DataFrame:
    s = df[(df["indicator"] == code) & (df["breakdown"] == breakdown)].copy()
    # ict_specialists has two units (% of employed and thousands): keep the percentage
    if code == "desi_ict_spec":
        s = s[s["unit"] == "pc_ind_emp"]
    s = s.dropna(subset=["value"])
    s = s[s["reference_period"].isin(YEARS)]
    # The same year appears in several editions (e.g. 2021 data in the 2022 and 2023 editions):
    # keep the most recent edition, which includes any revisions.
    s = s.sort_values("edition").drop_duplicates(["country", "reference_period"], keep="last")
    return s


def main() -> None:
    df = load_clean(RAW)
    columns = []
    for name, (code, breakdown) in INDICATORS.items():
        s = extract_indicator(df, code, breakdown)
        s = s.rename(columns={"reference_period": "year"})
        columns.append(s.set_index(["country", "year"])["value"].rename(name))

    panel = pd.concat(columns, axis=1).reset_index()
    panel["year"] = panel["year"].astype(int)
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)

    # Quality checks
    print("Dataset shape:", panel.shape)
    print("Countries:", panel["country"].nunique(), "| Years:", [int(y) for y in sorted(panel["year"].unique())])
    print("Missing values per column:\n", panel.isna().sum().to_string())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUT, index=False)
    print("Saved to", OUT)


if __name__ == "__main__":
    main()