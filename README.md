# china-energy-monitor

Monthly data on China's energy system and EV transition — and the public dashboard built on top of it. Six data sources, fourteen CSVs, five automated update cycles.

Live: **[china-energy-monitor.com](https://china-energy-monitor.com)**

---

## Frontend / Dashboard

The dashboard runs as a static GitHub Pages site from the `docs/` folder. There is no build pipeline and no server: the browser loads `docs/index.html` and fetches all chart data at runtime via JavaScript `fetch()` directly from the CSVs in this repo.

### Technical setup

| Component | Details |
|---|---|
| Rendering | Static HTML, no framework |
| Charts | Chart.js 4.4.4 (CDN) |
| Data access | `fetch()` against `raw.githubusercontent.com` — no backend required |
| Deployment | GitHub Pages from `docs/`; custom domain via `docs/CNAME` |
| Analytics | GoatCounter (privacy-friendly, no cookies) |

On page load, fourteen CSVs are fetched in parallel:

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
data/power/gem_coal_capacity.csv
data/transport/china_car_sales_retail.csv
data/transport/china_car_sales_projection.csv
data/transport/fuel_savings.csv
```

All text, KPI values, chart titles, and summary paragraphs are generated from the fetched data. No hardcoded numbers or dates in the HTML.

### Sections

| # | Section | Data source | Content |
|---|---|---|---|
| 1 | This Month At A Glance | ember_power, gacc_imports, capacity_additions, china_car_sales_retail, fuel_savings | 6 KPI cards (energy + BEV share + EV oil displacement YTD) |
| 2 | Monthly Summary | ember_power, gacc_imports, fossil_supply | Dynamic prose; Fossil Supply (Butterfly + YoY); Power Generation Mix (stacked area); Electricity Demand vs. Generation (line chart) |
| 3 | Capacity Added | capacity_additions, ember_capacity, nea_battery_storage | 2 bar charts (YTD + monthly), 4 donuts, prose, Installed Capacity Growth (Wind + Solar line chart), Battery Storage Growth (annual GW / GWh / Duration) |
| 4 | Total Energy System | energy_balance, fossil_supply | 2 KPI cards (month + YTD), 2 carrier bars, YTD butterfly + YoY bars, Import Dependency line chart |
| 5 | Power Generation — Source Breakdown | ember_power, ember_capacity | TWh stacked, share stacked, Coal dual-axis, Wind + Solar capacity factor, CO₂ intensity, Hydro seasonal (6 vintages) |
| 6 | Fossil Fuel Imports | combined_*.csv (ComTrade + GACC), gacc_imports | 2 overview charts + 4 × 2 country-of-origin charts: Crude Oil → LNG → Coal → Pipeline Gas |
| 7 | Import Price Benchmarks | gacc_imports, wb_reference_prices | 4 charts (2×2): GACC VpU all fuels (USD/t); Crude Oil GACC vs. Brent + Dubai (USD/bbl); Gas GACC vs. LNG Japan (USD/MMBtu); Coal GACC vs. Australian Benchmark (USD/t) |
| 8 | EV Transition | china_car_sales_retail, china_car_sales_projection | The Cliff (stacked bar: BEV/PHEV/EREV/ICE share); Trajectory to 2040 (actual bars + S-curve projection lines) |
| 9 | Oil Displacement & Energy Balance | fuel_savings | 2 KPI tiles (full-year 2026 crude mb + net TWh); Crude Oil Displaced (bar + projection line, mb/d); Primary Energy Balance (stacked area: fuel savings vs. grid cost, TWh/month) |
| 10 | About | — | Donation (Stripe), project description, data sources, raw data request (mailto), feedback link |
| 11 | Methodology | — | Source table with links, TWh conversion factors, VpU explanation, gas BCM conversion, ComTrade/GACC merge logic, Jan/Feb reporting, CREA delay, EV S-curve parameters, oil displacement model |

### Updating data

Once a new month is pushed to any of the eleven CSVs, the dashboard automatically shows the updated numbers on the next page load. No deployment or HTML edit required.

---

## Data sources and coverage

| Source | Content | Period | Update |
|---|---|---|---|
| [UN ComTrade](https://comtradeplus.un.org/) API | Fossil fuel imports by country of origin | 2020–ongoing | Monthly automated (15th) |
| GACC / NBS via Vault | Import volumes + values (GACC), domestic production (NBS) | May 2026–ongoing | Manual after each energy balance report |
| Ember API | Power generation by source, demand, CO₂ intensity, installed wind/solar capacity | 2015–ongoing | Monthly automated (17th–31st) |
| CREA Monthly Energy & Air Quality Snapshot | Capacity additions by source (coal, gas, nuclear, hydro, wind, solar) | May 2026–ongoing | Manual via machine_data block; N-2 delay |
| [World Bank](https://www.worldbank.org/en/research/commodity-markets) Pink Sheet | Commodity benchmarks: Brent, Dubai, Coal AU, LNG Japan | Jan 2026–ongoing | Monthly automated (15th) |
| CPCA via [@leRaffl](https://x.com/leRaffl) | Monthly passenger car retail + wholesale sales by drivetrain (BEV, PHEV, EREV, ICE) | Nov 2016–ongoing | Monthly automated (8th–end of month) |
| NEA (National Energy Administration, China) | Annual cumulative new-type battery storage capacity (GW, GWh) and duration ratio | 2021–ongoing | Manual, once per year after NEA year-end press conference |

**ComTrade** provides granular country-of-origin data for coal, crude oil, LNG, and pipeline gas — historical from 2020, automated for 2025 via GitHub Actions.

**GACC/NBS** provides the official Chinese monthly figures (General Administration of Customs for imports, National Bureau of Statistics for domestic production). These data are not available via API; they are extracted from monthly energy balance research reports (RECH files in the local vault).

**CREA** (Centre for Research on Energy and Clean Air) publishes monthly snapshots of China's energy system and air quality. Capacity addition data covers newly installed capacity by source (GW) with a two-month delay: for reporting month N, the current CREA snapshot contains data for N-2. Values are extracted manually from the PDF and written to `data/power/capacity_additions.csv` via the machine_data block in the RECH document.

**Ember** provides monthly electricity data for China from 2015: generation by source (TWh and share), total demand, CO₂ intensity, and installed capacity for wind (onshore/offshore) and solar. New monthly data typically appear with a ~7-week delay (August data around 20 September). The update workflow checks for new data daily from the 17th of each month and self-deactivates after the first successful update.

---

## Repo structure

```
data/
  fuel-imports/
    comtrade_coal.csv           — Coal imports by country of origin (ComTrade, 2020–)
    comtrade_crude_oil.csv      — Crude oil imports by country of origin (ComTrade, 2020–)
    comtrade_lng.csv            — LNG imports by country of origin (ComTrade, 2020–)
    comtrade_pipeline_gas.csv   — Pipeline gas imports by country of origin (ComTrade, 2020–)
    gacc_imports.csv            — Total imports coal/crude oil/gas (GACC, May 2026–)
    gacc_coal.csv               — Coal imports by country of origin (GACC, Jan 2025–)
    gacc_crude_oil.csv          — Crude oil imports by country of origin (GACC, Jan 2025–)
    gacc_lng.csv                — LNG imports by country of origin (GACC, Jan 2025–)
    gacc_pipeline_gas.csv       — Pipeline gas imports by country of origin (GACC, Jan 2025–)
  production/
    nbs_production.csv          — Domestic production coal/crude oil/gas (NBS, May 2026–)
  power/
    ember_power.csv             — Power generation, demand, CO₂ intensity (Ember, 2015–)
    ember_capacity.csv          — Installed wind/solar capacity (Ember, 2015–)
    capacity_additions.csv      — Monthly capacity additions by source in GW (CREA, N-2; May 2026–)
  combined/
    fossil_supply.csv           — Import + domestic production fossil (May 2026–); auto-rebuild
    energy_balance.csv          — Total energy system in TWh: fossil + clean, YoY, YTD (May 2026–); auto-rebuild
    combined_coal.csv           — Coal imports by country, ComTrade+GACC (Jan 2020–); auto-rebuild
    combined_crude_oil.csv      — Crude oil imports by country, ComTrade+GACC (Jan 2020–); auto-rebuild
    combined_lng.csv            — LNG imports by country, ComTrade+GACC (Jan 2020–); auto-rebuild
    combined_pipeline_gas.csv   — Pipeline gas imports by country, ComTrade+GACC (Jan 2020–); auto-rebuild
  reference/
    wb_reference_prices.csv     — Monthly commodity benchmarks (World Bank Pink Sheet): Brent, Dubai, Coal AU, LNG Japan (Jan 2026–); auto-rebuild on 15th
  transport/
    china_car_sales_retail.csv  — Monthly retail car sales by drivetrain: BEV, PHEV, EREV, ICE, TOTAL (CPCA via @leRaffl, Nov 2016–)
    china_car_sales_wholesale.csv — Monthly wholesale car sales by drivetrain (CPCA via @leRaffl, Sep 2024–)
    china_car_sales_projection.csv — S-curve BEV projection 2016–2040 (auto-rebuilt monthly)
    fuel_savings.csv            — Monthly crude oil displacement (mb/d) and primary energy balance (TWh) from China's EV fleet (Weibull model, auto-rebuilt monthly)
  storage/
    nea_battery_storage.csv     — Annual cumulative new-type battery storage installed capacity: GW, GWh, duration ratio (NEA, 2021–; updated once per year)

scripts/
  fetch_history.py              — One-time: loads ComTrade history 2020–2024
  fetch_comtrade.py             — Monthly: updates ComTrade data for 2025
  rech_to_github.py             — Single file: extracts machine_data from one RECH file
  backfill_to_github.py         — One-time/local: processes all annotated RECH files
  fetch_ember_history.py        — One-time: loads Ember power history from 2015
  fetch_ember_monthly.py        — Monthly: checks for new Ember data and updates CSVs
  build_supply.py               — Auto: combines GACC imports + NBS production into fossil_supply.csv
  build_energy_balance.py       — Auto: converts everything to TWh, adds clean power generation
  build_combined.py             — Auto: merges ComTrade + GACC country-of-origin CSVs into combined_*.csv
  fetch_wb_reference_prices.py  — Monthly: scrapes Pink Sheet URL, parses Excel, writes wb_reference_prices.csv
  fetch_china_car_sales.py      — Monthly: pulls retail + wholesale CSVs from @leRaffl, appends new rows only
  build_car_projection.py       — Auto: fits logistic S-curve to retail BEV share, writes china_car_sales_projection.csv
  compute_fuel_savings.py       — Auto: Weibull fleet model; reads retail + projection CSVs, writes fuel_savings.csv

.github/workflows/
  monthly_update.yml                    — Cron: 15th of each month, 06:00 UTC (ComTrade)
  fetch_history.yml                     — workflow_dispatch, one-time (ComTrade)
  fetch_ember_history.yml               — workflow_dispatch, one-time (Ember)
  monthly_ember_update.yml              — Cron: 17th–31st of each month, 06:00 UTC; self-deactivates after update
  monthly_ember_reenable.yml            — Cron: 1st of each month, 05:00 UTC; re-enables update workflow
  build_supply.yml                      — Push trigger: rebuilds fossil_supply.csv + energy_balance.csv when GACC/NBS changes; also dispatched by monthly_ember_update.yml
  build_combined.yml                    — Push trigger: rebuilds combined_*.csv when comtrade_*.csv or gacc_*.csv changes
  fetch_wb_reference_prices.yml         — Cron: 15th of each month, 06:00 UTC; scrapes World Bank Pink Sheet
  fetch_wb_reference_prices_history.yml — workflow_dispatch, one-time (backfill from Jan 2026)
  fetch_china_car_sales.yml             — Cron: daily 07:00 UTC from 8th of each month; pulls @leRaffl data, rebuilds projection, runs fuel savings model, self-stops after first new data found
```

---

## File formats

### `data/fuel-imports/comtrade_*.csv`

One file per fuel. Each row is one country of origin for one month.

| Column | Unit | Description |
|---|---|---|
| period | YYYYMM | Reporting month |
| partner | Text | Country of origin ([UN ComTrade](https://comtradeplus.un.org/) name) |
| value_usd_bn | USD bn | Import value |
| qty_mt | Mt | Import volume |
| value_per_mt_usd | USD/t | Import value per tonne |

HS codes: Coal = 2701, Crude oil = 2709, LNG = 271111, Pipeline gas = 271121.

### `data/fuel-imports/gacc_imports.csv`

One row per month. Total imports across all countries of origin (GACC aggregate).

**January/February note (GACC):** GACC never publishes January and February separately; they are always combined into a single two-month figure. From 2026 onwards, January and February are stored as separate rows: the January-only value is derived by subtracting the standalone February figure from the combined Jan-Feb total (source: GACC XLS, sheet "Jan-Feb"). YoY fields for both rows are left empty because comparable monthly breakdowns for 2025 are not available.

| Column | Unit | Description |
|---|---|---|
| period | YYYYMM | Reporting month |
| coal_mt | Mt | Coal imports (volume) |
| coal_mt_yoy_pct | Pct | YoY change in volume |
| coal_usd_bn | USD bn | Coal imports (value) |
| coal_usd_bn_yoy_pct | Pct | YoY change in value |
| coal_usd_per_mt | USD/t | Coal price per tonne |
| crude_oil_mt | Mt | Crude oil imports (volume) |
| crude_oil_mt_yoy_pct | Pct | YoY change in volume |
| crude_oil_usd_bn | USD bn | Crude oil imports (value) |
| crude_oil_usd_bn_yoy_pct | Pct | YoY change in value |
| crude_oil_usd_per_mt | USD/t | Crude oil price per tonne |
| gas_mt | Mt | Gas imports LNG + pipeline (volume) |
| gas_mt_yoy_pct | Pct | YoY change in volume |
| gas_usd_bn | USD bn | Gas imports (value) |
| gas_usd_bn_yoy_pct | Pct | YoY change in value |
| gas_usd_per_mt | USD/t | Gas price per tonne |

### `data/power/ember_power.csv`

One row per month. Power generation by source, total demand, and CO₂ intensity for China.

| Column | Unit | Description |
|---|---|---|
| period | YYYYMM | Reporting month |
| demand_twh | TWh | Total electricity demand |
| coal_twh | TWh | Power generation from coal |
| coal_share_pct | Pct | Coal share of total generation |
| gas_twh | TWh | Power generation from gas |
| gas_share_pct | Pct | Gas share |
| nuclear_twh | TWh | Power generation from nuclear |
| nuclear_share_pct | Pct | Nuclear share |
| hydro_twh | TWh | Power generation from hydro |
| hydro_share_pct | Pct | Hydro share |
| wind_twh | TWh | Power generation from wind |
| wind_share_pct | Pct | Wind share |
| solar_twh | TWh | Power generation from solar |
| solar_share_pct | Pct | Solar share |
| bioenergy_twh | TWh | Power generation from bioenergy |
| bioenergy_share_pct | Pct | Bioenergy share |
| other_fossil_twh | TWh | Other fossil generation |
| other_fossil_share_pct | Pct | Other fossil share |
| net_imports_twh | TWh | Net electricity imports |
| net_imports_share_pct | Pct | Net imports share |
| fossil_twh | TWh | Total fossil (coal + gas + other fossil) |
| fossil_share_pct | Pct | Total fossil share |
| clean_twh | TWh | Total clean (renewables + nuclear) |
| clean_share_pct | Pct | Total clean share |
| renewables_twh | TWh | Total renewables (hydro + wind + solar + bioenergy) |
| renewables_share_pct | Pct | Total renewables share |
| carbon_intensity_gco2_kwh | gCO₂/kWh | Grid carbon intensity |

### `data/power/ember_capacity.csv`

One row per month. Installed wind and solar capacity.

**Note:** The Ember monthly capacity API provides data for onshore wind, offshore wind, and solar only. Coal, gas, nuclear, and hydro are not available there.

| Column | Unit | Description |
|---|---|---|
| period | YYYYMM | Reporting month |
| onshore_wind_gw | GW | Installed onshore wind capacity |
| offshore_wind_gw | GW | Installed offshore wind capacity |
| wind_gw | GW | Total installed wind capacity (onshore + offshore) |
| solar_gw | GW | Installed solar capacity |

### `data/production/nbs_production.csv`

One row per month. Chinese domestic production per NBS.

| Column | Unit | Description |
|---|---|---|
| period | YYYYMM | Reporting month |
| coal_mt | Mt | Raw coal production |
| coal_mt_yoy_pct | Pct | YoY change |
| crude_oil_mt | Mt | Crude oil production |
| crude_oil_mt_yoy_pct | Pct | YoY change |
| gas_bcm | BCM | Natural gas production |
| gas_bcm_yoy_pct | Pct | YoY change |

**January/February note (NBS):** NBS publishes January and February only as a combined two-month figure. The row with `period=202601` in `nbs_production.csv` therefore contains the cumulative Jan-Feb value. From March onwards, individual monthly values are reported.

### `data/combined/fossil_supply.csv`

Auto-generated from `gacc_imports.csv` + `nbs_production.csv`. One row per month. Per fuel: imports, domestic production, total supply, YoY for each component and the aggregate, plus cumulative year-to-date supply (YTD) with YTD YoY.

**Gas unit:** All gas figures in BCM. GACC imports (Mt) are converted using the following factor:

```
gas_import_bcm = gas_import_mt × 1.36
```

**Source of conversion factor:** BP Statistical Review of World Energy, Annex: Conversion Factors (updated annually); consistent with the GIIGNL Annual LNG Report.

**Note:** The factor 1 Mt = 1.36 BCM applies strictly to LNG. For pipeline gas in mass units, the factor would be approximately 1.1–1.3 BCM/Mt depending on gas composition and reference pressure. Since GACC does not separate LNG and pipeline gas in mass units and LNG accounts for the majority of Chinese gas imports, 1.36 is applied uniformly. The original `gas_import_mt` column is retained for reference.

| Column | Unit | Description |
|---|---|---|
| period | YYYYMM | Reporting month |
| coal_import_mt | Mt | Coal imports (GACC) |
| coal_prod_mt | Mt | Domestic coal production (NBS) |
| coal_total_mt | Mt | Total coal supply |
| coal_import_yoy_pct | Pct | YoY coal imports |
| coal_prod_yoy_pct | Pct | YoY coal production |
| coal_total_yoy_pct | Pct | YoY total coal supply (derived from components) |
| coal_ytd_mt | Mt | Cumulative YTD coal supply |
| coal_ytd_yoy_pct | Pct | YoY cumulative coal supply |
| crude_oil_import_mt | Mt | Crude oil imports (GACC) |
| crude_oil_prod_mt | Mt | Domestic crude oil production (NBS) |
| crude_oil_total_mt | Mt | Total crude oil supply |
| crude_oil_import_yoy_pct | Pct | YoY crude oil imports |
| crude_oil_prod_yoy_pct | Pct | YoY crude oil production |
| crude_oil_total_yoy_pct | Pct | YoY total crude oil supply |
| crude_oil_ytd_mt | Mt | Cumulative YTD crude oil supply |
| crude_oil_ytd_yoy_pct | Pct | YoY cumulative crude oil supply |
| gas_import_mt | Mt | Gas imports LNG + pipeline (GACC, original unit) |
| gas_import_bcm | BCM | Gas imports converted (Mt × 1.36) |
| gas_prod_bcm | BCM | Domestic gas production (NBS) |
| gas_total_bcm | BCM | Total gas supply |
| gas_import_yoy_pct | Pct | YoY gas imports |
| gas_prod_yoy_pct | Pct | YoY gas production |
| gas_total_yoy_pct | Pct | YoY total gas supply |
| gas_ytd_bcm | BCM | Cumulative YTD gas supply |
| gas_ytd_yoy_pct | Pct | YoY cumulative gas supply |

**YoY method:** Combined YoY values for totals and YTD are not directly measured but derived from the individual components. Prior-year values are back-calculated from the known component-level YoY figures and then summed. The deviation from the actual prior-year aggregate is negligible when all components are well-documented.

### `data/combined/energy_balance.csv`

Auto-generated from `fossil_supply.csv` + `ember_power.csv`. Brings all energy carriers to a common unit (TWh) so the total energy system — fossil primary energy plus clean power generation — can be compared in a single table.

#### Conversion factors

All fossil fuels are converted to TWh using standard IEA and BP Statistical Review factors:

| Fuel | Factor | Formula | Basis |
|---|---|---|---|
| Coal | 8.14 TWh/Mt | `Mt × 8.14` | 29.3 GJ/t (tce, standard coal equivalent) |
| Crude oil | 11.63 TWh/Mt | `Mt × 11.63` | 41.87 GJ/t (toe, tonne of oil equivalent) |
| Gas | 10.55 TWh/BCM | `BCM × 10.55` | 38 GJ/1,000 m³ (gross calorific value) |

**Sources:** BP Statistical Review of World Energy, Annex: Conversion Factors; IEA Energy Statistics Manual, chapter: Conversion Factors.

Clean power generation (nuclear, hydro, wind, solar, bioenergy) is taken directly from Ember in TWh — no conversion required.

#### Methodological note: primary vs. final energy

Fossil fuel volumes represent the **primary energy content** of the fuel (heat content before conversion losses). Clean power generation is **final energy** (electricity actually produced). Adding both yields a proxy for total energy entering the Chinese system — a common approximation in energy reporting that does not claim physical equivalence.

Coal and gas power generation from Ember are **not** added, to avoid double-counting with the fossil supply figures.

#### Schema

| Column | Unit | Description |
|---|---|---|
| period | YYYYMM | Reporting month |
| coal_import_twh | TWh | Coal imports in primary energy |
| coal_prod_twh | TWh | Domestic coal production in primary energy |
| coal_total_twh | TWh | Total coal supply |
| coal_total_yoy_pct | Pct | YoY total coal supply |
| coal_ytd_twh | TWh | Cumulative YTD coal supply |
| crude_oil_import_twh | TWh | Crude oil imports in primary energy |
| crude_oil_prod_twh | TWh | Domestic crude oil production in primary energy |
| crude_oil_total_twh | TWh | Total crude oil supply |
| crude_oil_total_yoy_pct | Pct | YoY total crude oil supply |
| crude_oil_ytd_twh | TWh | Cumulative YTD crude oil supply |
| gas_import_twh | TWh | Gas imports in primary energy |
| gas_prod_twh | TWh | Domestic gas production in primary energy |
| gas_total_twh | TWh | Total gas supply |
| gas_total_yoy_pct | Pct | YoY total gas supply |
| gas_ytd_twh | TWh | Cumulative YTD gas supply |
| fossil_total_twh | TWh | Total fossil primary energy (coal + oil + gas) |
| fossil_total_yoy_pct | Pct | YoY total fossil primary energy |
| fossil_ytd_twh | TWh | Cumulative YTD fossil primary energy |
| fossil_ytd_yoy_pct | Pct | YoY cumulative fossil primary energy |
| nuclear_twh | TWh | Nuclear power generation (Ember) |
| hydro_twh | TWh | Hydro power generation (Ember) |
| wind_twh | TWh | Wind power generation (Ember) |
| solar_twh | TWh | Solar power generation (Ember) |
| bioenergy_twh | TWh | Bioenergy power generation (Ember) |
| clean_power_twh | TWh | Total clean power generation |
| clean_power_yoy_pct | Pct | YoY clean power generation |
| clean_power_ytd_twh | TWh | Cumulative YTD clean power generation |
| clean_power_ytd_yoy_pct | Pct | YoY cumulative clean power generation |
| total_twh | TWh | Total energy system (fossil + clean) |
| total_yoy_pct | Pct | YoY total energy system |
| total_ytd_twh | TWh | Cumulative YTD total energy system |
| total_ytd_yoy_pct | Pct | YoY cumulative total energy system |

**Jan-Feb convention:** Fossil periods follow NBS/GACC practice (202601 = Jan+Feb combined). The corresponding Ember periods 202601 and 202602 are automatically summed before merging with the fossil figures.

---

### `data/power/capacity_additions.csv`

Monthly capacity additions by source in gigawatts (GW). Source: CREA Monthly Energy & Air Quality Snapshot. Data appear with a two-month delay: for reporting month N, CREA provides data for N-2 (the `crea_period` column therefore differs from the RECH reporting month in `period`). Values are extracted manually from the CREA PDF and written to the CSV via the machine_data block.

| Column | Unit | Content |
|---|---|---|
| period | YYYYMM | Reporting month of the RECH document (NBS/GACC period) |
| crea_period | YYYYMM | Month for which CREA provides capacity data (in real-time workflow = period minus 2 months) |
| thermal_gw | GW | Newly installed thermal capacity in the month (coal + gas combined; CREA provides no breakdown) |
| thermal_yoy_pct | Pct | YoY thermal, month |
| nuclear_gw | GW | Newly installed nuclear capacity in the month |
| nuclear_yoy_pct | Pct | YoY nuclear, month (null if prior year = 0 GW) |
| hydro_gw | GW | Newly installed hydro capacity in the month |
| hydro_yoy_pct | Pct | YoY hydro, month |
| wind_gw | GW | Newly installed wind capacity in the month (onshore + offshore) |
| wind_yoy_pct | Pct | YoY wind, month |
| solar_gw | GW | Newly installed solar capacity in the month |
| solar_yoy_pct | Pct | YoY solar, month |
| total_gw | GW | Total additions in the month |
| total_yoy_pct | Pct | YoY total, month (derived; null if a component is missing) |
| thermal_ytd_gw | GW | Cumulative thermal additions Jan–crea_period |
| thermal_ytd_yoy_pct | Pct | YoY thermal, cumulative |
| nuclear_ytd_gw | GW | Cumulative nuclear additions |
| nuclear_ytd_yoy_pct | Pct | YoY nuclear, cumulative (null if prior year = 0 GW) |
| hydro_ytd_gw | GW | Cumulative hydro additions |
| hydro_ytd_yoy_pct | Pct | YoY hydro, cumulative |
| wind_ytd_gw | GW | Cumulative wind additions |
| wind_ytd_yoy_pct | Pct | YoY wind, cumulative |
| solar_ytd_gw | GW | Cumulative solar additions |
| solar_ytd_yoy_pct | Pct | YoY solar, cumulative |
| total_ytd_gw | GW | Total cumulative additions |
| total_ytd_yoy_pct | Pct | YoY total, cumulative (derived; null if a component is missing) |

**Source:** Centre for Research on Energy and Clean Air (CREA), Monthly Energy & Air Quality Snapshot, energyandcleanair.org

---

### `data/reference/wb_reference_prices.csv`

Monthly commodity reference prices from the [World Bank](https://www.worldbank.org/en/research/commodity-markets) Pink Sheet (CMO-Historical-Data-Monthly.xlsx). Updated automatically on the 15th of each month.

| Column | Unit | Description |
|---|---|---|
| period | YYYYMM | Reporting month |
| brent_usd_bbl | USD/bbl | Brent crude oil (spot) |
| dubai_usd_bbl | USD/bbl | Dubai crude oil (spot) |
| coal_au_usd_mt | USD/t | Australian thermal coal (Newcastle) |
| lng_japan_usd_mmbtu | USD/MMBtu | LNG Japan (JKM proxy) |

**Purpose in the dashboard:** Comparison with GACC import prices (VpU) in the Import Price Benchmarks section. For the comparison, GACC VpU is converted: crude oil USD/t ÷ 7.33 = USD/bbl; gas USD/t ÷ 52 = USD/MMBtu; coal direct.

**Data source:** [World Bank](https://www.worldbank.org/en/research/commodity-markets) Commodity Markets, Pink Sheet (monthly). The Excel URL changes each month; `fetch_wb_reference_prices.py` scrapes it at runtime from the WB page.

### `data/transport/fuel_savings.csv`

Auto-generated by `compute_fuel_savings.py` after each CPCA update. One row per month from November 2016 to December 2030. Rows with `type = historical` use actual CPCA sales data; rows with `type = projected` use S-curve market share projections applied to a trailing 12-month average sales volume.

| Column | Unit | Description |
|---|---|---|
| period | YYYY-MM | Reporting month |
| type | historical / projected | Whether the underlying sales data are actual or projected |
| crude_disp_mb_d | mb/d | Crude oil displaced by the active EV fleet in that month, in million barrels per day |
| crude_disp_mb_month | mb | Total crude oil displaced in that month, in million barrels |
| pe_saved_twh | TWh | Gross primary energy saved (fuel not burned), well-to-tank basis |
| pe_added_twh | TWh | Primary energy added by the grid to power the EV fleet |
| pe_net_twh | TWh | Net primary energy saved (pe_saved_twh − pe_added_twh) |

**Model scope:** Passenger cars only (CPCA retail sales). Two-wheelers, buses, and commercial vehicles are excluded.

**Key parameters:** Weibull k = 2.5, λ = 14.9 yr · ICE 11,000 km/yr at 6.2 L/100 km · BEV 12,500 km/yr at 16.0 kWh/100 km · PHEV utility factor 0.50 · EREV utility factor 0.65 · displacement coefficient 0.90 · WTT factor 1.24 (JEC WTW v5 COG1) · refinery yield 0.43 · grid factor 1.80 (2025) → 1.15 (2040).

**Calibration anchor:** IEA GEO 2026 — China passenger car EV fleet ≈ 1.0 mb/d for full-year 2025.

**Open calibration question (Q3 2026):** Carbon Brief / CREA reported charging volume +60% in Q2 2026, with the larger share attributable to more intensive use of existing vehicles rather than fleet growth alone — especially in the taxi segment. Given that the EV fleet grew by only ~33% in H1 2026, a 60% charging volume increase implies meaningfully higher annual mileage per vehicle. `KM_BEV = 12,500 km/yr` is calibrated to IEA GEO 2026 data that may not reflect this acceleration. The model likely understates fuel savings for 2026. To be revisited once an updated empirical mileage figure for China BEVs (2025/2026) becomes available.

### `data/storage/nea_battery_storage.csv`

Annual new-type battery storage (新型储能) installed capacity for China, sourced from the National Energy Administration (NEA). Updated manually once per year after the NEA year-end press conference (typically January). The H1 2026 row is sourced from the CNESA semi-annual industry report. The 2021 and 2023 year-end figures are derived by combining confirmed CNESA annual addition data with the adjacent confirmed year-end totals.

| Column | Unit | Description |
|---|---|---|
| period | YYYYMM | Reference period — December (202112, 202212 …) for year-end values; June (202606) for H1 |
| period_type | year-end / H1 | Whether the row represents a full-year or half-year cumulative |
| cumulative_gw | GW | Total cumulative installed power capacity (new-type storage only, excludes pumped hydro) |
| cumulative_gwh | GWh | Total cumulative installed energy capacity |
| duration_h | h | Average storage duration (cumulative_gwh ÷ cumulative_gw) |
| yoy_gw_pct | Pct | Year-on-year growth in cumulative GW |
| yoy_gwh_pct | Pct | Year-on-year growth in cumulative GWh |
| source_note | Text | Data provenance note |

---

## Automation: ComTrade

**GitHub Actions** runs on the 15th of each month (06:00 UTC) and calls `fetch_comtrade.py`. The script fetches all available 2025 months via the ComTrade API and upserts them into the four commodity CSVs. Existing 2025 rows are fully replaced (idempotent). Years 2020–2024 are not touched.

ComTrade typically publishes monthly data with a 2–3 month lag. The script exits cleanly if no 2025 data are available yet.

Required GitHub Secrets:
- `COMTRADE_PRIMARY_KEY` — [UN ComTrade](https://comtradeplus.un.org/) API Primary Key

---

## Automation: Ember

**GitHub Actions** checks from the 17th of each month daily (06:00 UTC) whether Ember has published new monthly data for China. If a new month is available, `ember_power.csv` and `ember_capacity.csv` are fully rewritten and the workflow self-deactivates. On the 1st of the following month (05:00 UTC), a separate workflow re-enables the update cycle.

**Why this mechanism?** Ember publishes new monthly data irregularly, typically with a ~7-week lag. A simple daily cron would run indefinitely. The self-deactivation mechanism ensures the workflow stays inactive after the first successful update until the next month.

**One-time history import** (already completed):

```bash
export EMBER_KEY=<key>
python scripts/fetch_ember_history.py
```

Alternatively via the `fetch_ember_history` workflow (workflow_dispatch). Writes both CSVs with the full history from 2015.

**Manual update test:**

```bash
export EMBER_KEY=<key>
python scripts/fetch_ember_monthly.py
```

The script outputs `new_data=true/false` and `new_period=YYYYMM`. In the GitHub Actions context, these values are set as step outputs and control the commit and self-deactivation.

Required GitHub Secrets:
- `EMBER_KEY` — Ember API Key

---

## Automation: World Bank Reference Prices

**GitHub Actions** runs on the 15th of each month (06:00 UTC) and calls `fetch_wb_reference_prices.py`. The script scrapes the current Pink Sheet URL from the [World Bank](https://www.worldbank.org/en/research/commodity-markets) Commodity Markets page, downloads the Excel file, parses the "Monthly Prices" sheet, and writes `data/reference/wb_reference_prices.csv` via upsert. Existing rows are replaced; older rows are preserved.

The update timing (15th) is intentionally ahead of the energy balance update (~20th), so current reference prices are available whenever a manual GACC push is made.

**One-time backfill** (already completed, from Jan 2026):

```bash
START_PERIOD=202601 python scripts/fetch_wb_reference_prices.py
```

Alternatively via the `fetch_wb_reference_prices_history` workflow (workflow_dispatch).

No additional GitHub Secrets required — the [World Bank](https://www.worldbank.org/en/research/commodity-markets) Pink Sheet is publicly accessible.

---

## Automation: fossil_supply.csv

`build_supply.yml` triggers automatically on any push that modifies `gacc_imports.csv` or `nbs_production.csv`. The script reads both CSVs from the repo, calculates the combined supply, and commits `data/combined/fossil_supply.csv`. Since the commit originates from `github-actions[bot]`, no further workflow is triggered.

The script can also be run locally:

```bash
python scripts/build_supply.py
```

---

## Manual workflow: GACC/NBS data

GACC and NBS do not provide a machine-readable API. Data are instead extracted from monthly energy balance research reports via a structured annotation process.

### Step 1: machine_data block in RECH file

Each energy balance RECH file in the vault contains an HTML comment block at the end with the structured data for that month:

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

Units: `qty_mt` and `*_mt` in million tonnes, `value_usd_bn` in USD billion, `gas_bcm` in BCM. `null` means missing data, not zero.

### Step 2: Extraction

After annotating, process a single RECH file:

```bash
# Prerequisite: Python venv with requirements.txt, gh CLI authenticated
python scripts/rech_to_github.py \
    --file "11_Recherche/Berichte/260820_RECH_China_Energiebilanz_Juli2026.md"
```

The script reads the machine_data block, calculates `*_usd_per_mt` values, upserts the row into `gacc_imports.csv` and `nbs_production.csv`, and pushes.

To process all annotated RECH files at once (backfill after a new annotation round):

```bash
python scripts/backfill_to_github.py
```

`backfill_to_github.py` runs locally only — it requires access to the vault at `/Users/hado/Documents/Arbeit/China-Archiv`.

### Step 3: value_per_mt calculation

`rech_to_github.py` and `backfill_to_github.py` calculate the price per tonne automatically:

```
value_per_mt_usd = round(value_usd_bn * 1000 / qty_mt, 1)
```

If either input is `null`, `value_per_mt_usd` is also left empty.

---

## Manual workflow: CREA capacity additions

CREA publishes the monthly snapshot as a PDF at energyandcleanair.org. Capacity addition data are extracted from the PDF as part of the `/energiebilanz` skill (step 9b) and written to `capacity_additions.csv` via the machine_data block.

### Data delay

CREA delivers data with approximately a two-month delay. For an energy balance report covering reporting month N, the current CREA snapshot contains capacity data for month N-2. The `crea_period` column in the CSV documents which month the capacity data actually refer to.

### Step 1: Obtain CREA snapshot

The current snapshot is retrieved via Gmail search or directly from energyandcleanair.org. The PDF is loaded into a NotebookLM notebook as a source and queried via chat (automated via `/energiebilanz` steps 1, 3, and 9b).

### Step 2: Fill machine_data block

The values extracted from the notebook are entered into the `capacity_additions` block at the end of the RECH file:

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
  ...
-->
```

`null` for `nuclear_yoy_pct` and `nuclear_ytd_yoy_pct` when the prior-year value was 0 GW (division by zero). `total_yoy_pct` and `total_ytd_yoy_pct` are back-calculated from the components and entered manually when all components are known.

### Step 3: Extraction and push

Identical to the GACC/NBS workflow:

```bash
python scripts/rech_to_github.py \
    --file "11_Recherche/Berichte/260902_RECH_China_Energiebilanz_August2026.md"
```

The script reads the `capacity_additions` block and upserts the row into `data/power/capacity_additions.csv`.

---

## One-time history import (2020–2024)

`fetch_history.py` loads the complete ComTrade history 2020–2024 and rewrites the four commodity CSVs. This script was run once via the `fetch_history` workflow and does not need to be repeated unless ComTrade revises historical data retroactively.

```bash
export COMTRADE_PRIMARY_KEY=<key>
python scripts/fetch_history.py
```

---

## Dependencies

```
comtradeapicall   — UN ComTrade Python wrapper
pandas            — Data processing
requests          — HTTP
urllib3           — HTTP transport
pyyaml            — YAML parsing of machine_data blocks
openpyxl          — Excel parsing (World Bank Pink Sheet)
scipy             — Nonlinear least squares for S-curve fitting (build_car_projection.py)
```

Local: `pip install -r requirements.txt` in a venv. On macOS with an externally managed Python, a venv under `/tmp/` or `~/.venv/` is recommended.

---

## GACC country-of-origin data (gacc_*.csv)

GACC publishes monthly granular import data by country of origin. The four country-of-origin CSVs (`gacc_coal.csv`, `gacc_crude_oil.csv`, `gacc_lng.csv`, `gacc_pipeline_gas.csv`) fill the ComTrade gap from January 2025 onwards: ComTrade delivers monthly data with an 18–20 month lag and has not yet published 2025 data. GACC data are available with approximately a 6-week lag.

**Schema** (identical for all four files):

| Column | Unit | Description |
|---|---|---|
| period | YYYYMM | Reporting month |
| partner | Text | Country of origin (ComTrade naming convention) |
| value_usd_bn | USD bn | Import value |

**Differences from ComTrade:** GACC does not include volume data (`qty_mt`) in its public CSV downloads. The `qty_mt` and `value_per_mt_usd` columns are therefore absent from the GACC country-of-origin CSVs. Volume charts in the dashboard are rendered only for the ComTrade period (2020–2024).

**HS codes and categorisation:**

| Category | GACC HS codes | ComTrade HS code |
|---|---|---|
| coal | 270111 + 270112 + 270119 | 2701 |
| crude_oil | 270900 | 2709 |
| lng | 271111 | 271111 |
| pipeline_gas | 271121 | 271121 |

**Manual update:** GACC does not provide a machine-readable API. New CSVs are downloaded from GACC (GBK encoding), transformed, and pushed to the repo. On push, `build_combined.yml` automatically triggers a rebuild of the `combined_*.csv` files.

---

## Automation: combined_*.csv

`build_combined.yml` triggers on any push that modifies `data/fuel-imports/comtrade_*.csv` or `data/fuel-imports/gacc_*.csv`. The script `scripts/build_combined.py` merges both sources with ComTrade taking priority:

- For any `(period, partner)` entry present in ComTrade, ComTrade values are used.
- GACC fills all periods for which ComTrade has no data yet (currently from January 2025).
- When ComTrade delivers 2025 data, the next rebuild automatically overwrites the GACC rows for those periods.

Run locally:

```bash
python scripts/build_combined.py
```

**Output schema** (`data/combined/combined_*.csv`):

| Column | Unit | Description |
|---|---|---|
| period | YYYYMM | Reporting month |
| partner | Text | Country of origin |
| value_usd_bn | USD bn | Import value |
| qty_mt | Mt | Import volume (ComTrade rows only; GACC: empty) |
| value_per_mt_usd | USD/t | Price per tonne (ComTrade rows only) |
| source | comtrade / gacc | Row origin |

---

## Automation: CPCA car sales

**GitHub Actions** checks for new CPCA data daily from the 8th of each month (07:00 UTC) and stops as soon as new data is found. The workflow pulls the retail and wholesale CSVs from [@leRaffl's public gallery](https://leraffl.github.io/LeRaffl-Gallery/), compares the latest period in the remote file against the local copy, appends any new rows, and immediately rebuilds the S-curve projection.

The commit only happens if at least one new row was appended. The workflow does not run from the 1st through the 7th because CPCA typically does not release monthly data before the 8th.

**Manual run:**

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -q
.venv/bin/python scripts/fetch_china_car_sales.py
.venv/bin/python scripts/build_car_projection.py
```

No additional GitHub Secrets required — all source data is publicly accessible.

---

## Open items

- **2026 ComTrade**: Once UN ComTrade makes 2026 data available, update `YEAR` in `fetch_comtrade.py` and trigger the workflow manually.
- **Pipeline Gas explainer**: The "Pipeline Gas Imports" section needs an explanatory text block covering why pipeline gas imports appear nominally higher before 2021 (Central Asia Line D stall, Turkmenistan supply problems, accelerating Chinese shale gas growth, Power of Siberia ramp-up from 2019). SEO-relevant.
- **Canonical URL**: `<link rel="canonical">` in `docs/index.html` still points at the GitHub subdomain instead of china-energy-monitor.com; one-line fix.

---

## Import Price Benchmarks — concept and methodology

`gacc_imports.csv` contains the implied import price (Value per Unit, VpU) for coal, crude oil, and gas derived from GACC customs data. This price is a weighted average of all actual physical transactions in the month — not a spot or paper price, but what China actually paid. Comparing it with market benchmarks allows approximate assessments of whether China bought above or below market prices.

**Methodological caveat:** All benchmark prices are spot or assessment prices. China's imports are largely based on long-term contracts (often oil-indexed) or politically negotiated prices (Central Asia, Russia). The comparison is structurally uneven but analytically meaningful — trend breaks in particular (China buying oil well below Brent after 2022 = Russia discount effect) are visible.

**Iran note:** Iranian crude oil does not appear in GACC data (recorded as Malaysia, UAE, Oman). A structural data gap.

### Units and conversions

| Fuel | GACC VpU | Dashboard unit | Conversion |
|---|---|---|---|
| Coal | USD/t | USD/t | Direct |
| Crude oil | USD/t | USD/bbl | ÷ 7.33 (IEA standard factor) |
| Gas | USD/t | USD/MMBtu | ÷ 52 (LNG rule of thumb; GIIGNL: 43–49 MMBtu/t) |

### Benchmark sources

| Fuel | Benchmark | Source |
|---|---|---|
| Crude oil | Brent (USD/bbl) + Dubai (USD/bbl) | World Bank Pink Sheet |
| Gas | LNG Japan (USD/MMBtu) — JKM proxy | World Bank Pink Sheet |
| Coal | Coal Australian — Newcastle (USD/t) | World Bank Pink Sheet |
---

## Article Cards

Four *China Business Spotlight* articles are displayed in the dashboard below the Monthly Summary section. Each card links to the article with referral parameter `?r=25gtpf`.

Images are stored locally in `docs/` as square JPEGs (1:1 aspect ratio). The dashboard renders them at 1:1 via `aspect-ratio: 1/1` in the CSS.

| # | Title | URL | Image |
|---|---|---|---|
| 1 | China's 3-Layer Grid Replaces Baseload | https://chinabusinessspotlight.substack.com/p/chinas-3-layer-grid-replaces-baseload?r=25gtpf | cem-card-1.jpg |
| 2 | Coal vs. AI: China's Strategy Against the Dunkelflaute | https://chinabusinessspotlight.substack.com/p/coal-vs-ai-chinas-strategy-against?r=25gtpf | cem-card-2.jpg |
| 3 | China Grid Bottleneck Slows Solar and Wind Expansion | https://chinabusinessspotlight.substack.com/p/china-grid-bottleneck-slows-solar?r=25gtpf | cem-card-3.jpg |
| 4 | China Out of Gas: The Hormuz Shock in Traffic Data | https://chinabusinessspotlight.substack.com/p/china-out-of-gas-the-hormuz-shock?r=25gtpf | cem-card-4.jpg |

To update a card: replace the corresponding `docs/cem-card-N.jpg` file and update the URL and title in the `article-grid` block in `docs/index.html`.
