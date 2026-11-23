"""Entec UK Limited (2002/2005) power-based ship emission methodology.

Thesis equations (2.5)-(2.7), with load factors as fractions::

    E_cruise      = D/V * (ME*LF_me + AE*LF_ae) * EF_cruise         [g]
    E_maneuvering = T_m * (ME*LF_me + AE*LF_ae) * EF_maneuvering    [g]
    E_hotelling   = T_h *  AE*LF_ae             * EF_hotelling      [g]

    D distance [nm], V service speed [kn], ME/AE installed power [kW],
    T time [h], EF [g/kWh]. Results are reported in tonnes (/1e6).
"""
from __future__ import annotations

import pandas as pd

from . import factors as F
from .factors import POLLUTANTS_ENTEC as POLL, norm

MODES = ("cruise", "maneuvering", "hotelling")


def _lookup(series, table, what):
    keys = series.map(norm)
    missing = sorted(set(keys[~keys.isin(table.keys())]))
    if missing:
        raise KeyError(f"Unknown {what}: {missing}")
    return keys.map(table)


def _lf(df, mode, engine):
    default = float(F.ENTEC_LOAD_PCT[mode][engine])
    col = f"{mode}_{engine}_lf_pct"
    if col in df:
        return df[col].astype(float).fillna(default)
    return pd.Series(default, index=df.index)


def _hours(df, mode):
    if mode == "cruise":
        v = _lookup(df["ship_type"], F.ENTEC_SPEED_KN, "Entec ship type (speed)")
        if "speed_kn" in df:
            v = df["speed_kn"].astype(float).where(df["speed_kn"].notna(), v)
        return df["distance_nm"].astype(float) / v
    col = f"{mode}_h"
    return df[col].astype(float).fillna(0.0) if col in df else pd.Series(0.0, index=df.index)


def energy_kwh(df: pd.DataFrame, include_main_in_hotelling: bool = False) -> dict:
    """Engine output per mode [kWh]."""
    me = df["main_kw"].astype(float)
    ae = df["aux_kw"].astype(float)
    out = {}
    for m in MODES:
        h = _hours(df, m)
        p_me = me * _lf(df, m, "main") / 100.0
        p_ae = ae * _lf(df, m, "aux") / 100.0
        if m == "hotelling" and not include_main_in_hotelling:
            p_me = 0.0
        out[m] = h * (p_me + p_ae)
    return out


def estimate(df: pd.DataFrame, *, include_main_in_hotelling: bool = False) -> pd.DataFrame:
    """Estimate emissions [t] and fuel [t] with the Entec methodology.

    Required columns: ``ship_type`` (Entec type, e.g. ``Passenger``),
    ``distance_nm``, ``main_kw``, ``aux_kw``. Optional: ``maneuvering_h``,
    ``hotelling_h``, ``speed_kn`` (overrides the type average) and load factors
    ``{mode}_{main|aux}_lf_pct`` (defaults: thesis table 20).
    """
    kwh = energy_kwh(df, include_main_in_hotelling)
    out = pd.DataFrame(index=df.index)
    for c in ("vessel", "ship_type"):
        if c in df:
            out[c] = df[c]
    tot = {p: 0.0 for p in (*POLL, "fuel")}
    for m in MODES:
        ef = _lookup(df["ship_type"], F.ENTEC_EF[m], "Entec ship type")
        out[f"energy_{m}_kwh"] = kwh[m]
        for p, key in [(p, p) for p in POLL] + [("fuel", "SFC")]:
            e = kwh[m] * ef.map(lambda d: d[key]) / 1e6
            out[f"{p}_{m}_t"] = e
            tot[p] = tot[p] + e
    out["fuel_t"] = tot["fuel"]
    for p in POLL:
        out[f"{p}_t"] = tot[p]
    return out


# ---------------------------------------------------------------------------
# Exact replication of the thesis Excel workbooks
# ---------------------------------------------------------------------------

#: Constant multipliers found in the workbook formulas (not part of the method).
THESIS_MULTIPLIERS = {
    "local": {"cruise": {"NOx": 1, "CO2": 1, "VOC": 4, "PM": 1, "SOx": 1},
              "maneuvering": {"NOx": 1, "CO2": 1, "VOC": 4, "PM": 1, "SOx": 1},
              "hotelling": {"NOx": 1, "CO2": 1, "VOC": 4, "PM": 1, "SOx": 1}},
    "transit": {"cruise": {"NOx": 5, "CO2": 6, "VOC": 5, "PM": 3, "SOx": 3},
                "maneuvering": {"NOx": 1, "CO2": 1, "VOC": 1, "PM": 1, "SOx": 1},
                "hotelling": {"NOx": 1, "CO2": 1, "VOC": 1, "PM": 1, "SOx": 1}},
}


def replicate_thesis(df: pd.DataFrame, variant: str = "local") -> pd.DataFrame:
    """Re-implementation of the 'Entec UK Limited' workbooks.

    Load factors are used as percentages without dividing by 100 and the
    divisors are 1e6 (cruise) and 1e7 (maneuvering/hotelling), exactly as in
    the spreadsheets. ``variant`` is "local" or "transit" (they differ in the
    constant multipliers, see :data:`THESIS_MULTIPLIERS`).
    """
    k = THESIS_MULTIPLIERS[variant]
    me, ae = df["main_kw"].astype(float), df["aux_kw"].astype(float)
    D = df["distance_nm"].astype(float)
    G = df["maneuvering_h"].astype(float)
    H = df["hotelling_h"].astype(float)
    v = _lookup(df["ship_type"], F.ENTEC_SPEED_KN, "Entec ship type (speed)")
    lf = {(m, e): _lf(df, m, e) for m in MODES for e in ("main", "aux")}
    ef = {m: _lookup(df["ship_type"], F.ENTEC_EF[m], "Entec ship type") for m in MODES}

    out = pd.DataFrame(index=df.index)
    if "vessel" in df:
        out["vessel"] = df["vessel"]
    tot = {p: 0.0 for p in POLL}
    for p in POLL:
        f = {m: ef[m].map(lambda d: d[p]) for m in MODES}
        cr = (D * (me * lf["cruise", "main"] + ae * lf["cruise", "aux"]) * k["cruise"][p]
              * f["cruise"] / 1000 / v / 1000)
        mv = (G * (me * lf["maneuvering", "main"] + ae * lf["maneuvering", "aux"]) / 1000
              * f["maneuvering"] / 10000) * k["maneuvering"][p]
        ht = (H * ae * lf["hotelling", "aux"] / 1000 * f["hotelling"] / 10000) * k["hotelling"][p]
        out[f"{p}_cruise_t"], out[f"{p}_maneuvering_t"], out[f"{p}_hotelling_t"] = cr, mv, ht
        out[f"{p}_t"] = cr + mv + ht
    return out
