"""Command line interface.

Examples::

    shipemis entec  examples/turyol_entec.csv  -o out.csv
    shipemis trozzi examples/turyol_trozzi.csv -o out.csv --hotelling-fraction 0.2
    shipemis entec  examples/turyol_entec.csv  --thesis local      # Excel behaviour
    shipemis check  data/raw/local_entec_turyol.xlsx --kind entec-local
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

from . import entec, io, trozzi

KINDS = {
    "trozzi-local": (io.read_trozzi_local_workbook, trozzi.replicate_thesis_local),
    "trozzi-transit": (io.read_trozzi_transit_workbook, trozzi.replicate_thesis_transit),
    "entec-local": (io.read_entec_workbook, lambda d: entec.replicate_thesis(d, "local")),
    "entec-transit": (io.read_entec_workbook, lambda d: entec.replicate_thesis(d, "transit")),
}


def _summary(df: pd.DataFrame) -> pd.Series:
    return df[[c for c in df.columns if c.endswith("_t") and c.count("_") == 1]].sum()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="shipemis", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("entec", "trozzi"):
        p = sub.add_parser(name, help=f"{name} methodology on a CSV/Excel input table")
        p.add_argument("input")
        p.add_argument("-o", "--output", help="write per-ship results to CSV")
        p.add_argument("--thesis", choices=["local", "transit"],
                       help="reproduce the original Excel workbook instead of the corrected method")
        if name == "trozzi":
            p.add_argument("--hotelling-fraction", default="by_type",
                           help='"by_type" (default) or a number such as 0.2')
            p.add_argument("--sulfur-pct", type=float, default=None)
            p.add_argument("--aux-sfoc", type=float, default=220.0, help="g/kWh")
            p.add_argument("--aux-ef", choices=["table", "polynomial"], default="table")
        else:
            p.add_argument("--main-in-hotelling", action="store_true")

    c = sub.add_parser("check", help="compare this package with a thesis workbook")
    c.add_argument("workbook")
    c.add_argument("--kind", choices=sorted(KINDS), required=True)

    a = ap.parse_args(argv)

    if a.cmd == "check":
        reader, fn = KINDS[a.kind]
        inp, exp = reader(a.workbook)
        got = fn(inp)
        cols = [x for x in exp.columns if x in got]
        rel = ((got[cols] - exp[cols]).abs() / exp[cols].abs().clip(lower=1e-12)).max()
        print(f"{len(inp)} rows compared; max relative difference per column:")
        print(rel.to_string())
        return 0 if (rel < 1e-9).all() else 1

    df = io.read_table(a.input)
    if a.cmd == "entec":
        res = (entec.replicate_thesis(df, a.thesis) if a.thesis
               else entec.estimate(df, include_main_in_hotelling=a.main_in_hotelling))
    else:
        if a.thesis == "local":
            res = trozzi.replicate_thesis_local(df)
        elif a.thesis == "transit":
            res = trozzi.replicate_thesis_transit(df)
        else:
            hf = a.hotelling_fraction
            hf = hf if hf == "by_type" else float(hf)
            res = trozzi.estimate(df, hotelling_fraction=hf, sulfur_pct=a.sulfur_pct,
                                  aux_sfoc_g_kwh=a.aux_sfoc, aux_ef_method=a.aux_ef)
    if a.output:
        res.to_csv(a.output, index=False)
    print(_summary(res).round(4).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
