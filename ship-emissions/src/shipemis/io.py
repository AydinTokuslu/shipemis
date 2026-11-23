"""Readers for the original thesis workbooks and for plain CSV input."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

TROZZI_LOCAL_COLS = {
    1: "vessel", 2: "ship_type", 3: "gt", 4: "hotelling_days", 5: "hotelling_engine",
    6: "maneuvering_days", 7: "maneuvering_engine", 8: "cruise_days", 9: "cruise_engine",
    10: "aux_kw", 11: "aux_load_pct", 14: "co2_gen_ef",
}
TROZZI_LOCAL_OUT = {18: "fuel_t", 19: "NOx_t", 20: "CO_t", 21: "CO2_t", 22: "VOC_t",
                    23: "PM_t", 24: "SOx_t"}

ENTEC_COLS = {
    1: "vessel", 2: "ship_type", 3: "distance_nm", 4: "main_kw", 5: "aux_kw",
    6: "maneuvering_h", 7: "hotelling_h",
    8: "cruise_main_lf_pct", 9: "maneuvering_main_lf_pct", 10: "hotelling_main_lf_pct",
    11: "cruise_aux_lf_pct", 12: "maneuvering_aux_lf_pct", 13: "hotelling_aux_lf_pct",
}
ENTEC_OUT = {29: "NOx_t", 30: "CO2_t", 31: "VOC_t", 32: "PM_t", 33: "SOx_t"}

TROZZI_TRANSIT_COLS = {0: "vessel", 1: "month", 2: "ship_type", 3: "gt",
                       4: "distance_nm", 5: "engine"}
TROZZI_TRANSIT_OUT = {6: "fuel_t", 7: "NOx_t", 8: "CO_t", 9: "CO2_t", 10: "VOC_t",
                      11: "PM_t", 12: "SOx_t"}


def _read_sheet(path, sheet, header_rows, inputs, outputs):
    raw = pd.read_excel(path, sheet_name=sheet, header=None, skiprows=header_rows)
    # keep data rows only: ship type present and column D numeric (drops the
    # total row and the template rows with #REF! formulas below the data)
    raw = raw[raw.iloc[:, 2].notna() & pd.to_numeric(raw.iloc[:, 3], errors="coerce").notna()]
    inp = raw[list(inputs)].rename(columns=inputs).reset_index(drop=True)
    exp = raw[list(outputs)].rename(columns=outputs).apply(pd.to_numeric).reset_index(drop=True)
    return inp, exp


def read_trozzi_local_workbook(path: str | Path):
    """Return (inputs, excel_results) from a 'Yerel Trafik - Trozzi' workbook."""
    return _read_sheet(path, "VERİ GİRİŞİ", 2, TROZZI_LOCAL_COLS, TROZZI_LOCAL_OUT)


def read_entec_workbook(path: str | Path):
    """Return (inputs, excel_results) from an 'Entec UK Limited' workbook."""
    return _read_sheet(path, "VERİ GİRİŞİ", 2, ENTEC_COLS, ENTEC_OUT)


def read_trozzi_transit_workbook(path: str | Path):
    """Return (inputs, excel_results) from the 'Transit Trafik - Trozzi' .xls."""
    return _read_sheet(path, "DataPage", 1, TROZZI_TRANSIT_COLS, TROZZI_TRANSIT_OUT)


def read_table(path: str | Path) -> pd.DataFrame:
    """Read a CSV or Excel file that already uses the package column names."""
    p = Path(path)
    if p.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    return pd.read_csv(p)
