# shipemis: activity-based ship emission inventories in Python

`shipemis` estimates exhaust emissions (NOx, SOx, CO, CO₂, VOC, PM) and fuel use
of ships with two established bottom-up methodologies:

* **Trozzi & Vaccaro (MEET RF98)**: fuel-based. Full-power consumption as a
  function of gross tonnage, operating-mode fractions, and emission factors
  by engine type (kg/t fuel). Auxiliary generators are included.
* **Entec UK Limited (2002/2005)**: power-based. Installed main and auxiliary
  power, load factors, time in mode, and ship-type emission factors (g/kWh).

The package is a Python port of the Excel/VBA workflow used in my PhD thesis
*Analysis of Ship-Borne Air Emissions in the Istanbul Strait and Presenting Its
Effects* (Istanbul University, 2019). It provides two layers:

| Function | Purpose |
|---|---|
| `entec.estimate`, `trozzi.estimate` | Methodology with consistent units (recommended) |
| `entec.replicate_thesis`, `trozzi.replicate_thesis_local/_transit` | Exact re-implementation of the original workbooks, for reproducibility and auditing |

The replication layer reproduces all 38 original workbooks (12 monthly transit
files per method and 14 local-traffic files, ~87,000 ship rows) with zero
difference. Building it exposed several errors in the spreadsheets;
see [Known issues](#known-issues-in-the-original-workbooks).

## Installation

```bash
pip install -e ".[dev]"     # numpy, pandas, openpyxl (+ xlrd, pytest)
pytest                      # 18 tests
```

## Usage

```python
import pandas as pd
from shipemis import entec, trozzi

ships = pd.DataFrame([
    dict(vessel="A", ship_type="Bulk Dry", distance_nm=17, main_kw=4397, aux_kw=5880),
    dict(vessel="B", ship_type="Container", distance_nm=17, main_kw=14871, aux_kw=5880,
         maneuvering_h=1.5, hotelling_h=12),
])
entec.estimate(ships)[["vessel", "fuel_t", "CO2_t", "NOx_t", "SOx_t"]]

transit = pd.DataFrame([dict(ship_type="SOLID BULK", gt=26062, distance_nm=17,
                             cruise_engine="SLOW SPEED DIESEL ENGINES")])
trozzi.estimate(transit)
```

Command line:

```bash
shipemis entec  examples/turyol_entec.csv  -o results.csv
shipemis trozzi examples/turyol_trozzi.csv -o results.csv --hotelling-fraction 0.2
shipemis entec  examples/turyol_entec.csv  --thesis local    # original Excel behaviour
shipemis check  data/raw/transit_entec_august.xlsx --kind entec-transit
```

Every result table contains per-mode columns (`CO2_cruise_t`, `NOx_hotelling_t`, …),
per-ship totals (`CO2_t`, …) and fuel (`fuel_t`). Entec results also include
engine energy (`energy_cruise_kwh`, …).

### Input columns

**Entec**: `ship_type` (Entec type, e.g. `Passenger`, `Bulk Dry`), `distance_nm`,
`main_kw`, `aux_kw`, optionally `maneuvering_h`, `hotelling_h`, `speed_kn`, and
load factors `{cruise|maneuvering|hotelling}_{main|aux}_lf_pct` (defaults 80/30,
20/40, 20/50 %).

**Trozzi**: `ship_type` (MEET class, e.g. `PASSENGER`, `SOLID BULK`), `gt`;
activity as `cruise_days` or `distance_nm`, plus `maneuvering_days`,
`hotelling_days`; engine types `{mode}_engine` (or a single `engine`);
optionally generator `aux_kw` and `aux_load_pct`.

### Assumptions in the corrected Trozzi method

* Hotelling fuel fraction by ship class (MEET table 20: passenger 0.32, tanker
  0.20, other 0.12); `hotelling_fraction=0.2` reproduces the single default.
* Generator fuel = rated kW × load × running hours × SFOC (default 220 g/kWh).
  Running hours default to the time spent in all modes.
* Generator NOx/CO/VOC factors are interpolated from MEET table 8. The MEET
  table 14 NOx polynomial becomes negative between ~55 and 180 kW, so it is
  optional (`aux_ef_method="polynomial"`).

## Known issues in the original workbooks

Found while building the replication layer. Full details, with cell references
and impact figures, are in [`docs/AUDIT_TR.md`](docs/AUDIT_TR.md) (Turkish).

* Entec: load factors entered in % but not divided by 100 (cruise ×100,
  manoeuvring and hotelling ×10). Transit cruise formulas also carry constant
  multipliers (NOx ×5, CO₂ ×6, VOC ×5, PM ×3, SOx ×3); local VOC is multiplied by 4.
* Entec: total rows sum only the first 41 ships (`SUM(…3:…43)`).
* Trozzi: General Cargo consumption intercept entered as 98.197 instead of 9.8197.
* Trozzi transit: daily consumption divided by 10 instead of 24 when converting
  to hours (×2.4).
* Trozzi local: inconsistent divisors per pollutant (/10, /2), CO₂ factor stored
  as 3.2 in the mode sheets but 3200 for generators, a sign error in the
  generator NOx regression, and an auto-filled CO₂ factor (3200…3231).

### 2015 Istanbul Strait transit traffic (43,544 passages)

| t/year | CO₂ | NOx | SOx | PM |
|---|---:|---:|---:|---:|
| Trozzi & Vaccaro, corrected | 134,102 | 2,493 | 562 | 69 |
| Entec UK, corrected | 157,711 | 3,497 | 2,661 | 335 |
| Trozzi & Vaccaro, thesis | 937,017 | 18,324 | 5,294 | 692 |
| Entec UK, thesis | 1,086,585 | 19,987 | 9,150 | 1,143 |

The corrected methods agree within 18 % for CO₂ and match the order of magnitude
of an earlier independent estimate (Kesgin & Vardar, 2001: 173,362 t CO₂ for
1998). Monthly values are in [`results/`](results/). The thesis Entec total
turned out to be the sum of the first 41 ships of each monthly file.

### 2015 Istanbul local ferry traffic (221 ships, 7 operators, cruising only)

| t/year | CO₂ | NOx | SOx | PM |
|---|---:|---:|---:|---:|
| Entec UK, corrected (recommended) | 178,310 | 3,049 | 2,988 | 206 |
| Trozzi & Vaccaro, corrected | 391,011 | 7,260 | 1,688 | 197 |
| Entec UK, thesis | 321,269 | 5,582 | 4,711 | 348 |
| Trozzi & Vaccaro, thesis | 315,310 | 4,101 | 3,566 | 330 |

The ship-by-ship input table (`data/local_fleet_2015.csv`) is built from the
operators' inventory sheets and the thesis ship lists by
`scripts/build_local_fleet.py`, with the source of every value recorded.
Manoeuvring and berth times are not available, so these are lower bounds.
Trozzi's tonnage-based fuel regression overstates consumption for small ferries,
so the power-based Entec result is preferred for local traffic.

## Batch processing

```bash
python scripts/batch_inventory.py data/raw/transit_entec  --kind entec-transit  -o results/entec.csv
python scripts/batch_inventory.py data/raw/transit_trozzi --kind trozzi-transit -o results/trozzi.csv
python scripts/batch_inventory.py data/raw/local          --kind local          -o results/local.csv
python scripts/build_local_fleet.py data/raw/envanter -o data/local_fleet_2015.csv
python scripts/local_inventory.py  data/local_fleet_2015.csv -o results
```

## Data

`examples/` holds the Turyol fleet inputs used in the thesis. `tests/fixtures/`
contains small anonymised subsets of the August 2015 transit data (flag state
and ship type only), with the values stored in the original workbooks. The full
transit data from the Directorate General of Coastal Safety (KEGM) and the
original workbooks are not distributed. Place them in `data/raw/` to run the
full replication tests.

## References

* Trozzi, C., Vaccaro, R. (1998). *Methodologies for estimating air pollutant
  emissions from ships*. MEET Deliverable RF98, Techne.
* Entec UK Limited (2002). *Quantification of emissions from ships associated
  with ship movements between ports in the European Community*. Report for the
  European Commission.
* Entec UK Limited (2005). *Service Contract on Ship Emissions: Assignment,
  Abatement and Market-based Instruments. Task 1*. Report for the European
  Commission.
* Tokuşlu, A. (2019). PhD thesis, Istanbul University, Institute of Marine
  Sciences and Management.

## License

MIT
