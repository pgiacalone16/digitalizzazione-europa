"""
add_worldbank.py
Scarica indicatori socio-economici dalla Banca Mondiale e li unisce al panel DESI.

Input : data/processed/desi_panel.csv   (prodotto da build_dataset.py)
Output: data/raw/worldbank_raw.csv      (dati scaricati, in formato lungo)
        data/processed/panel_full.csv   (panel DESI + variabili Banca Mondiale)

Uso:  python add_worldbank.py
Serve una connessione internet (API della Banca Mondiale).
"""
from pathlib import Path

import pandas as pd

PANEL_IN = Path("data/processed/desi_panel.csv")
WB_RAW = Path("data/raw/worldbank_raw.csv")
PANEL_OUT = Path("data/processed/panel_full.csv")

# Codice DESI/Eurostat (ISO2, ma Grecia = EL) -> codice ISO3 usato dalla Banca Mondiale
ISO2_TO_ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "CY": "CYP", "CZ": "CZE", "DE": "DEU",
    "DK": "DNK", "EE": "EST", "EL": "GRC", "ES": "ESP", "FI": "FIN", "FR": "FRA",
    "HR": "HRV", "HU": "HUN", "IE": "IRL", "IT": "ITA", "LT": "LTU", "LU": "LUX",
    "LV": "LVA", "MT": "MLT", "NL": "NLD", "PL": "POL", "PT": "PRT", "RO": "ROU",
    "SE": "SWE", "SI": "SVN", "SK": "SVK",
}

# nome_leggibile -> codice indicatore Banca Mondiale
WB_INDICATORS = {
    "gdp_pc_ppp":      "NY.GDP.PCAP.PP.KD",   # PIL pro capite, PPA, prezzi costanti
    "tertiary_enrol":  "SE.TER.ENRR",         # iscrizione all'istruzione terziaria (% lordo)
    "rnd_gdp":         "GB.XPD.RSDV.GD.ZS",   # spesa in R&S (% del PIL)
    "urban_pop":       "SP.URB.TOTL.IN.ZS",   # popolazione urbana (%)
    "services_gdp":    "NV.SRV.TOTL.ZS",      # servizi (% del PIL)
    "population":      "SP.POP.TOTL",         # popolazione totale
}

# Le statistiche della Banca Mondiale escono con ritardo: per ogni anno Y del panel
# usiamo il valore dell'anno Y-1 (cosi' i predittori precedono l'esito) e, se manca,
# l'ultimo valore disponibile fino a 2 anni prima.
LAG = 1
FFILL_LIMIT = 2


def download_worldbank(years: range) -> pd.DataFrame:
    import wbgapi as wb  # installato con: pip install wbgapi

    economies = list(ISO2_TO_ISO3.values())
    frames = []
    for name, code in WB_INDICATORS.items():
        print(f"Scarico {name} ({code})...")
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
    # riempie i buchi con l'ultimo valore noto (massimo FFILL_LIMIT anni) dentro ogni paese
    wb_wide = wb_wide.groupby(level="iso3").ffill(limit=FFILL_LIMIT).reset_index()

    df = panel.copy()
    df["iso3"] = df["country"].map(ISO2_TO_ISO3)
    df["wb_year"] = df["year"] - LAG
    df = df.merge(wb_wide, left_on=["iso3", "wb_year"], right_on=["iso3", "year"],
                  how="left", suffixes=("", "_wb"))
    df = df.drop(columns=["year_wb", "wb_year"])
    # PIL e popolazione hanno scale molto diverse: usiamo il logaritmo (spesso utile nei modelli)
    import numpy as np
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
    print("\nForma del panel completo:", full.shape)
    print("Valori mancanti nelle variabili Banca Mondiale:")
    print(full[list(WB_INDICATORS)].isna().sum().to_string())

    full.to_csv(PANEL_OUT, index=False)
    print("Salvato in", PANEL_OUT)


if __name__ == "__main__":
    main()
