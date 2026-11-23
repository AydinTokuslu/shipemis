"""Trozzi & Vaccaro (MEET) activity-based ship emission methodology.

Detailed methodology (MEET RF98, ch. 3 and 8)::

    E_i = sum_m  C(GT) * p_m * t_m * F_i,l,m          [kg]

    C(GT)  full-power fuel consumption of the ship class   [t fuel / day]
    p_m    fraction of full-power consumption in mode m    [-]
    t_m    days spent in mode m                            [day]
    F      emission factor of engine type l in mode m      [kg / t fuel]

Auxiliary diesel generators are added as a separate source whose fuel use is
derived from rated output, load and specific fuel oil consumption.

Two entry points are provided:

* :func:`estimate` – the methodology with consistent units ("corrected").
* :func:`replicate_thesis_local` / :func:`replicate_thesis_transit` – an exact
  re-implementation of the original Excel workbooks used in the thesis, kept for
  reproducibility and auditing. See ``docs/AUDIT_TR.md``.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import factors as F
from .factors import POLLUTANTS_TROZZI as POLL, norm

MODES = ("hotelling", "maneuvering", "cruise")


def _lookup(series: pd.Series, table: dict, what: str) -> pd.Series:
    keys = series.map(norm)
    missing = sorted(set(keys[~keys.isin(table.keys())]))
    if missing:
        raise KeyError(f"Unknown {what}: {missing}. Known: {sorted(table)}")
    return keys.map(table)


def full_power_consumption(ship_type: pd.Series, gt: pd.Series, table=None) -> pd.Series:
    """C(GT) in t fuel/day."""
    table = table or F.TROZZI_CONSUMPTION
    ab = _lookup(ship_type, table, "Trozzi ship class")
    return ab.map(lambda t: t[0]) + ab.map(lambda t: t[1]) * gt.astype(float)


def _hotelling_fraction(ship_type: pd.Series, how) -> pd.Series:
    if how == "by_type":
        return ship_type.map(norm).map(F.TROZZI_HOTELLING_FRACTION_BY_TYPE).fillna(
            F.TROZZI_HOTELLING_FRACTION_OTHER)
    return pd.Series(float(how if how is not None else F.TROZZI_MODE_FRACTION["hotelling"]),
                     index=ship_type.index)


def _col(df, name, default=0.0):
    if name in df:
        return df[name].astype(float).fillna(default)
    return pd.Series(default, index=df.index, dtype=float)


def estimate(
    df: pd.DataFrame,
    *,
    hotelling_fraction="by_type",
    sulfur_pct: float | None = None,
    aux_sfoc_g_kwh: float = 220.0,
    aux_ef_method: str = "table",
    aux_sulfur_pct: float = 0.5,
    aux_hours: pd.Series | float | None = None,
) -> pd.DataFrame:
    """Estimate emissions [t] with the Trozzi & Vaccaro detailed methodology.

    Required columns: ``ship_type`` (MEET class, e.g. ``PASSENGER``), ``gt``.
    Activity (days): ``hotelling_days``, ``maneuvering_days``, ``cruise_days``;
    if ``cruise_days`` is absent, ``distance_nm`` is converted with the class
    speed. Engine types: ``hotelling_engine``, ``maneuvering_engine``,
    ``cruise_engine`` (a single ``engine`` column is used as a fallback).
    Optional generator inputs: ``aux_kw`` (rated output) and ``aux_load_pct``.

    Parameters
    ----------
    hotelling_fraction : "by_type" (MEET table 20) or a number (e.g. 0.20).
    sulfur_pct : if given, SOx = 20 * S kg/t replaces the tabulated SOx factors.
    aux_sfoc_g_kwh : generator specific fuel consumption (assumption, g/kWh).
    aux_ef_method : "table" (interpolate MEET table 8) or "polynomial" (table 14).
    aux_sulfur_pct : fuel sulphur of the generators, SOx = 20 * S.
    aux_hours : generator running hours; default = all hours in the three modes.
    """
    df = df.copy()
    out = pd.DataFrame(index=df.index)
    for c in ("vessel", "ship_type"):
        if c in df:
            out[c] = df[c]

    C = full_power_consumption(df["ship_type"], df["gt"])
    days = {
        "hotelling": _col(df, "hotelling_days"),
        "maneuvering": _col(df, "maneuvering_days"),
    }
    if "cruise_days" in df:
        days["cruise"] = df["cruise_days"].astype(float)
    elif "distance_nm" in df:
        v = _lookup(df["ship_type"], F.TROZZI_SPEED_KN, "Trozzi ship class (speed)")
        if "speed_kn" in df:
            v = df["speed_kn"].astype(float).where(df["speed_kn"].notna(), v)
        days["cruise"] = df["distance_nm"].astype(float) / v / 24.0
    else:
        days["cruise"] = pd.Series(0.0, index=df.index)

    frac = {
        "cruise": F.TROZZI_MODE_FRACTION["cruise"],
        "maneuvering": F.TROZZI_MODE_FRACTION["maneuvering"],
        "hotelling": _hotelling_fraction(df["ship_type"], hotelling_fraction),
    }

    total = {p: pd.Series(0.0, index=df.index) for p in POLL}
    total_fuel = pd.Series(0.0, index=df.index)
    for m in MODES:
        eng_col = f"{m}_engine" if f"{m}_engine" in df else "engine"
        fuel = C * frac[m] * days[m]                                   # t fuel
        if (fuel > 0).any():
            ef = _lookup(df.loc[fuel > 0, eng_col], F.TROZZI_EF[m], f"{m} engine type")
            ef = ef.reindex(df.index)
        out[f"fuel_{m}_t"] = fuel
        total_fuel += fuel
        for p in POLL:
            if (fuel > 0).any():
                f_ip = ef.map(lambda d: d[p] if isinstance(d, dict) else 0.0).astype(float)
            else:
                f_ip = pd.Series(0.0, index=df.index)
            if p == "SOx" and sulfur_pct is not None:
                f_ip = pd.Series(20.0 * sulfur_pct, index=df.index)
            e = fuel * f_ip / 1000.0                                   # kg -> t
            out[f"{p}_{m}_t"] = e
            total[p] += e

    if "aux_kw" in df:
        P = df["aux_kw"].astype(float)
        L = _col(df, "aux_load_pct", 75.0)
        hours = aux_hours if aux_hours is not None else 24.0 * sum(days.values())
        fuel = P * L / 100.0 * hours * aux_sfoc_g_kwh / 1e6            # t fuel
        if aux_ef_method == "table":
            gen = F.trozzi_generator_ef_table(P, L)
        else:
            gen = F.trozzi_generator_ef_polynomial(P, L)
        gen = {k: pd.Series(np.asarray(v, float), index=df.index) for k, v in gen.items()}
        gen["CO2"] = F.TROZZI_GEN_CONST["CO2"]
        gen["PM"] = F.TROZZI_GEN_CONST["PM"]
        gen["SOx"] = 20.0 * aux_sulfur_pct
        out["fuel_aux_t"] = fuel
        total_fuel += fuel
        for p in POLL:
            e = fuel * gen[p] / 1000.0
            out[f"{p}_aux_t"] = e
            total[p] += e

    out["fuel_t"] = total_fuel
    for p in POLL:
        out[f"{p}_t"] = total[p]
    return out


# ---------------------------------------------------------------------------
# Exact replication of the thesis Excel workbooks
# ---------------------------------------------------------------------------

#: The FORMUL sheet of the thesis workbooks. Differs from the source in one cell:
#: GENERAL CARGO intercept was entered as 98.197 instead of 9.8197.
THESIS_CONSUMPTION = {**F.TROZZI_CONSUMPTION, "GENERAL CARGO": (98.197, 0.00143)}


def _thesis_mode_ef(mode):
    """Mode EF sheets of the local workbook: CO2 stored as 3.2 (t/t, not kg/t)."""
    return {k: {**v, "CO2": v["CO2"] / 1000.0} for k, v in F.TROZZI_EF[mode].items()}


def replicate_thesis_local(df: pd.DataFrame) -> pd.DataFrame:
    """Re-implementation of 'Yerel Trafik - Trozzi & Vaccaro' workbook.

    Input columns as in the workbook: ``ship_type``, ``gt``, ``hotelling_days``,
    ``hotelling_engine``, ``maneuvering_days``, ``maneuvering_engine``,
    ``cruise_days``, ``cruise_engine``, ``aux_kw`` (P), ``aux_load_pct`` (L) and
    optionally ``co2_gen_ef`` (column O; 3200 by default).
    """
    P = df["aux_kw"].astype(float)
    L = df["aux_load_pct"].astype(float)
    gen = {  # columns M..R. NOTE: NOx uses +2.47*P (source: -2.47*P)
        "NOx": 108.58 + 2.47 * P + 0.0136 * P**2 - 0.000018 * P**3 + 0.000684 * P * L,
        "CO": 20.72 - 0.218 * L - 0.0231 * P + 0.000345 * P * L,
        "CO2": _col(df, "co2_gen_ef", 3200.0),
        "VOC": 3.27 + 2.164 * P - 0.0144 * P**2 + 0.0000203 * P**3 - 0.719 * L + 0.00476 * L**2,
        "PM": pd.Series(1.1, index=df.index),
        "SOx": pd.Series(54.0, index=df.index),
    }
    S = full_power_consumption(df["ship_type"], df["gt"], THESIS_CONSUMPTION) / 10.0
    ef = {m: _lookup(df[f"{m}_engine"], _thesis_mode_ef(m), f"{m} engine type") for m in MODES}
    E, G, I = (df[c].astype(float) for c in ("hotelling_days", "maneuvering_days", "cruise_days"))
    scale = {"NOx": S / 10, "CO": S / 2, "CO2": S, "VOC": S / 10, "PM": S, "SOx": S / 2}

    out = pd.DataFrame(index=df.index)
    if "vessel" in df:
        out["vessel"] = df["vessel"]
    for p in POLL:
        out[f"gen_ef_{p}"] = gen[p]
    out["fuel_t"] = S
    for p in POLL:
        h = ef["hotelling"].map(lambda d: d[p])
        mv = ef["maneuvering"].map(lambda d: d[p])
        cr = ef["cruise"].map(lambda d: d[p])
        inner = (0.2 * E * h + gen[p]) / 1000 + 0.4 * G * mv / 1000 + 0.8 * I * cr / 1000
        out[f"{p}_t"] = scale[p] * inner
    return out


def replicate_thesis_transit(df: pd.DataFrame) -> pd.DataFrame:
    """Re-implementation of 'Transit Trafik - Trozzi & Vaccaro' workbook
    (reverse-engineered from its stored values; macros were not preserved).

    ``E = C(GT)/10 * 0.8 * distance_nm / speed_kn * EF / 1000`` for cruising only.
    Input columns: ``ship_type``, ``gt``, ``distance_nm``, ``engine``.
    """
    S = full_power_consumption(df["ship_type"], df["gt"], THESIS_CONSUMPTION) / 10.0
    v = _lookup(df["ship_type"], F.TROZZI_SPEED_KN, "Trozzi ship class (speed)")
    ef = _lookup(df["engine"], F.TROZZI_EF["cruise"], "engine type")
    out = pd.DataFrame(index=df.index)
    if "vessel" in df:
        out["vessel"] = df["vessel"]
    out["fuel_t"] = S
    k = S * 0.8 * df["distance_nm"].astype(float) / v
    for p in POLL:
        out[f"{p}_t"] = k * ef.map(lambda d: d[p]) / 1000.0
    return out
