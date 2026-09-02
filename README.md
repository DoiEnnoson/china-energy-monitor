# china-energy-monitor

Strukturierte Monatsdaten zu Chinas Energieimporten, -produktion und Stromerzeugung. Drei Datenquellen, neun Tabellen, drei automatisierte Update-Zyklen.

---

## Datenquellen und Abdeckung

| Quelle | Inhalt | Zeitraum | Update |
|---|---|---|---|
| UN ComTrade API | Fossile Brennstoffimporte nach Lieferland | 2020–laufend | monatlich automatisch (15.) |
| GACC / NBS via Vault | Importmengen + -werte (GACC), Inlandsproduktion (NBS) | Mai 2026–laufend | manuell nach jedem Energiebilanz-RECH |
| Ember API | Stromerzeugung nach Quelle, Nachfrage, CO₂-Intensität, installierte Wind-/Solarleistung | 2015–laufend | monatlich automatisch (17.–31.) |

**ComTrade** liefert granulare Herkunftsland-Daten für Kohle, Rohöl, LNG und Pipelinegas — historisch ab 2020, laufend für 2025 automatisiert per GitHub Actions.

**GACC/NBS** liefert die offiziellen chinesischen Monatszahlen (Generalzollverwaltung für Importe, Nationales Statistikamt für Inlandsproduktion). Diese Daten kommen nicht über eine API, sondern werden aus den monatlichen Energiebilanz-Rechercheberichten (RECH-Dateien im lokalen Vault) extrahiert.

**Ember** liefert monatliche Stromdaten für China ab 2015: Erzeugung nach Energieträger (TWh und Anteil), Gesamtnachfrage, CO₂-Intensität sowie installierte Leistung für Wind (onshore/offshore) und Solar. Neue Monatsdaten erscheinen typischerweise mit ca. 7 Wochen Verzögerung (Augustdaten ca. 20. September). Der Update-Workflow prüft ab dem 17. jeden Monats täglich auf neue Daten und deaktiviert sich nach dem ersten erfolgreichen Update automatisch.

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
  power/
    ember_power.csv             — Stromerzeugung, -nachfrage, CO₂-Intensität (Ember, 2015–)
    ember_capacity.csv          — Installierte Wind-/Solarleistung (Ember, 2015–)
  combined/
    fossil_supply.csv           — Import + Inlandsproduktion fossil (Mai 2026–); auto-rebuild
    energy_balance.csv          — Gesamtenergiesystem in TWh: fossil + sauber, YoY, YTD (Mai 2026–)

scripts/
  fetch_history.py        — Einmalig: lädt ComTrade-Historie 2020–2024
  fetch_comtrade.py       — Monatlich: aktualisiert ComTrade-Daten für 2025
  rech_to_github.py       — Einzeln: extrahiert machine_data aus einer RECH-Datei
  backfill_to_github.py   — Einmalig/lokal: verarbeitet alle annotierten RECH-Dateien
  fetch_ember_history.py  — Einmalig: lädt Ember-Stromhistorie ab 2015
  fetch_ember_monthly.py  — Monatlich: prüft auf neue Ember-Daten und aktualisiert CSVs
  build_supply.py         — Auto: kombiniert GACC-Importe + NBS-Produktion zu fossil_supply.csv
  build_energy_balance.py — Auto: konvertiert alles nach TWh, addiert saubere Stromerzeugung

.github/workflows/
  monthly_update.yml          — Cron: 15. jeden Monats, 06:00 UTC (ComTrade)
  fetch_history.yml           — workflow_dispatch, einmalig (ComTrade)
  fetch_ember_history.yml     — workflow_dispatch, einmalig (Ember)
  monthly_ember_update.yml    — Cron: 17.–31. jeden Monats, 06:00 UTC; deaktiviert sich nach Update
  monthly_ember_reenable.yml  — Cron: 1. jeden Monats, 05:00 UTC; reaktiviert Update-Workflow
  build_supply.yml            — Push-Trigger: rebuild fossil_supply.csv + energy_balance.csv wenn GACC/NBS sich ändern; auch von monthly_ember_update.yml dispatcht
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

### `data/power/ember_power.csv`

Eine Zeile pro Monat. Stromerzeugung nach Energieträger, Gesamtnachfrage und CO₂-Intensität für China.

| Spalte | Einheit | Beschreibung |
|---|---|---|
| period | YYYYMM | Berichtsmonat |
| demand_twh | TWh | Gesamtstromnachfrage |
| coal_twh | TWh | Stromerzeugung aus Kohle |
| coal_share_pct | Prozent | Anteil Kohle an Gesamterzeugung |
| gas_twh | TWh | Stromerzeugung aus Gas |
| gas_share_pct | Prozent | Anteil Gas |
| nuclear_twh | TWh | Stromerzeugung aus Kernkraft |
| nuclear_share_pct | Prozent | Anteil Kernkraft |
| hydro_twh | TWh | Stromerzeugung aus Wasserkraft |
| hydro_share_pct | Prozent | Anteil Wasserkraft |
| wind_twh | TWh | Stromerzeugung aus Wind |
| wind_share_pct | Prozent | Anteil Wind |
| solar_twh | TWh | Stromerzeugung aus Solar |
| solar_share_pct | Prozent | Anteil Solar |
| bioenergy_twh | TWh | Stromerzeugung aus Bioenergie |
| bioenergy_share_pct | Prozent | Anteil Bioenergie |
| other_fossil_twh | TWh | Sonstige fossile Erzeugung |
| other_fossil_share_pct | Prozent | Anteil sonstige Fossile |
| net_imports_twh | TWh | Nettostromimporte |
| net_imports_share_pct | Prozent | Anteil Nettoimporte |
| fossil_twh | TWh | Summe fossil (Kohle + Gas + sonstige Fossile) |
| fossil_share_pct | Prozent | Anteil fossil gesamt |
| clean_twh | TWh | Summe sauber (Erneuerbare + Kernkraft) |
| clean_share_pct | Prozent | Anteil sauber gesamt |
| renewables_twh | TWh | Summe erneuerbar (Wasser + Wind + Solar + Bioenergie) |
| renewables_share_pct | Prozent | Anteil erneuerbar gesamt |
| carbon_intensity_gco2_kwh | gCO₂/kWh | CO₂-Intensität des Strommixes |

### `data/power/ember_capacity.csv`

Eine Zeile pro Monat. Installierte Leistung Wind und Solar.

**Hinweis:** Ember stellt über die monatliche Kapazitäts-API nur Daten für Onshore-Wind, Offshore-Wind und Solar bereit. Kohle, Gas, Kernkraft und Wasserkraft sind dort nicht verfügbar.

| Spalte | Einheit | Beschreibung |
|---|---|---|
| period | YYYYMM | Berichtsmonat |
| onshore_wind_gw | GW | Installierte Onshore-Windleistung |
| offshore_wind_gw | GW | Installierte Offshore-Windleistung |
| wind_gw | GW | Installierte Windleistung gesamt (onshore + offshore) |
| solar_gw | GW | Installierte Solarleistung |

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

**Hinweis Januar/Februar (NBS):** NBS und GACC veröffentlichen Januar und Februar grundsätzlich nur als kombinierten Zweimonatswert. Die Zeile mit `period=202601` enthält daher den kumulierten Jan-Feb-Wert (z. B. 760 Mio. t Kohle für zwei Monate). Die YoY-Angaben beziehen sich ebenfalls auf den kombinierten Zweimonatszeitraum. Ab März sind Einzelmonatswerte ausgewiesen. Diese Struktur ist konsistent mit der GACC-Berichtspraxis.

### `data/combined/fossil_supply.csv`

Automatisch generiert aus `gacc_imports.csv` + `nbs_production.csv`. Eine Zeile pro Monat. Pro Energieträger: Import, Inlandsproduktion, Gesamtangebot, YoY für jede Komponente und das Gesamtaggregat, sowie kumulatives Jahresangebot (YTD) mit YTD-YoY.

**Gas-Einheit:** Alle Gasangaben in BCM. GACC-Importe (Mt) werden mit dem folgenden Faktor konvertiert:

```
gas_import_bcm = gas_import_mt × 1.36
```

**Quelle des Umrechnungsfaktors:** BP Statistical Review of World Energy, Annex: Conversion Factors (jährlich aktualisiert); übereinstimmend mit dem GIIGNL Annual LNG Report (Groupe International des Importateurs de Gaz Naturel Liquéfié).

**Hinweis:** Der Faktor 1 Mt = 1,36 BCM gilt streng genommen für LNG (Flüssigerdgas). Für Pipelinegas in Masseneinheiten läge der Faktor je nach Gaszusammensetzung und Normierungsdruck bei ca. 1,1–1,3 BCM/Mt. Da GACC LNG und Pipelinegas nicht getrennt in Masseneinheiten ausweist und LNG den Großteil der chinesischen Gasimporte ausmacht, wird 1,36 einheitlich angewendet. Die Ursprungsspalte `gas_import_mt` ist zur Nachvollziehbarkeit enthalten.

| Spalte | Einheit | Beschreibung |
|---|---|---|
| period | YYYYMM | Berichtsmonat |
| coal_import_mt | Mio. t | Kohleeinfuhren (GACC) |
| coal_prod_mt | Mio. t | Inlandsproduktion Kohle (NBS) |
| coal_total_mt | Mio. t | Gesamtangebot Kohle |
| coal_import_yoy_pct | Prozent | YoY Kohleeinfuhren |
| coal_prod_yoy_pct | Prozent | YoY Kohleproduktion |
| coal_total_yoy_pct | Prozent | YoY Gesamtangebot Kohle (aus Einzelkomponenten abgeleitet) |
| coal_ytd_mt | Mio. t | Kumulatives Jahresangebot Kohle |
| coal_ytd_yoy_pct | Prozent | YoY kumulatives Jahresangebot Kohle |
| crude_oil_import_mt | Mio. t | Rohöleinfuhren (GACC) |
| crude_oil_prod_mt | Mio. t | Inlandsproduktion Rohöl (NBS) |
| crude_oil_total_mt | Mio. t | Gesamtangebot Rohöl |
| crude_oil_import_yoy_pct | Prozent | YoY Rohöleinfuhren |
| crude_oil_prod_yoy_pct | Prozent | YoY Rohölproduktion |
| crude_oil_total_yoy_pct | Prozent | YoY Gesamtangebot Rohöl |
| crude_oil_ytd_mt | Mio. t | Kumulatives Jahresangebot Rohöl |
| crude_oil_ytd_yoy_pct | Prozent | YoY kumulatives Jahresangebot Rohöl |
| gas_import_mt | Mio. t | Gaseinfuhren LNG + Pipeline (GACC, Originaleinheit) |
| gas_import_bcm | Mrd. m³ | Gaseinfuhren konvertiert (Mt × 1,36) |
| gas_prod_bcm | Mrd. m³ | Inlandsproduktion Gas (NBS) |
| gas_total_bcm | Mrd. m³ | Gesamtangebot Gas |
| gas_import_yoy_pct | Prozent | YoY Gaseinfuhren |
| gas_prod_yoy_pct | Prozent | YoY Gasproduktion |
| gas_total_yoy_pct | Prozent | YoY Gesamtangebot Gas |
| gas_ytd_bcm | Mrd. m³ | Kumulatives Jahresangebot Gas |
| gas_ytd_yoy_pct | Prozent | YoY kumulatives Jahresangebot Gas |

**YoY-Methode:** Die kombinierten YoY-Werte für Gesamt und YTD werden nicht direkt gemessen, sondern aus den Einzelkomponenten abgeleitet. Dazu werden die 2025-Vorjahreswerte aus den jeweils bekannten Einzelkomponenten-YoY-Angaben zurückgerechnet und anschließend addiert. Die Abweichung gegenüber dem tatsächlichen Vorjahreswert ist bei gut belegten Einzelkomponenten vernachlässigbar.

---

## Automatisierung: ComTrade

**GitHub Actions** läuft am 15. jeden Monats (06:00 UTC) und ruft `fetch_comtrade.py` auf. Das Script holt alle verfügbaren 2025-Monate per ComTrade API und pflegt sie per Upsert in die vier Commodity-CSVs ein. Bereits vorhandene 2025-Zeilen werden vollständig ersetzt (idempotent). Ältere Jahre (2020–2024) bleiben unberührt.

ComTrade veröffentlicht Monatsdaten typischerweise mit 2–3 Monaten Verzögerung. Das Script bricht sauber ab, wenn noch keine 2025-Daten verfügbar sind.

Erforderliche GitHub Secrets:
- `COMTRADE_PRIMARY_KEY` — UN ComTrade API Primary Key

---

## Automatisierung: Ember

**GitHub Actions** prüft ab dem 17. jeden Monats täglich (06:00 UTC), ob Ember neue Monatsdaten für China veröffentlicht hat. Liegt ein neuer Monat vor, werden `ember_power.csv` und `ember_capacity.csv` vollständig neu geschrieben und der Workflow deaktiviert sich selbst. Am 1. des Folgemonats (05:00 UTC) reaktiviert ein separater Workflow den Update-Zyklus.

**Warum dieser Mechanismus?** Ember veröffentlicht neue Monatsdaten unregelmäßig, typischerweise mit ca. 7 Wochen Verzögerung. Ein einfacher Tages-Cron würde dauerhaft laufen. Der Selbstdeaktivierungs-Mechanismus stellt sicher, dass der Workflow nach dem ersten erfolgreichen Update bis zum nächsten Monat inaktiv bleibt.

**Einmaliger Historien-Import** (bereits ausgeführt):

```bash
export EMBER_KEY=<key>
python scripts/fetch_ember_history.py
```

Alternativ per `fetch_ember_history`-Workflow (workflow_dispatch). Schreibt beide CSVs mit der vollständigen Geschichte ab 2015.

**Manueller Update-Test:**

```bash
export EMBER_KEY=<key>
python scripts/fetch_ember_monthly.py
```

Das Script gibt `new_data=true/false` und `new_period=YYYYMM` aus. Im GitHub Actions-Kontext werden diese Werte als Step-Outputs gesetzt und steuern Commit und Selbstdeaktivierung.

Erforderliche GitHub Secrets:
- `EMBER_KEY` — Ember API Key

---

## Automatisierung: fossil_supply.csv

`build_supply.yml` triggert automatisch bei jedem Push, der `gacc_imports.csv` oder `nbs_production.csv` verändert. Das Script liest beide CSVs aus dem Repo, berechnet das kombinierte Angebot und committed `data/combined/fossil_supply.csv`. Da der Commit von `github-actions[bot]` stammt, wird kein weiterer Workflow ausgelöst.

Das Script kann auch lokal ausgeführt werden:

```bash
python scripts/build_supply.py
```

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

- **2026 ComTrade**: Sobald UN ComTrade 2026-Daten verfügbar macht, `YEAR` in `fetch_comtrade.py` aktualisieren und den Workflow manuell antriggern.
- **CREA Kapazitätsdaten**: Monatliche installierte Leistung nach Energieträger (Kohle, Gas, Kernkraft, Wasserkraft, Wind, Solar) — derzeit noch nicht integriert.
