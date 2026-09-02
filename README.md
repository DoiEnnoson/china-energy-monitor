# china-energy-monitor

Strukturierte Monatsdaten zu Chinas Energieimporten und -produktion. Zwei Datenquellen, drei Tabellen, ein automatisierter Update-Zyklus.

---

## Datenquellen und Abdeckung

| Quelle | Inhalt | Zeitraum | Update |
|---|---|---|---|
| UN ComTrade API | Fossile Brennstoffimporte nach Lieferland | 2020–laufend | monatlich automatisch (15.) |
| GACC / NBS via Vault | Importmengen + -werte (GACC), Inlandsproduktion (NBS) | Mai 2026–laufend | manuell nach jedem Energiebilanz-RECH |

**ComTrade** liefert granulare Herkunftsland-Daten für Kohle, Rohöl, LNG und Pipelinegas — historisch ab 2020, laufend für 2025 automatisiert per GitHub Actions.

**GACC/NBS** liefert die offiziellen chinesischen Monatszahlen (Generalzollverwaltung für Importe, Nationales Statistikamt für Inlandsproduktion). Diese Daten kommen nicht über eine API, sondern werden aus den monatlichen Energiebilanz-Rechercheberichten (RECH-Dateien im lokalen Vault) extrahiert.

---

## Repo-Struktur

```
data/
  fuel-imports/
    comtrade_coal.csv           — Kohleimporte nach Lieferland (ComTrade, 2020–)
    comtrade_crude_oil.csv      — Rohölimporte nach Lieferland (ComTrade, 2020–)
    comtrade_lng.csv            — LNG-Importe nach Lieferland (ComTrade, 2020–)
    comtrade_pipeline_gas.csv   — Pipelinegas-Importe nach Lieferland (ComTrade, 2020–)
    gacc_imports.csv            — Gesamtimporte Kohle/Rohöl/Gas (GACC, Mai 2026–)
  production/
    nbs_production.csv          — Inlandsproduktion Kohle/Rohöl/Gas (NBS, Mai 2026–)

scripts/
  fetch_history.py      — Einmalig: lädt ComTrade-Historie 2020–2024
  fetch_comtrade.py     — Monatlich: aktualisiert ComTrade-Daten für 2025
  rech_to_github.py     — Einzeln: extrahiert machine_data aus einer RECH-Datei
  backfill_to_github.py — Einmalig/lokal: verarbeitet alle annotierten RECH-Dateien

.github/workflows/
  monthly_update.yml   — Cron: 15. jeden Monats, 06:00 UTC
  fetch_history.yml    — workflow_dispatch (manuell, einmalig)
```

---

## Dateiformat

### `data/fuel-imports/comtrade_*.csv`

Eine Datei pro Energieträger. Jede Zeile ist ein Lieferland für einen Monat.

| Spalte | Einheit | Beschreibung |
|---|---|---|
| period | YYYYMM | Berichtsmonat |
| partner | Text | Lieferland (UN ComTrade Bezeichnung) |
| value_usd_bn | Mrd. USD | Importwert |
| qty_mt | Mio. t | Importmenge |
| value_per_mt_usd | USD/t | Importwert je Tonne |

HS-Codes: Kohle = 2701, Rohöl = 2709, LNG = 271111, Pipelinegas = 271121.

### `data/fuel-imports/gacc_imports.csv`

Eine Zeile pro Monat. Gesamtimporte aller Lieferländer (GACC-Aggregat).

| Spalte | Einheit | Beschreibung |
|---|---|---|
| period | YYYYMM | Berichtsmonat |
| coal_mt | Mio. t | Kohleeinfuhren (Menge) |
| coal_mt_yoy_pct | Prozent | Veränderung Menge gegenüber Vorjahresmonat |
| coal_usd_bn | Mrd. USD | Kohleeinfuhren (Wert) |
| coal_usd_bn_yoy_pct | Prozent | Veränderung Wert gegenüber Vorjahresmonat |
| coal_usd_per_mt | USD/t | Kohlepreis je Tonne |
| crude_oil_mt | Mio. t | Rohöleinfuhren (Menge) |
| crude_oil_mt_yoy_pct | Prozent | Veränderung Menge gegenüber Vorjahresmonat |
| crude_oil_usd_bn | Mrd. USD | Rohöleinfuhren (Wert) |
| crude_oil_usd_bn_yoy_pct | Prozent | Veränderung Wert gegenüber Vorjahresmonat |
| crude_oil_usd_per_mt | USD/t | Rohölpreis je Tonne |
| gas_mt | Mio. t | Gaseinfuhren LNG + Pipeline (Menge) |
| gas_mt_yoy_pct | Prozent | Veränderung Menge gegenüber Vorjahresmonat |
| gas_usd_bn | Mrd. USD | Gaseinfuhren (Wert) |
| gas_usd_bn_yoy_pct | Prozent | Veränderung Wert gegenüber Vorjahresmonat |
| gas_usd_per_mt | USD/t | Gaspreis je Tonne |

### `data/production/nbs_production.csv`

Eine Zeile pro Monat. Chinesische Inlandsproduktion nach NBS.

| Spalte | Einheit | Beschreibung |
|---|---|---|
| period | YYYYMM | Berichtsmonat |
| coal_mt | Mio. t | Rohkohleproduktion |
| coal_mt_yoy_pct | Prozent | Veränderung gegenüber Vorjahresmonat |
| crude_oil_mt | Mio. t | Rohölproduktion |
| crude_oil_mt_yoy_pct | Prozent | Veränderung gegenüber Vorjahresmonat |
| gas_bcm | Mrd. m³ | Erdgasproduktion |
| gas_bcm_yoy_pct | Prozent | Veränderung gegenüber Vorjahresmonat |

**Hinweis Januar/Februar:** NBS und GACC veröffentlichen Januar und Februar grundsätzlich nur als kombinierten Zweimonatswert. Die Zeile mit `period=202601` enthält daher den kumulierten Jan-Feb-Wert (z. B. 760 Mio. t Kohle für zwei Monate). Die YoY-Angaben beziehen sich ebenfalls auf den kombinierten Zweimonatszeitraum. Ab März sind Einzelmonatswerte ausgewiesen. Diese Struktur ist konsistent mit der GACC-Berichtspraxis.

---

## Automatisierung: ComTrade

**GitHub Actions** läuft am 15. jeden Monats (06:00 UTC) und ruft `fetch_comtrade.py` auf. Das Script holt alle verfügbaren 2025-Monate per ComTrade API und pflegt sie per Upsert in die vier Commodity-CSVs ein. Bereits vorhandene 2025-Zeilen werden vollständig ersetzt (idempotent). Ältere Jahre (2020–2024) bleiben unberührt.

ComTrade veröffentlicht Monatsdaten typischerweise mit 2–3 Monaten Verzögerung. Das Script bricht sauber ab, wenn noch keine 2025-Daten verfügbar sind.

Erforderliche GitHub Secrets:
- `COMTRADE_PRIMARY_KEY` — UN ComTrade API Primary Key

---

## Manueller Workflow: GACC/NBS-Daten

GACC und NBS stellen keine maschinenlesbare API bereit. Die Daten werden stattdessen über einen strukturierten Annotationsprozess aus den monatlichen Energiebilanz-Rechercheberichten extrahiert.

### Schritt 1: machine_data-Block in RECH-Datei

Jede Energiebilanz-RECH-Datei im Vault enthält am Ende einen HTML-Kommentarblock mit den Strukturdaten des Monats:

```
<!--machine_data
period: "202607"
imports:
  coal:      { qty_mt: 42.73, qty_yoy_pct: 20.6,  value_usd_bn: 4.35,  value_yoy_pct: 83.6 }
  crude_oil: { qty_mt: 35.73, qty_yoy_pct: -24.1, value_usd_bn: 22.78, value_yoy_pct: -5.3 }
  gas:       { qty_mt: 10.54, qty_yoy_pct: -0.1,  value_usd_bn: 5.70,  value_yoy_pct: 20.8 }
production:
  coal_mt: 340.0
  crude_oil_mt: 18.27
  gas_bcm: 21.4
-->
```

Einheiten: `qty_mt` und `*_mt` in Mio. Tonnen, `value_usd_bn` in Mrd. USD, `gas_bcm` in Mrd. m³. `null` steht für fehlende Daten, nicht für Null.

### Schritt 2: Extraktion

Nach dem Annotieren eine RECH-Datei einzeln verarbeiten:

```bash
# Voraussetzung: Python-Venv mit requirements.txt, gh CLI authentifiziert
python scripts/rech_to_github.py \
    --file "11_Recherche/Berichte/260820_RECH_China_Energiebilanz_Juli2026.md"
```

Das Script liest den machine_data-Block, berechnet die `*_usd_per_mt`-Werte, pflegt die Zeile per Upsert in `gacc_imports.csv` und `nbs_production.csv` ein und pusht.

Alle annotierten RECH-Dateien auf einmal verarbeiten (Backfill nach einer neuen Annotation-Runde):

```bash
python scripts/backfill_to_github.py
```

`backfill_to_github.py` läuft ausschließlich lokal — es braucht Zugriff auf den Vault unter `/Users/hado/Documents/Arbeit/China-Archiv`.

### Schritt 3: value_per_mt-Berechnung

`rech_to_github.py` und `backfill_to_github.py` berechnen den Preis je Tonne automatisch:

```
value_per_mt_usd = round(value_usd_bn * 1000 / qty_mt, 1)
```

Ist einer der beiden Eingangswerte `null`, bleibt `value_per_mt_usd` ebenfalls leer.

---

## Einmaliger Historien-Import (2020–2024)

`fetch_history.py` lädt die komplette ComTrade-Historie 2020–2024 und schreibt die vier Commodity-CSVs neu. Dieses Script wurde einmalig über den `fetch_history`-Workflow ausgeführt und muss nicht wiederholt werden, es sei denn, die historischen Daten werden in ComTrade nachträglich revidiert.

```bash
export COMTRADE_PRIMARY_KEY=<key>
python scripts/fetch_history.py
```

---

## Abhängigkeiten

```
comtradeapicall   — UN ComTrade Python-Wrapper
pandas            — Datenverarbeitung
requests          — HTTP
urllib3           — HTTP-Transport
pyyaml            — YAML-Parsing der machine_data-Blöcke
```

Lokal: `pip install -r requirements.txt` in einem venv. Auf macOS mit extern verwaltetem Python empfiehlt sich ein venv unter `/tmp/` oder `~/.venv/`.

---

## Offene Erweiterungen

- **Ember API**: Stromerzeugung und -nachfrage (geplant, noch nicht implementiert). Würde eine weitere Tabelle `data/power/ember_power.csv` ergänzen und als separater monatlicher Workflow laufen.
- **2026 ComTrade**: Sobald UN ComTrade 2026-Daten verfügbar macht, `YEAR` in `fetch_comtrade.py` aktualisieren und den Workflow manuell antriggern.
