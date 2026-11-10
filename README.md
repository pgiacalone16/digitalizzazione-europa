# Digitalizzazione in Europa: cosa spiega le differenze tra i paesi UE?
 
> **Stato del progetto**: in corso. Dati preparati ✅ · Analisi esplorativa ⬜ ·
> Modelli ⬜ · Clustering ⬜
 
## Domanda di ricerca
Quali fattori strutturali (istruzione, reddito, infrastrutture, competenze,
spesa in ricerca) sono associati al livello di digitalizzazione delle imprese
nei paesi dell'Unione Europea, e quali gruppi di paesi emergono?
 
## Obiettivo
Questo progetto mira ad analizzare con tecniche di machine learning le differenze di maturità digitale
tra i 27 paesi UE tra il 2021 e il 2025, individuare i fattori più associati
alla digitalizzazione delle imprese e raggruppare i paesi in profili simili.
 
## Dati
- **Digital Decade DESI** (Commissione Europea): indicatori su competenze,
  infrastrutture, imprese e servizi pubblici digitali.
  Fonte: https://digital-decade-desi.digital-strategy.ec.europa.eu/
- **World Bank Open Data**: PIL pro capite, istruzione terziaria, spesa in R&S,
  urbanizzazione.
  Fonte: https://data.worldbank.org/
Panel di 27 paesi per 3 anni (2021, 2023, 2025): 81 osservazioni.
 
## Metodo
 
L'analisi si articola in quattro fasi.
 
### 1. Preparazione dei dati
- Unione dei due dataset su chiave `paese` + `anno`.
- Per le variabili World Bank si usa il valore dell'anno precedente (ritardo
  di 1 anno), così i predittori precedono l'esito; se manca, si usa l'ultimo
  valore noto fino a 2 anni prima (documentando quali celle sono state
  riempite). Nessuna imputazione sulla variabile target.
- Standardizzazione (z-score) delle variabili esplicative, calcolata
  **solo sul training set** di ogni fold per evitare data leakage.
  Gli z-score delle componenti del target sono invece calcolati sull'intero
  panel: è una scelta dichiarata, che non usa i valori del target come
  predittore.
- Analisi esplorativa: distribuzioni, matrice di correlazione, controllo
  della multicollinearità (VIF).
### 2. Variabile target e variabili esplicative
- **Target**: indice composito di digitalizzazione delle imprese, media di
  quattro indicatori DESI standardizzati (z-score): PMI con livello base di
  intensità digitale, imprese che usano cloud, IA ed ERP. Big data ed
  e-commerce sono esclusi perché non disponibili per tutti gli anni e paesi.
- **Esplicative**: competenze digitali della popolazione, copertura
  infrastrutturale (banda larga ad alta capacità, 5G), PIL pro capite,
  istruzione terziaria, spesa in R&S in % del PIL, urbanizzazione.
- Per evitare circolarità, gli indicatori DESI sulle imprese usati nel target
  non vengono inclusi tra le esplicative.
### 3. Modelli supervisionati (fattori associati alla digitalizzazione)
- **Baseline**: regressione lineare regolarizzata (Ridge, Lasso, Elastic Net),
  interpretabile e adatta a campioni piccoli.
- **Modelli non lineari**: Random Forest e Gradient Boosting, per cogliere
  interazioni e non linearità.
- **Validazione**: cross-validation raggruppata per paese
  (`GroupKFold` / leave-one-country-out), perché le tre osservazioni dello
  stesso paese non sono indipendenti. Metriche: R², RMSE, MAE, confrontate
  con un modello banale (media del target).
- **Interpretazione**: coefficienti (modelli lineari), permutation importance
  e valori SHAP (modelli ad albero), con stabilità dell'importanza valutata
  tra i fold.
### 4. Clustering (profili di paesi)
- Riduzione di dimensionalità con PCA sulle variabili standardizzate.
- Confronto tra **K-means** e **clustering gerarchico** (linkage di Ward).
- Scelta del numero di cluster con silhouette, metodo del gomito e
  interpretabilità dei profili.
- Caratterizzazione dei cluster tramite medie delle variabili e loro
  evoluzione nel tempo (2021 → 2025).
## Risultati
 
> Sezione da completare dopo l'esecuzione delle analisi. Struttura prevista:
 
### Qualità dei modelli
| Modello | R² (CV per paese) | RMSE | MAE |
|---|---|---|---|
| Baseline (media) | – | – | – |
| Ridge / Lasso / Elastic Net | – | – | – |
| Random Forest | – | – | – |
| Gradient Boosting | – | – | – |
 
### Fattori più associati alla digitalizzazione
- Classifica delle variabili per importanza (permutation importance / SHAP):
  *da inserire*.
- Direzione e forma delle associazioni (grafici di dipendenza parziale):
  *da inserire*.
### Profili di paesi
- Numero di cluster scelto e relativa silhouette: *da inserire*.
- Descrizione sintetica di ciascun cluster e paesi che ne fanno parte:
  *da inserire*.
- Paesi che cambiano cluster tra 2021 e 2025: *da inserire*.
## Limiti
 
- **Campione ridotto**: 81 osservazioni (27 paesi × 3 anni) limitano la
  capacità dei modelli complessi e rendono instabili le stime di importanza;
  i risultati vanno letti come indicativi.
- **Dipendenza temporale**: le osservazioni dello stesso paese sono
  correlate; la cross-validation per paese attenua il problema ma non lo
  elimina.
- **Associazione, non causalità**: i modelli individuano correlazioni, non
  effetti causali. Possibili variabili omesse e causalità inversa (es. più
  digitalizzazione → più reddito).
- **Multicollinearità**: PIL pro capite, istruzione, R&S e competenze sono
  fortemente correlati, quindi l'importanza di singole variabili può essere
  distribuita in modo arbitrario tra loro.
- **Costruzione dell'indice**: il target composito dipende dalle scelte su
  indicatori e pesi; inoltre la metodologia DESI è cambiata nel passaggio al
  Digital Decade, con possibili discontinuità tra anni.
- **Disallineamento dei dati**: alcuni indicatori World Bank sono pubblicati
  con ritardo o con anni mancanti; i valori riportati dall'anno precedente
  possono introdurre errore.
- **Livello aggregato**: i dati sono a livello nazionale; le differenze
  regionali o settoriali all'interno dei paesi non sono catturate
  (rischio di fallacia ecologica).
- **Clustering**: i cluster dipendono da algoritmo, scala delle variabili e
  numero scelto di gruppi; vanno considerati una sintesi descrittiva, non una
  classificazione "vera".
## Come eseguire il progetto
 
### Struttura attuale
```
.
├── data/
│   ├── raw/                # CSV scaricati da DESI (non modificati)
│   └── processed/          # dataset prodotti dagli script
├── build_dataset.py        # costruisce il panel DESI (paese x anno)
├── add_worldbank.py        # scarica i dati World Bank e li unisce al panel
├── requirements.txt
└── README.md
```
Cartelle previste nelle prossime fasi: `notebooks/` (analisi esplorativa e
modelli) e `outputs/` (tabelle e grafici).
 
### Requisiti
- Python 3.10+
- Librerie principali: `pandas`, `numpy`, `scikit-learn`, `wbgapi`, `shap`,
  `statsmodels`, `matplotlib`, `seaborn`
### Passi
```bash
# 1. Creare e attivare l'ambiente, poi installare le librerie
python -m venv .venv
source .venv/bin/activate        # su Windows: .venv\Scripts\activate
pip install -r requirements.txt
 
# 2. Scaricare a mano i CSV DESI da
#    https://digital-decade-desi.digital-strategy.ec.europa.eu/
#    e salvarli in data/raw/ (desi-data.csv, desi-2022-data.csv,
#    dd-trajectories-data.csv)
 
# 3. Costruire il dataset (i dati World Bank vengono scaricati dallo script;
#    serve una connessione internet)
python build_dataset.py
python add_worldbank.py
```
 
Il dataset finale si trova in `data/processed/panel_full.csv`.
 