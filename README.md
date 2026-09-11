# china-energy-monitor

Strukturierte Monatsdaten zu Chinas Energieimporten, -produktion und Stromerzeugung — und das öffentliche Dashboard, das darauf aufbaut. Fünf Datenquellen, elf Tabellen, vier automatisierte Update-Zyklen.

Live: **[china-energy-monitor.com](https://china-energy-monitor.com)**

---

## Frontend / Dashboard

Das Dashboard läuft als statische GitHub-Pages-Site aus dem Ordner `docs/`. Es gibt keine Build-Pipeline und keinen Server: Der Browser lädt `docs/index.html` und holt alle Chart-Daten zur Laufzeit per JavaScript `fetch()` direkt aus den CSVs dieses Repos.

### Technischer Aufbau

| Komponente | Details |
|---|---|
| Rendering | Statisches HTML, kein Framework |
| Charts | Chart.js 4.4.4 (CDN) |
| Datenzugriff | `fetch()` gegen `raw.githubusercontent.com` — kein Backend nötig |
| Deployment | GitHub Pages aus `docs/`; Domain via `docs/CNAME` |

Beim Seitenaufruf werden elf CSVs parallel geladen:

```
data/power/ember_power.csv
data/power/capacity_additions.csv
data/power/ember_capacity.csv
data/combined/fossil_supply.csv
data/fuel-imports/gacc_imports.csv
data/combined/combined_coal.csv
data/combined/combined_crude_oil.csv
data/combined/combined_lng.csv
data/combined/combined_pipeline_gas.csv
data/combined/energy_balance.csv
data/reference/wb_reference_prices.csv
```

Alle Texte, KPI-Werte, Chart-Titel und Summary-Absätze werden aus den geholten Daten generiert — keine hardcodierten Zahlen oder Datumsangaben im HTML.

### Aktuelle Sektionen

| Nr. | Sektion | Datenquelle | Charts / Inhalt |
|---|---|---|---|
| 1 | This Month At A Glance | ember_power, gacc_imports, capacity_additions | 4 KPI-Karten |
| 2 | Monthly Summary | ember_power, gacc_imports, fossil_supply | Dynamischer Fließtext; Fossil Supply (Butterfly + YoY); Power Generation Mix (gestapeltes Flächendiagramm); Electricity Demand vs. Generation (Liniendiagramm) |
| 3 | Capacity Added | capacity_additions, ember_capacity | 2 Balken (YTD + Monat), 4 Donuts, Fließtext, Installed Capacity Growth (Liniendiagramm Wind + Solar) |
| 4 | Total Energy System | energy_balance, fossil_supply | 2 KPI-Karten (Monat + YTD), 2 Träger-Balken, YTD-Butterfly + YoY-Balken, Import-Dependency Liniendiagramm |
| 5 | Power Generation — Source Breakdown | ember_power, ember_capacity | TWh gestapelt, Share gestapelt, Kohle Dual-Achse, Kapazitätsfaktor Wind + Solar, CO₂-Intensität, Hydro Saisonal (6 Jahrgänge) |
| 6 | Fossil Fuel Imports | combined_*.csv (ComTrade + GACC), gacc_imports | 2 Übersichts-Charts + 4 × 2 Länder-Charts in der Reihenfolge Crude Oil → LNG → Coal → Pipeline Gas |
| 7 | Import Price Benchmarks | gacc_imports, wb_reference_prices | 4 Charts (2×2): GACC VpU alle Träger (USD/t); Crude Oil GACC vs. Brent + Dubai (USD/bbl); Gas GACC vs. LNG Japan (USD/MMBtu); Coal GACC vs. Australian Benchmark (USD/t) |
| 8 | About | — | Spendenaufruf (Stripe), Projektbeschreibung, Datenquellen-Übersicht, Raw-Data-Request (mailto), Feedback-Link |
| 9 | Methodology | — | Quelltabelle mit Links, TWh-Umrechnungsfaktoren, VpU-Erklärung (GACC-Zollrechnung vs. Spot-Benchmarks), Gas BCM-Konversion, ComTrade/GACC-Merge-Logik, Jan/Feb-Reporting, CREA-Verzögerung |

### Daten aktualisieren

Sobald ein neuer Monat in einen der neun CSVs gepusht wird, zeigt das Dashboard beim nächsten Seitenaufruf automatisch die aktuellen Zahlen. Kein Deployment, kein HTML-Edit nötig.

---

## Datenquellen und Abdeckung

| Quelle | Inhalt | Zeitraum | Update |
|---|---|---|---|
| [UN ComTrade](https://comtradeplus.un.org/) API | Fossile Brennstoffimporte nach Lieferland | 2020–laufend | monatlich automatisch (15.) |
| GACC / NBS via Vault | Importmengen + -werte (GACC), Inlandsproduktion (NBS) | Mai 2026–laufend | manuell nach jedem Energiebilanz-RECH |
| Ember API | Stromerzeugung nach Quelle, Nachfrage, CO₂-Intensität, installierte Wind-/Solarleistung | 2015–laufend | monatlich automatisch (17.–31.) |
| CREA Monthly Energy & Air Quality Snapshot | Kapazitätszubau nach Energieträger (Kohle, Gas, Kernkraft, Wasserkraft, Wind, Solar) | Mai 2026–laufend | manuell via machine_data-Block; N-2-Verzögerung |
| [World Bank](https://www.worldbank.org/en/research/commodity-markets) Pink Sheet | Rohstoff-Benchmarks: Brent, Dubai, Coal AU, LNG Japan | Jan 2026–laufend | monatlich automatisch (15.) |

**ComTrade** liefert granulare Herkunftsland-Daten für Kohle, Rohöl, LNG und Pipelinegas — historisch ab 2020, laufend für 2025 automatisiert per GitHub Actions.

**GACC/NBS** liefert die offiziellen chinesischen Monatszahlen (Generalzollverwaltung für Importe, Nationales Statistikamt für Inlandsproduktion). Diese Daten kommen nicht über eine API, sondern werden aus den monatlichen Energiebilanz-Rechercheberichten (RECH-Dateien im lokalen Vault) extrahiert.

**CREA** (Centre for Research on Energy and Clean Air) veröffentlicht monatliche Snapshots zu Chinas Energiesystem und Luftqualität. Der Kapazitätszubau-Abschnitt liefert Daten zu neu installierter Leistung nach Energieträger (in GW) mit einer Verzögerung von zwei Monaten: Für den Berichtsmonat N enthält der Snapshot Daten für N-2. Die Zahlen werden manuell aus dem PDF extrahiert und über den machine_data-Block im RECH-Dokument in `data/power/capacity_additions.csv` gespeichert.

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
    gacc_coal.csv               — Kohleimporte nach Lieferland (GACC, Jan 2025–)
    gacc_crude_oil.csv          — Rohölimporte nach Lieferland (GACC, Jan 2025–)
    gacc_lng.csv                — LNG-Importe nach Lieferland (GACC, Jan 2025–)
    gacc_pipeline_gas.csv       — Pipelinegas-Importe nach Lieferland (GACC, Jan 2025–)
  production/
    nbs_production.csv          — Inlandsproduktion Kohle/Rohöl/Gas (NBS, Mai 2026–)
  power/
    ember_power.csv             — Stromerzeugung, -nachfrage, CO₂-Intensität (Ember, 2015–)
    ember_capacity.csv          — Installierte Wind-/Solarleistung (Ember, 2015–)
    capacity_additions.csv      — Kapazitätszubau nach Träger in GW (CREA, N-2; Mai 2026–)
  combined/
    fossil_supply.csv           — Import + Inlandsproduktion fossil (Mai 2026–); auto-rebuild
    energy_balance.csv          — Gesamtenergiesystem in TWh: fossil + sauber, YoY, YTD (Mai 2026–)
    combined_coal.csv           — Kohleimporte nach Lieferland, ComTrade+GACC (Jan 2020–); auto-rebuild
    combined_crude_oil.csv      — Rohölimporte nach Lieferland, ComTrade+GACC (Jan 2020–); auto-rebuild
    combined_lng.csv            — LNG-Importe nach Lieferland, ComTrade+GACC (Jan 2020–); auto-rebuild
    combined_pipeline_gas.csv   — Pipelinegas-Importe nach Lieferland, ComTrade+GACC (Jan 2020–); auto-rebuild
  reference/
    wb_reference_prices.csv     — Monatliche Rohstoff-Benchmarks (World Bank Pink Sheet): Brent, Dubai, Coal AU, LNG Japan (Jan 2026–); auto-rebuild am 15.

scripts/
  fetch_history.py              — Einmalig: lädt ComTrade-Historie 2020–2024
  fetch_comtrade.py             — Monatlich: aktualisiert ComTrade-Daten für 2025
  rech_to_github.py             — Einzeln: extrahiert machine_data aus einer RECH-Datei
  backfill_to_github.py         — Einmalig/lokal: verarbeitet alle annotierten RECH-Dateien
  fetch_ember_history.py        — Einmalig: lädt Ember-Stromhistorie ab 2015
  fetch_ember_monthly.py        — Monatlich: prüft auf neue Ember-Daten und aktualisiert CSVs
  build_supply.py               — Auto: kombiniert GACC-Importe + NBS-Produktion zu fossil_supply.csv
  build_energy_balance.py       — Auto: konvertiert alles nach TWh, addiert saubere Stromerzeugung
  build_combined.py             — Auto: merged ComTrade + GACC Lieferland-CSVs zu combined_*.csv
  fetch_wb_reference_prices.py  — Monatlich: scrapt Pink Sheet URL, parsed Excel, schreibt wb_reference_prices.csv

.github/workflows/
  monthly_update.yml                    — Cron: 15. jeden Monats, 06:00 UTC (ComTrade)
  fetch_history.yml                     — workflow_dispatch, einmalig (ComTrade)
  fetch_ember_history.yml               — workflow_dispatch, einmalig (Ember)
  monthly_ember_update.yml              — Cron: 17.–31. jeden Monats, 06:00 UTC; deaktiviert sich nach Update
  monthly_ember_reenable.yml            — Cron: 1. jeden Monats, 05:00 UTC; reaktiviert Update-Workflow
  build_supply.yml                      — Push-Trigger: rebuild fossil_supply.csv + energy_balance.csv wenn GACC/NBS sich ändern; auch von monthly_ember_update.yml dispatcht
  build_combined.yml                    — Push-Trigger: rebuild combined_*.csv wenn comtrade_*.csv oder gacc_*.csv sich ändern
  fetch_wb_reference_prices.yml         — Cron: 15. jeden Monats, 06:00 UTC; scrapt World Bank Pink Sheet
  fetch_wb_reference_prices_history.yml — workflow_dispatch, einmalig (Backfill ab Jan 2026)
```

---

## Dateiformat

### `data/fuel-imports/comtrade_*.csv`

Eine Datei pro Energieträger. Jede Zeile ist ein Lieferland für einen Monat.

| Spalte | Einheit | Beschreibung |
|---|---|---|
| period | YYYYMM | Berichtsmonat |
| partner | Text | Lieferland ([UN ComTrade](https://comtradeplus.un.org/) Bezeichnung) |
| value_usd_bn | Mrd. USD | Importwert |
| qty_mt | Mio. t | Importmenge |
| value_per_mt_usd | USD/t | Importwert je Tonne |

HS-Codes: Kohle = 2701, Rohöl = 2709, LNG = 271111, Pipelinegas = 271121.

### `data/fuel-imports/gacc_imports.csv`

Eine Zeile pro Monat. Gesamtimporte aller Lieferländer (GACC-Aggregat).

**Hinweis Januar/Februar (GACC):** GACC veröffentlicht Januar und Februar nie getrennt, sondern stets als kombinierten Zweimonatswert. Ab 2026 werden Jan und Feb dennoch als separate Zeilen geführt: Jan-only wird aus der Jan-Feb-Gesamtsumme abzüglich des separat ausgewiesenen Feb-Werts errechnet (Quelle: GACC XLS, Sheet "Jan-Feb", Spalten Gesamt minus Feb-alone). Die YoY-Felder beider Zeilen bleiben leer, da vergleichbare Monatseinzelwerte für 2025 nicht vorliegen.

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

**Hinweis Januar/Februar (NBS):** NBS veröffentlicht Januar und Februar grundsätzlich nur als kombinierten Zweimonatswert. Die Zeile mit `period=202601` in `nbs_production.csv` enthält daher den kumulierten Jan-Feb-Wert. Ab März sind Einzelmonatswerte ausgewiesen.

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

### `data/combined/energy_balance.csv`

Automatisch generiert aus `fossil_supply.csv` + `ember_power.csv`. Bringt alle Energieträger auf eine gemeinsame Einheit (TWh), so dass das Gesamtenergiesystem — fossile Primärenergie plus saubere Stromerzeugung — in einer einzigen Tabelle vergleichbar wird.

#### Umrechnungsfaktoren

Alle fossilen Brennstoffe werden mit Standardfaktoren der IEA und des BP Statistical Review of World Energy in TWh umgerechnet:

| Energieträger | Faktor | Formel | Grundlage |
|---|---|---|---|
| Kohle | 8,14 TWh/Mt | `Mt × 8,14` | 29,3 GJ/t (Steinkohle-Einheit, tce) |
| Rohöl | 11,63 TWh/Mt | `Mt × 11,63` | 41,87 GJ/t (Öleinheit, toe) |
| Gas | 10,55 TWh/BCM | `BCM × 10,55` | 38 GJ/1.000 m³ (Brennwert, GCV) |

**Quellen:** BP Statistical Review of World Energy, Annex: Conversion Factors (jährlich aktualisiert, bp.com/statisticalreview); IEA Energy Statistics Manual (iea.org), Kapitel: Conversion Factors.

Saubere Stromerzeugung (Kernkraft, Wasserkraft, Wind, Solar, Bioenergie) wird direkt aus Ember in TWh übernommen — keine Umrechnung nötig.

#### Methodischer Hinweis: Primärenergie vs. Endenergie

Fossile Brennstoffmengen entsprechen dem **Primärenergiegehalt** des Brennstoffs (Wärmeinhalt vor Umwandlungsverlusten). Saubere Stromerzeugung ist **Endenergie** (tatsächlich erzeugter Strom). Die Addition beider Größen ergibt einen Proxy für die „ins chinesische Energiesystem eingehende Gesamtenergie" — eine in der journalistischen Energieberichterstattung verbreitete Annäherung, die keine exakte physikalische Äquivalenz beansprucht.

Kohle- und Gasstromerzeugung (Ember) werden **nicht** addiert, um Doppelzählung mit den fossilen Lieferzahlen zu vermeiden.

#### Schema

| Spalte | Einheit | Beschreibung |
|---|---|---|
| period | YYYYMM | Berichtsmonat |
| coal_import_twh | TWh | Kohleeinfuhren in Primärenergie |
| coal_prod_twh | TWh | Inlandsproduktion Kohle in Primärenergie |
| coal_total_twh | TWh | Gesamtangebot Kohle |
| coal_total_yoy_pct | Prozent | YoY Gesamtangebot Kohle |
| coal_ytd_twh | TWh | Kumulatives Jahresangebot Kohle |
| crude_oil_import_twh | TWh | Rohöleinfuhren in Primärenergie |
| crude_oil_prod_twh | TWh | Inlandsproduktion Rohöl in Primärenergie |
| crude_oil_total_twh | TWh | Gesamtangebot Rohöl |
| crude_oil_total_yoy_pct | Prozent | YoY Gesamtangebot Rohöl |
| crude_oil_ytd_twh | TWh | Kumulatives Jahresangebot Rohöl |
| gas_import_twh | TWh | Gaseinfuhren in Primärenergie |
| gas_prod_twh | TWh | Inlandsproduktion Gas in Primärenergie |
| gas_total_twh | TWh | Gesamtangebot Gas |
| gas_total_yoy_pct | Prozent | YoY Gesamtangebot Gas |
| gas_ytd_twh | TWh | Kumulatives Jahresangebot Gas |
| fossil_total_twh | TWh | Fossile Primärenergie gesamt (Kohle + Öl + Gas) |
| fossil_total_yoy_pct | Prozent | YoY fossile Primärenergie gesamt |
| fossil_ytd_twh | TWh | Kumulativ fossile Primärenergie |
| fossil_ytd_yoy_pct | Prozent | YoY kumulativ fossile Primärenergie |
| nuclear_twh | TWh | Stromerzeugung Kernkraft (Ember) |
| hydro_twh | TWh | Stromerzeugung Wasserkraft (Ember) |
| wind_twh | TWh | Stromerzeugung Wind (Ember) |
| solar_twh | TWh | Stromerzeugung Solar (Ember) |
| bioenergy_twh | TWh | Stromerzeugung Bioenergie (Ember) |
| clean_power_twh | TWh | Saubere Stromerzeugung gesamt |
| clean_power_yoy_pct | Prozent | YoY saubere Stromerzeugung |
| clean_power_ytd_twh | TWh | Kumulativ saubere Stromerzeugung |
| clean_power_ytd_yoy_pct | Prozent | YoY kumulativ saubere Stromerzeugung |
| total_twh | TWh | Gesamtenergiesystem (fossil + sauber) |
| total_yoy_pct | Prozent | YoY Gesamtenergiesystem |
| total_ytd_twh | TWh | Kumulativ Gesamtenergiesystem |
| total_ytd_yoy_pct | Prozent | YoY kumulativ Gesamtenergiesystem |

**Jan-Feb-Konvention:** Fossil-Perioden folgen der NBS/GACC-Praxis (202601 = Jan+Feb kombiniert). Die entsprechenden Ember-Perioden 202601 und 202602 werden automatisch summiert, bevor sie mit den fossilen Werten zusammengeführt werden.

---

### `data/power/capacity_additions.csv`

Monatlicher Kapazitätszubau nach Energieträger in Gigawatt (GW). Quelle: CREA Monthly Energy & Air Quality Snapshot. Die Daten erscheinen mit zwei Monaten Verzögerung: Für den Berichtsmonat N liefert CREA Daten für N-2 (der Wert in `crea_period` weicht daher vom RECH-Berichtsmonat in `period` ab). Die Werte werden manuell aus dem CREA-PDF extrahiert und über den machine_data-Block in die CSV geschrieben.

| Spalte | Einheit | Inhalt |
|---|---|---|
| period | YYYYMM | Berichtsmonat des RECH-Dokuments (NBS/GACC-Periode) |
| crea_period | YYYYMM | Monat, für den CREA Zubaudaten liefert (bei Echtzeit-Workflow = period − 2 Monate) |
| thermal_gw | GW | Neu installierte thermische Leistung im Monat (Kohle + Gas kombiniert; CREA weist keine Aufschlüsselung aus) |
| thermal_yoy_pct | Prozent | YoY thermisch, Monat |
| nuclear_gw | GW | Neu installierte Kernkraftleistung im Monat |
| nuclear_yoy_pct | Prozent | YoY Nuklear, Monat (null wenn Vorjahr = 0 GW) |
| hydro_gw | GW | Neu installierte Wasserkraftleistung im Monat |
| hydro_yoy_pct | Prozent | YoY Wasser, Monat |
| wind_gw | GW | Neu installierte Windleistung im Monat (onshore + offshore) |
| wind_yoy_pct | Prozent | YoY Wind, Monat |
| solar_gw | GW | Neu installierte Solarleistung im Monat |
| solar_yoy_pct | Prozent | YoY Solar, Monat |
| total_gw | GW | Gesamter Zubau im Monat |
| total_yoy_pct | Prozent | YoY Gesamt, Monat (abgeleitet; null wenn Komponente fehlt) |
| thermal_ytd_gw | GW | Kumulierter thermischer Zubau Jan–crea_period |
| thermal_ytd_yoy_pct | Prozent | YoY thermisch, kumuliert |
| nuclear_ytd_gw | GW | Kumulierter Nuklear-Zubau |
| nuclear_ytd_yoy_pct | Prozent | YoY Nuklear, kumuliert (null wenn Vorjahr = 0 GW) |
| hydro_ytd_gw | GW | Kumulierter Wasser-Zubau |
| hydro_ytd_yoy_pct | Prozent | YoY Wasser, kumuliert |
| wind_ytd_gw | GW | Kumulierter Wind-Zubau |
| wind_ytd_yoy_pct | Prozent | YoY Wind, kumuliert |
| solar_ytd_gw | GW | Kumulierter Solar-Zubau |
| solar_ytd_yoy_pct | Prozent | YoY Solar, kumuliert |
| total_ytd_gw | GW | Gesamter kumulierter Zubau |
| total_ytd_yoy_pct | Prozent | YoY Gesamt, kumuliert (abgeleitet; null wenn Komponente fehlt) |

**Quelle:** Centre for Research on Energy and Clean Air (CREA), Monthly Energy & Air Quality Snapshot, energyandcleanair.org

---

### `data/reference/wb_reference_prices.csv`

Monatliche Rohstoff-Referenzpreise aus dem [World Bank](https://www.worldbank.org/en/research/commodity-markets) Pink Sheet (CMO-Historical-Data-Monthly.xlsx). Wird am 15. jeden Monats automatisch aktualisiert.

| Spalte | Einheit | Beschreibung |
|---|---|---|
| period | YYYYMM | Berichtsmonat |
| brent_usd_bbl | USD/bbl | Brent-Rohöl (Spot) |
| dubai_usd_bbl | USD/bbl | Dubai-Rohöl (Spot) |
| coal_au_usd_mt | USD/t | Australische Kraftwerkskohle (Newcastle) |
| lng_japan_usd_mmbtu | USD/MMBtu | LNG Japan (JKM-Proxy) |

**Verwendungszweck im Dashboard:** Vergleich mit den GACC-Importpreisen (VpU) in der Sektion "Import Price Benchmarks". Für den Vergleich wird der GACC-VpU umgerechnet: Rohöl USD/t ÷ 7,33 = USD/bbl; Gas USD/t ÷ 52 = USD/MMBtu; Kohle direkt.

**Datenquelle:** [World Bank](https://www.worldbank.org/en/research/commodity-markets) Commodity Markets, Pink Sheet (monatlich). Die Excel-URL ändert sich monatlich; `fetch_wb_reference_prices.py` scrapt sie zur Laufzeit von der WB-Seite.

---

## Automatisierung: ComTrade

**GitHub Actions** läuft am 15. jeden Monats (06:00 UTC) und ruft `fetch_comtrade.py` auf. Das Script holt alle verfügbaren 2025-Monate per ComTrade API und pflegt sie per Upsert in die vier Commodity-CSVs ein. Bereits vorhandene 2025-Zeilen werden vollständig ersetzt (idempotent). Ältere Jahre (2020–2024) bleiben unberührt.

ComTrade veröffentlicht Monatsdaten typischerweise mit 2–3 Monaten Verzögerung. Das Script bricht sauber ab, wenn noch keine 2025-Daten verfügbar sind.

Erforderliche GitHub Secrets:
- `COMTRADE_PRIMARY_KEY` — [UN ComTrade](https://comtradeplus.un.org/) API Primary Key

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

## Automatisierung: World Bank Reference Prices

**GitHub Actions** läuft am 15. jeden Monats (06:00 UTC) und ruft `fetch_wb_reference_prices.py` auf. Das Script scrapt die aktuelle Pink-Sheet-URL von der [World Bank](https://www.worldbank.org/en/research/commodity-markets) Commodity Markets-Seite, downloaded das Excel, parsed das Sheet "Monthly Prices" und schreibt `data/reference/wb_reference_prices.csv` per Upsert. Bereits vorhandene Zeilen werden ersetzt, ältere bleiben erhalten.

Der Update-Zeitpunkt (15.) liegt bewusst vor dem Energiebilanz-Update (~20.), sodass bei jedem manuellen GACC-Push aktuelle Referenzpreise vorliegen.

**Einmaliger Backfill** (bereits ausgeführt, ab Jan 2026):

```bash
START_PERIOD=202601 python scripts/fetch_wb_reference_prices.py
```

Alternativ per `fetch_wb_reference_prices_history`-Workflow (workflow_dispatch).

Keine zusätzlichen GitHub Secrets erforderlich — der [World Bank](https://www.worldbank.org/en/research/commodity-markets) Pink Sheet ist öffentlich zugänglich.

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

## Manueller Workflow: CREA-Kapazitätszubau

CREA veröffentlicht den monatlichen Snapshot als PDF auf energyandcleanair.org. Die Kapazitätszubau-Daten werden im Rahmen des `/energiebilanz`-Skills (Schritt 9b) aus dem PDF extrahiert und über den machine_data-Block in `capacity_additions.csv` übertragen.

### Datenverzögerung

CREA liefert Daten mit ca. zwei Monaten Verzögerung. Für den Energiebilanz-Bericht zu Berichtsmonat N enthält der aktuelle CREA-Snapshot die Zubaudaten für Monat N-2. Die Spalte `crea_period` im CSV dokumentiert, für welchen Monat die Zubaudaten tatsächlich gelten.

### Schritt 1: CREA-Snapshot beschaffen

Der aktuelle Snapshot wird per Gmail-Suche oder direkt von energyandcleanair.org bezogen. Das PDF wird als Quelle in ein NotebookLM-Notebook geladen und per Chat-Abfrage ausgewertet (automatisiert über `/energiebilanz` Schritt 1, 3 und 9b).

### Schritt 2: machine_data-Block befüllen

Die aus dem Notebook extrahierten Werte werden in den `capacity_additions`-Block am Ende der RECH-Datei eingetragen:

```
<!--machine_data
...
capacity_additions:
  crea_period: "202605"
  thermal_gw: 8.7
  thermal_yoy_pct: -4.0
  nuclear_gw: 0.0
  nuclear_yoy_pct: null
  hydro_gw: 1.6
  hydro_yoy_pct: null
  wind_gw: 3.8
  wind_yoy_pct: -85.0
  solar_gw: 8.7
  solar_yoy_pct: -91.0
  total_gw: 18.5
  total_yoy_pct: null
  thermal_ytd_gw: 32.4
  thermal_ytd_yoy_pct: 84.0
  nuclear_ytd_gw: 3.6
  nuclear_ytd_yoy_pct: null
  hydro_ytd_gw: 4.1
  hydro_ytd_yoy_pct: 24.0
  wind_ytd_gw: 25.0
  wind_ytd_yoy_pct: -46.0
  solar_ytd_gw: 59.6
  solar_ytd_yoy_pct: -70.0
  total_ytd_gw: 124.7
  total_ytd_yoy_pct: null
-->
```

`null` bei `nuclear_yoy_pct` und `nuclear_ytd_yoy_pct` wenn der Vorjahreswert 0 GW betrug (Division durch null). `total_yoy_pct` und `total_ytd_yoy_pct` werden manuell aus den Komponenten rückgerechnet und eingetragen, wenn alle Komponenten bekannt sind.

### Schritt 3: Extraktion und Push

Identisch zum GACC/NBS-Workflow:

```bash
python scripts/rech_to_github.py \
    --file "11_Recherche/Berichte/260902_RECH_China_Energiebilanz_August2026.md"
```

Das Script liest den `capacity_additions`-Block und schreibt die Zeile per Upsert in `data/power/capacity_additions.csv`.

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
openpyxl          — Excel-Parsing (World Bank Pink Sheet)
```

Lokal: `pip install -r requirements.txt` in einem venv. Auf macOS mit extern verwaltetem Python empfiehlt sich ein venv unter `/tmp/` oder `~/.venv/`.

---

## GACC Lieferland-Daten (gacc_*.csv)

GACC veröffentlicht monatlich granulare Importdaten nach Lieferland. Die vier Lieferland-CSVs (`gacc_coal.csv`, `gacc_crude_oil.csv`, `gacc_lng.csv`, `gacc_pipeline_gas.csv`) füllen die ComTrade-Lücke ab Januar 2025: ComTrade liefert Monatsdaten mit 18–20 Monaten Verzögerung und hat die 2025er Daten noch nicht. GACC liefert aktuell bis ca. 6 Wochen nach Berichtsmonat.

**Schema** (identisch für alle vier Dateien):

| Spalte | Einheit | Beschreibung |
|---|---|---|
| period | YYYYMM | Berichtsmonat |
| partner | Text | Lieferland (ComTrade-Namenskonvention) |
| value_usd_bn | Mrd. USD | Importwert |

**Abweichungen zu ComTrade:** GACC weist keine Mengendaten (`qty_mt`) in den öffentlichen CSV-Downloads aus. Spalten `qty_mt` und `value_per_mt_usd` fehlen daher in den GACC-Lieferland-CSVs. Im Dashboard werden Mengendiagramme nur für den ComTrade-Zeitraum (2020–2024) gerendert.

**HS-Codes und Kategorisierung:**

| Kategorie | GACC-HS-Codes | ComTrade-HS-Code |
|---|---|---|
| coal | 270111 + 270112 + 270119 | 2701 |
| crude_oil | 270900 | 2709 |
| lng | 271111 | 271111 |
| pipeline_gas | 271121 | 271121 |

**Manuelle Aktualisierung:** GACC stellt keine maschinenlesbare API bereit. Neue CSVs werden von GACC heruntergeladen (GBK-Encoding), transformiert und ins Repo gepusht. Bei Push triggert `build_combined.yml` automatisch den Rebuild der `combined_*.csv`.

---

## Automatisierung: combined_*.csv

`build_combined.yml` triggert bei jedem Push, der `data/fuel-imports/comtrade_*.csv` oder `data/fuel-imports/gacc_*.csv` verändert. Das Script `scripts/build_combined.py` mergt beide Quellen mit ComTrade-Priorität:

- Für jeden `(period, partner)`-Eintrag, der in ComTrade vorliegt, werden die ComTrade-Werte verwendet.
- GACC füllt alle Perioden, für die ComTrade noch keine Daten hat (aktuell ab Januar 2025).
- Wenn ComTrade 2025-Daten nachliefert, überschreibt der nächste Rebuild automatisch die GACC-Zeilen für diese Perioden.

Lokal ausführen:

```bash
python scripts/build_combined.py
```

**Output-Schema** (`data/combined/combined_*.csv`):

| Spalte | Einheit | Beschreibung |
|---|---|---|
| period | YYYYMM | Berichtsmonat |
| partner | Text | Lieferland |
| value_usd_bn | Mrd. USD | Importwert |
| qty_mt | Mio. t | Importmenge (nur ComTrade-Zeilen; GACC: leer) |
| value_per_mt_usd | USD/t | Preis je Tonne (nur ComTrade-Zeilen) |
| source | comtrade / gacc | Herkunft der Zeile |

---

## Offene Erweiterungen

- **2026 ComTrade**: Sobald UN ComTrade 2026-Daten verfügbar macht, `YEAR` in `fetch_comtrade.py` aktualisieren und den Workflow manuell antriggern.
- **Pipeline-Gas Begleittext**: Dashboard-Abschnitt "Pipeline Gas Imports" braucht einen erklärenden Textblock. Thema: warum die Pipelinegas-Importe bis 2021 nominal höher erscheinen als danach (Central Asia Line D-Stall, Turkmenistan-Lieferprobleme, beschleunigtes chinesisches Shale-Gas-Wachstum, Power of Siberia-Hochlauf ab 2019). Auch SEO-relevant.

---

## Import Price Benchmarks — Konzept und Methodik

`gacc_imports.csv` enthält für Kohle, Rohöl und Gas den impliziten Importpreis (Value per Unit, VpU) aus den GACC-Zolldaten. Dieser Preis ist ein gewichteter Durchschnitt aller tatsächlichen physischen Transaktionen im Monat — kein Spot- oder Papierpreis, sondern was China tatsächlich bezahlt hat. Ein Vergleich mit Markt-Benchmarks erlaubt näherungsweise Aussagen darüber, ob China über oder unter Marktpreisen kauft.

**Methodischer Vorbehalt:** Alle Benchmark-Preise sind Spot- oder Assessment-Preise, Chinas Importe basieren größtenteils auf Langzeitverträgen (oft ölindexiert) oder politisch ausgehandelten Preisen (Zentralasien, Russland). Der Vergleich ist strukturell ungleich, aber journalistisch aussagekräftig — insbesondere Trendbrüche (China kauft Öl nach 2022 deutlich unter Brent = Russland-Rabatt-Effekt) sind sichtbar.

**Iran-Hinweis:** Iranisches Öl taucht in GACC-Daten nicht auf (erfasst als Malaysia, UAE, Oman). Strukturelles Datenloch.

### Einheiten und Umrechnungen

| Träger | GACC-VpU | Dashboard-Einheit | Umrechnung |
|---|---|---|---|
| Kohle | USD/t | USD/t | direkt vergleichbar |
| Rohöl | USD/t | USD/bbl | ÷ 7,33 (IEA-Standardfaktor) |
| Gas | USD/t | USD/MMBtu | ÷ 52 (LNG-Faustregel; GIIGNL: 43–49 MMBtu/t) |

### Benchmark-Quellen

| Träger | Benchmark | Quelle |
|---|---|---|
| Rohöl | Brent ($/bbl) + Dubai ($/bbl) | World Bank Pink Sheet |
| Gas | LNG Japan ($/MMBtu) — JKM-Proxy | World Bank Pink Sheet |
| Kohle | Coal Australian — Newcastle ($/t) | World Bank Pink Sheet |
