"""
add_worldbank.py
Downloads socio-economic indicators from the World Bank and merges them into the DESI panel.

Input : data/processed/desi_panel.csv   (produced by build_dataset.py)
Output: data/raw/worldbank_raw.csv      (downloaded data, long format)
        data/processed/panel_full.csv   (DESI panel + World Bank variables)

Usage:  python add_worldbank.py
Requires an internet connection (World Bank API).
"""
from pathlib import Path

import numpy as np
import pandas as pd

PANEL_IN = Path("data/processed/desi_panel.csv")
WB_RAW = Path("data/raw/worldbank_raw.csv")
PANEL_OUT = Path("data/processed/panel_full.csv")

# DESI/Eurostat country code (ISO2, but Greece = EL) -> ISO3 code used by the World Bank
ISO2_TO_ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "CY": "CYP", "CZ": "CZE", "DE": "DEU",
    "DK": "DNK", "EE": "EST", "EL": "GRC", "ES": "ESP", "FI": "FIN", "FR": "FRA",
    "HR": "HRV", "HU": "HUN", "IE": "IRL", "IT": "ITA", "LT": "LTU", "LU": "LUX",
    "LV": "LVA", "MT": "MLT", "NL": "NLD", "PL": "POL", "PT": "PRT", "RO": "ROU",
    "SE": "SWE", "SI": "SVN", "SK": "SVK",
}

# readable name -> World Bank indicator code
WB_INDICATORS = {
    "gdp_pc_ppp":      "NY.GDP.PCAP.PP.KD",   # GDP per capita, PPP, constant prices
    "tertiary_enrol":  "SE.TER.ENRR",         # tertiary education enrolment (% gross)
    "rnd_gdp":         "GB.XPD.RSDV.GD.ZS",   # R&D expenditure (% of GDP)
    "urban_pop":       "SP.URB.TOTL.IN.ZS",   # urban population (%)
    "services_gdp":    "NV.SRV.TOTL.ZS",      # services, value added (% of GDP)
    "population":      "SP.POP.TOTL",         # total population
}

# World Bank statistics are published with a delay: for each panel year Y we use
# the value of year Y-1 (so predictors precede the outcome) and, if it is missing,
# the last available value up to 2 years earlier.
LAG = 1
FFILL_LIMIT = 2


def download_worldbank(years: range) -> pd.DataFrame:
    import wbgapi as wb  # installed with: pip install wbgapi

    economies = list(ISO2_TO_ISO3.values())
    frames = []
    for name, code in WB_INDICATORS.items():
        print(f"Downloading {name} ({code})...")
        wide = wb.data.DataFrame(code, economy=economies, time=years, numericTimeKeys=True)
        wide.index.name = "iso3"
        long = wide.reset_index().melt(id_vars="iso3", var_name="year", value_name="value")
        long["indicator"] = name
        frames.append(long)
    out = pd.concat(frames, ignore_index=True)
    out["year"] = out["year"].astype(int)
    return out


def merge_panel(panel: pd.DataFrame, wb_long: pd.DataFrame) -> pd.DataFrame:
    wb_wide = wb_long.pivot_table(index=["iso3", "year"], columns="indicator", values="value")
    wb_wide = wb_wide.sort_index()
    # fill gaps with the last known value (at most FFILL_LIMIT years) within each country
    wb_wide = wb_wide.groupby(level="iso3").ffill(limit=FFILL_LIMIT).reset_index()

    df = panel.copy()
    df["iso3"] = df["country"].map(ISO2_TO_ISO3)
    df["wb_year"] = df["year"] - LAG
    df = df.merge(wb_wide, left_on=["iso3", "wb_year"], right_on=["iso3", "year"],
                  how="left", suffixes=("", "_wb"))
    df = df.drop(columns=["year_wb", "wb_year"])
    # GDP and population are on very different scales: use logs (often useful in models)
    df["log_gdp_pc_ppp"] = np.log(df["gdp_pc_ppp"])
    df["log_population"] = np.log(df["population"])
    return df


def main() -> None:
    panel = pd.read_csv(PANEL_IN)
    years = range(int(panel["year"].min()) - LAG - FFILL_LIMIT, int(panel["year"].max()) + 1)

    wb_long = download_worldbank(years)
    WB_RAW.parent.mkdir(parents=True, exist_ok=True)
    wb_long.to_csv(WB_RAW, index=False)

    full = merge_panel(panel, wb_long)
    print("\nFull panel shape:", full.shape)
    print("Missing values in World Bank variables:")
    print(full[list(WB_INDICATORS)].isna().sum().to_string())

    full.to_csv(PANEL_OUT, index=False)
    print("Saved to", PANEL_OUT)


if __name__ == "__main__":
    main()