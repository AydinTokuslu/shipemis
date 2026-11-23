"""The thesis-replication functions must reproduce the Excel workbooks exactly."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shipemis import entec, io, trozzi

FIX = Path(__file__).parent / "fixtures"
EX = Path(__file__).parents[1] / "examples"
RAW = Path(__file__).parents[1] / "data" / "raw"

CASES = [
    ("trozzi local", EX / "turyol_trozzi.csv", FIX / "turyol_trozzi_excel_results.csv",
     trozzi.replicate_thesis_local),
    ("entec local", EX / "turyol_entec.csv", FIX / "turyol_entec_excel_results.csv",
     lambda d: entec.replicate_thesis(d, "local")),
    ("entec transit", FIX / "transit_entec_sample.csv", FIX / "transit_entec_sample_excel_results.csv",
     lambda d: entec.replicate_thesis(d, "transit")),
    ("trozzi transit", FIX / "transit_trozzi_sample.csv", FIX / "transit_trozzi_sample_excel_results.csv",
     trozzi.replicate_thesis_transit),
]


def _assert_same(got, exp):
    cols = [c for c in exp.columns if c in got]
    assert cols
    np.testing.assert_allclose(got[cols].to_numpy(float), exp[cols].to_numpy(float), rtol=1e-10, atol=1e-12)


@pytest.mark.parametrize("name,inp,exp,fn", CASES, ids=[c[0] for c in CASES])
def test_fixtures_match_excel(name, inp, exp, fn):
    _assert_same(fn(pd.read_csv(inp)), pd.read_csv(exp))


RAW_CASES = [
    ("local_trozzi_turyol.xlsx", io.read_trozzi_local_workbook, trozzi.replicate_thesis_local),
    ("local_entec_turyol.xlsx", io.read_entec_workbook, lambda d: entec.replicate_thesis(d, "local")),
    ("transit_entec_august.xlsx", io.read_entec_workbook, lambda d: entec.replicate_thesis(d, "transit")),
    ("transit_trozzi_august.xls", io.read_trozzi_transit_workbook, trozzi.replicate_thesis_transit),
]


@pytest.mark.parametrize("fname,reader,fn", RAW_CASES, ids=[c[0] for c in RAW_CASES])
def test_full_workbooks_match_excel(fname, reader, fn):
    path = RAW / fname
    if not path.exists():
        pytest.skip(f"original workbook {fname} not available (data/raw is not distributed)")
    inp, exp = reader(path)
    _assert_same(fn(inp), exp)
