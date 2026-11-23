"""Corrected 2015 local-traffic inventory from data/local_fleet_2015.csv.

Only the cruising phase is computed: the firms' data contain annual distance but
no manoeuvring or berth times, so the result is a lower bound.

    python scripts/local_inventory.py data/local_fleet_2015.csv -o results/
"""
import argparse
from pathlib import Path

import pandas as pd

from shipemis import entec, trozzi


def run(fleet: pd.DataFrame):
    e_in = fleet.rename(columns={"entec_type": "ship_type"})
    e = entec.estimate(e_in)
    t_in = fleet.rename(columns={"trozzi_type": "ship_type", "engine": "cruise_engine"}).drop(columns="entec_type")
    t_in["aux_load_pct"] = 75.0                          # MEET: generators at 75 % load
    hours = fleet["distance_nm"] / fleet["speed_kn"]     # generators run while cruising
    t = trozzi.estimate(t_in, aux_hours=hours)
    out = fleet[["firm", "vessel", "gt", "distance_nm", "speed_kn", "main_kw", "aux_kw"]].copy()
    out["cruise_h"] = hours
    for p in ["fuel", "NOx", "CO2", "VOC", "PM", "SOx"]:
        out[f"entec_{p}_t"] = e[f"{p}_t"]
    for p in ["fuel", "NOx", "CO", "CO2", "VOC", "PM", "SOx"]:
        out[f"trozzi_{p}_t"] = t[f"{p}_t"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fleet")
    ap.add_argument("-o", "--outdir", default="results")
    a = ap.parse_args()
    ships = run(pd.read_csv(a.fleet))
    firms = ships.drop(columns=["vessel"]).groupby("firm").sum(numeric_only=True)
    firms.insert(0, "ships", ships.groupby("firm").size())
    firms.loc["TOTAL"] = firms.sum()
    Path(a.outdir).mkdir(exist_ok=True)
    ships.round(4).to_csv(Path(a.outdir) / "local_2015_ships_corrected.csv", index=False)
    firms.round(2).to_csv(Path(a.outdir) / "local_2015_firms_corrected.csv")
    pd.set_option("display.width", 220)
    print(firms[["ships", "distance_nm", "cruise_h", "entec_fuel_t", "entec_CO2_t", "entec_NOx_t",
                 "trozzi_fuel_t", "trozzi_CO2_t", "trozzi_NOx_t"]].round(0).to_string())


if __name__ == "__main__":
    main()
