"""Run both methodologies over a folder of thesis workbooks.

    python scripts/batch_inventory.py data/raw/transit_entec  --kind entec-transit  -o results/x.csv
    python scripts/batch_inventory.py data/raw/transit_trozzi --kind trozzi-transit -o results/y.csv
    python scripts/batch_inventory.py data/raw/local          --kind local          -o results/z.csv

For every workbook the script (1) checks that the replication layer reproduces
the stored Excel values, and (2) reports the Excel totals next to the totals of
the unit-consistent methods.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from shipemis import entec, io, trozzi


def _maxrel(got, exp):
    cols = [c for c in exp.columns if c in got]
    return float(((got[cols] - exp[cols]).abs() / exp[cols].abs().clip(lower=1e-12)).max().max())


def process(path: Path, kind: str) -> dict:
    row = {"file": path.name}
    if kind == "entec-transit" or (kind == "local" and "DETAYLI" not in path.name.upper()
                                   and path.suffix == ".xlsx" and _is_entec(path)):
        inp, exp = io.read_entec_workbook(path)
        variant = "transit" if kind == "entec-transit" else "local"
        rep = entec.replicate_thesis(inp, variant)
        cor = entec.estimate(inp)
        row["method"] = "entec"
        polls = ["NOx", "CO2", "VOC", "PM", "SOx"]
        row["excel_first41_CO2_t"] = exp["CO2_t"].iloc[:41].sum()
    elif kind == "trozzi-transit":
        inp, exp = io.read_trozzi_transit_workbook(path)
        rep = trozzi.replicate_thesis_transit(inp)
        cor = trozzi.estimate(inp.rename(columns={"engine": "cruise_engine"}))
        row["method"] = "trozzi"
        polls = ["NOx", "CO", "CO2", "VOC", "PM", "SOx"]
    else:
        inp, exp = io.read_trozzi_local_workbook(path)
        rep = trozzi.replicate_thesis_local(inp)
        cor = trozzi.estimate(inp)
        row["method"] = "trozzi"
        polls = ["NOx", "CO", "CO2", "VOC", "PM", "SOx"]
    row["ships"] = len(inp)
    row["replication_max_rel_diff"] = _maxrel(rep, exp)
    for p in polls:
        row[f"{p}_excel_t"] = exp[f"{p}_t"].sum()
        row[f"{p}_corrected_t"] = cor[f"{p}_t"].sum()
    row["fuel_corrected_t"] = cor["fuel_t"].sum()
    return row


def _is_entec(path: Path) -> bool:
    import openpyxl
    return "CRUISING EMISSION FACTORS" in openpyxl.load_workbook(path, read_only=True).sheetnames and \
        "JENERATÖR EMİSYON FAKTÖRÜ" not in openpyxl.load_workbook(path, read_only=True).sheetnames


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--kind", choices=["entec-transit", "trozzi-transit", "local"], required=True)
    ap.add_argument("-o", "--output")
    a = ap.parse_args()
    files = sorted(p for p in Path(a.folder).iterdir() if p.suffix.lower() in {".xlsx", ".xls"})
    df = pd.DataFrame([process(p, a.kind) for p in files])
    pd.set_option("display.width", 200)
    print(df.to_string(index=False))
    if a.output:
        df.to_csv(a.output, index=False)


if __name__ == "__main__":
    main()
