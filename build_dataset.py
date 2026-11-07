"""
build_dataset.py
Costruisce un dataset "panel" (paese x anno) dai dati DESI / Digital Decade.

Input : data/raw/desi-data.csv  (file principale, edizioni DESI 2018-2026)
Output: data/processed/desi_panel.csv  (27 paesi UE x 3 anni = 81 righe)

Uso:  python build_dataset.py
"""
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/desi-data.csv")
OUT = Path("data/processed/desi_panel.csv")

# Anni di riferimento in cui TUTTI gli indicatori scelti sono disponibili
# (le indagini sulle competenze e sulle imprese sono biennali).
YEARS = [2021, 2023, 2025]

# Indicatori scelti: nome_leggibile -> (codice indicatore, breakdown)
# Il "breakdown" seleziona il sottogruppo; qui prendiamo sempre il totale.
INDICATORS = {
    # Persone
    "skills_basic":    ("desi_dsk_bab", "ind_total"),   # % con competenze digitali almeno di base
    "skills_above":    ("desi_dsk_ab", "ind_total"),    # % con competenze sopra la base
    "ict_specialists": ("desi_ict_spec", "total"),      # % occupati specialisti ICT
    # Infrastrutture
    "fttp":            ("desi_fttp", "total_pophh"),    # % famiglie con fibra
    "vhcn":            ("desi_vhcn", "total_pophh"),    # % famiglie con reti a banda molto alta
    "gbit5g":          ("desi_5gcov", "total_pophh"),   # % copertura 5G
    # Imprese
    "sme_digital_intensity": ("desi_sme_di3_gelo", "ent_sm_xfin"),  # % PMI con intensita' digitale di base
    "cloud":           ("desi_cloud", "ent_all_xfin"),  # % imprese che usano il cloud
    "ai":              ("desi_ai", "ent_all_xfin"),     # % imprese che usano l'AI
    "erp":             ("desi_erp", "ent_all_xfin"),    # % imprese che usano ERP
    "unicorns":        ("desi_unicorns", "total"),      # numero di unicorni (per paese)
    # Servizi pubblici
    "egov_citizens":   ("desi_dps_cit", "egov_le_cit"),   # punteggio servizi pubblici digitali per i cittadini
    "egov_business":   ("desi_dps_biz", "egov_le_biz"),   # punteggio servizi pubblici digitali per le imprese
}


def load_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # 1) Tieni solo le righe delle edizioni (esclude le righe con period == "2030", che sono target)
    df = df[df["period"].str.startswith("desi_")].copy()
    # 2) Elimina l'aggregato "EU": non e' un paese e falserebbe analisi e clustering
    df = df[df["country"] != "EU"].copy()
    # 3) "period" e' l'EDIZIONE del rapporto; l'anno reale dei dati e' "reference_period"
    df["edition"] = df["period"].str[5:].astype(int)
    return df


def extract_indicator(df: pd.DataFrame, code: str, breakdown: str) -> pd.DataFrame:
    s = df[(df["indicator"] == code) & (df["breakdown"] == breakdown)].copy()
    # ict_specialists ha due unita' (% occupati e migliaia): teniamo la percentuale
    if code == "desi_ict_spec":
        s = s[s["unit"] == "pc_ind_emp"]
    s = s.dropna(subset=["value"])
    s = s[s["reference_period"].isin(YEARS)]
    # Lo stesso anno compare in piu' edizioni (es. dati 2021 nelle edizioni 2022 e 2023):
    # teniamo l'edizione piu' recente, che include eventuali revisioni.
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

    # Controlli di qualita'
    print("Forma del dataset:", panel.shape)
    print("Paesi:", panel["country"].nunique(), "| Anni:", sorted(panel["year"].unique()))
    print("Valori mancanti per colonna:\n", panel.isna().sum().to_string())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUT, index=False)
    print("Salvato in", OUT)


if __name__ == "__main__":
    main()
