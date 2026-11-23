"""Reference tables for the two activity-based ship emission methodologies.

Units are stated explicitly for every table. Values are taken from the sources
cited in the thesis (Tokuşlu, 2019):

* Trozzi & Vaccaro (1998, MEET RF98; updated values as reported in the thesis
  tables 8-10, Trozzi & Vaccaro 2006). Emission factors are **kg pollutant per
  tonne of fuel**; fuel consumption regressions are **tonnes fuel per day** at
  full power.
* Entec UK Limited (2002/2005), 2015 values. Emission factors are **g pollutant
  per kWh** of engine output (the thesis labels them "kg/ton yakıt"; the CO2/SFC
  ratio of ~3.18 confirms g/kWh).
"""
from __future__ import annotations

import numpy as np

POLLUTANTS_TROZZI = ("NOx", "CO", "CO2", "VOC", "PM", "SOx")
POLLUTANTS_ENTEC = ("NOx", "CO2", "VOC", "PM", "SOx")


def norm(name: str) -> str:
    """Normalise a category label (case, surrounding spaces)."""
    return " ".join(str(name).strip().upper().split())


# ---------------------------------------------------------------------------
# Trozzi & Vaccaro
# ---------------------------------------------------------------------------

#: Full-power daily fuel consumption C(GT) = a + b * GT  [t fuel / day]
TROZZI_CONSUMPTION = {
    "SOLID BULK": (20.186, 0.00049),
    "LIQUID BULK": (14.685, 0.00079),
    "GENERAL CARGO": (9.8197, 0.00143),
    "CONTAINER": (8.0552, 0.00235),
    "PASSENGER/RO-RO/CARGO": (12.834, 0.00156),
    "PASSENGER": (16.904, 0.00198),
    "HIGH SPEED FERRY": (39.483, 0.00972),
    "INLAND CARGO": (9.8197, 0.00143),
    "SAIL SHIPS": (0.42682, 0.00100),
    "TUGS": (5.6511, 0.01048),
    "FISHING": (1.9387, 0.00448),
    "OTHER SHIPS": (9.7126, 0.00091),
    "ALL SHIPS": (16.263, 0.001),
}

#: Average cruising speed by ship class [knots] (thesis table 13)
TROZZI_SPEED_KN = {
    "SOLID BULK": 14.32,
    "LIQUID BULK": 14.20,
    "GENERAL CARGO": 14.29,
    "CONTAINER": 19.09,
    "PASSENGER/RO-RO/CARGO": 16.49,
    "PASSENGER": 17.81,
    "HIGH SPEED FERRY": 36.64,
    "INLAND CARGO": 14.29,
    "SAIL SHIPS": 9.63,
    "TUGS": 12.91,
    "FISHING": 11.96,
    "OTHER SHIPS": 13.45,
    "ALL SHIPS": 14.77,
}

#: Fraction of full-power fuel consumption per operating mode (MEET table 20)
TROZZI_MODE_FRACTION = {"cruise": 0.80, "maneuvering": 0.40, "hotelling": 0.20}

#: Ship-class specific hotelling fractions (MEET table 20)
TROZZI_HOTELLING_FRACTION_BY_TYPE = {
    "PASSENGER": 0.32,
    "PASSENGER/RO-RO/CARGO": 0.32,
    "HIGH SPEED FERRY": 0.32,
    "LIQUID BULK": 0.20,
}
TROZZI_HOTELLING_FRACTION_OTHER = 0.12

_E = ("NOx", "CO", "CO2", "VOC", "PM", "SOx")


def _tbl(rows):
    return {norm(k): dict(zip(_E, v)) for k, v in rows.items()}


#: Emission factors [kg / t fuel] by engine type and mode (thesis tables 8-10).
#: SOx values correspond to 20*S with S = 0.5 % (10) or 2.7 % (54).
TROZZI_EF = {
    "cruise": _tbl({
        "STEAM TURBINES - BFO ENGINES": (6.98, 0.431, 3200, 0.085, 2.5, 54),
        "STEAM TURBINES - MDO ENGINES": (6.25, 0.6, 3200, 0.5, 2.08, 10),
        "HIGH SPEED DIESEL ENGINES": (60, 2.8, 3200, 1.0, 0.52, 10),
        "MEDIUM SPEED DIESEL ENGINES": (57, 7.4, 3200, 2.4, 1.2, 10),
        "SLOW SPEED DIESEL ENGINES": (87, 7.4, 3200, 2.4, 7.6, 54),
        "GAS TURBINES": (18, 0.8, 3200, 0.3, 0.01, 10),
        "PLEASURE CRAFT-INBOARD ENG.-DIESEL": (48, 20, 3200, 26, 0, 4),
        "PLEASURE CRAFT-INBOARD ENG.-GASOLINE": (21.2, 201, 3000, 13.9, 0, 0.1),
        "PLEASURE CRAFT-OUTBOARD ENG.-GASOLINE": (1.07, 540, 3000, 176, 0, 0.1),
    }),
    "maneuvering": _tbl({
        "STEAM TURBINES - BFO ENGINES": (6.11, 0.19, 3200, 0.85, 2.5, 54),
        "STEAM TURBINES - MDO ENGINES": (5.47, 0.27, 3200, 5.0, 2.08, 10),
        "HIGH SPEED DIESEL ENGINES": (54, 10.6, 3200, 1.5, 0.52, 10),
        "MEDIUM SPEED DIESEL ENGINES": (51, 28, 3200, 3.6, 1.2, 10),
        "SLOW SPEED DIESEL ENGINES": (78, 28, 3200, 3.6, 7.6, 54),
        "GAS TURBINES": (18, 0.8, 3200, 0.3, 0.01, 10),
        "PLEASURE CRAFT-INBOARD ENG.-DIESEL": (48, 20, 3200, 26, 0, 4),
        "PLEASURE CRAFT-INBOARD ENG.-GASOLINE": (21.2, 201, 3000, 13.9, 0, 0.1),
        "PLEASURE CRAFT-OUTBOARD ENG.-GASOLINE": (1.07, 540, 3000, 176, 0, 0.1),
    }),
    "hotelling": _tbl({
        "STEAM TURBINES - BFO ENGINES": (4.55, 0.0, 3200, 0.4, 1.25, 54),
        "STEAM TURBINES - MDO ENGINES": (3.11, 0.6, 3200, 0.5, 2.11, 10),
        "HIGH SPEED DIESEL ENGINES": (28, 120, 3200, 28.9, 1.5, 10),
        "MEDIUM SPEED DIESEL ENGINES": (23, 99, 3200, 23.1, 1.2, 10),
        "SLOW SPEED DIESEL ENGINES": (35, 99, 3200, 23.1, 1.2, 54),
        "GAS TURBINES": (6, 7, 3200, 1.9, 1.1, 10),
        "DIESEL AUXILIARY ENGINES - MDO": (63, 4, 3200, 1.9, 1.1, 10),
    }),
}

#: Auxiliary diesel generator emission factors [kg / t fuel] (MEET table 8):
#: rows = rated electrical output [kW], cols = load [% rated output].
TROZZI_GEN_P = np.array([20.0, 40.0, 200.0, 500.0])
TROZZI_GEN_L = np.array([0.0, 25.0, 50.0, 75.0])
TROZZI_GEN_TABLE = {
    "NOx": np.array([[60.89, 62.30, 66.98, 69.44],
                     [29.98, 30.68, 31.73, 32.67],
                     [19.91, 19.79, 19.67, 19.20],
                     [21.43, 31.15, 41.10, 51.05]]),
    "CO": np.array([[21.08, 11.18, 7.49, 4.00],
                    [21.43, 12.53, 9.48, 8.99],
                    [18.85, 13.70, 8.75, 3.75],
                    [8.20, 7.49, 6.74, 6.14]]),
    "VOC": np.array([[36.89, 28.57, 20.26, 11.94],
                     [81.97, 51.87, 40.05, 32.44],
                     [18.97, 4.70, 2.49, 2.46],
                     [29.27, 15.22, 11.48, 8.29]]),
}
TROZZI_GEN_CONST = {"CO2": 3200.0, "PM": 1.1}


def trozzi_generator_ef_polynomial(p_kw, load_pct):
    """MEET table 14 regressions [kg/t fuel]. NOTE: the NOx polynomial turns
    negative for roughly 55-180 kW, so the tabulated values are preferred."""
    P = np.asarray(p_kw, float)
    L = np.asarray(load_pct, float)
    return {
        "NOx": 108.58 - 2.47 * P + 0.0136 * P**2 - 0.000018 * P**3 + 0.000684 * P * L,
        "CO": 20.72 - 0.218 * L - 0.0231 * P + 0.000345 * P * L,
        "VOC": 3.27 + 2.164 * P - 0.0144 * P**2 + 0.0000203 * P**3 - 0.719 * L + 0.00476 * L**2,
    }


def trozzi_generator_ef_table(p_kw, load_pct):
    """Bilinear interpolation in MEET table 8 [kg/t fuel] (inputs clipped to
    the tabulated range 20-500 kW, 0-75 % load)."""
    P = np.clip(np.atleast_1d(np.asarray(p_kw, float)), TROZZI_GEN_P[0], TROZZI_GEN_P[-1])
    L = np.clip(np.atleast_1d(np.asarray(load_pct, float)), TROZZI_GEN_L[0], TROZZI_GEN_L[-1])
    P, L = np.broadcast_arrays(P, L)
    i = np.clip(np.searchsorted(TROZZI_GEN_P, P, side="right") - 1, 0, len(TROZZI_GEN_P) - 2)
    j = np.clip(np.searchsorted(TROZZI_GEN_L, L, side="right") - 1, 0, len(TROZZI_GEN_L) - 2)
    tp = (P - TROZZI_GEN_P[i]) / (TROZZI_GEN_P[i + 1] - TROZZI_GEN_P[i])
    tl = (L - TROZZI_GEN_L[j]) / (TROZZI_GEN_L[j + 1] - TROZZI_GEN_L[j])
    out = {}
    for k, T in TROZZI_GEN_TABLE.items():
        out[k] = ((1 - tp) * (1 - tl) * T[i, j] + tp * (1 - tl) * T[i + 1, j]
                  + (1 - tp) * tl * T[i, j + 1] + tp * tl * T[i + 1, j + 1])
    return out


# ---------------------------------------------------------------------------
# Entec UK Limited (2015 factors)
# ---------------------------------------------------------------------------
_P5 = ("NOx", "SOx", "CO2", "VOC", "PM", "SFC")


def _etbl(rows):
    return {norm(k): dict(zip(_P5, v)) for k, v in rows.items()}


#: Emission factors [g / kWh] and specific fuel consumption SFC [g fuel / kWh]
#: by ship type and mode. Column "VOC" is the Entec HC factor.
ENTEC_EF = {
    "cruise": _etbl({
        "Liquefied Gas": (8, 12.4, 816, 0.31, 1.03, 257),
        "Chemical": (14.6, 11, 650, 0.55, 1.34, 204),
        "Oil": (13.3, 11.7, 690, 0.5, 1.43, 217),
        "Other Liquids": (14.6, 11, 649, 0.55, 1.3, 204),
        "Bulk Dry": (15.9, 10.6, 627, 0.59, 1.61, 197),
        "Bulk Dry / Oil": (15, 10.1, 646, 0.56, 1.5, 203),
        "General Cargo": (14.5, 10.9, 649, 0.54, 1.28, 204),
        "Passenger/General Cargo": (14, 11.2, 658, 0.53, 1.15, 207),
        "Container": (15.5, 10.8, 635, 0.57, 1.56, 200),
        "Refrigerated Cargo": (15.3, 10.8, 636, 0.57, 1.47, 200),
        "Ro-Ro Cargo": (13.7, 11.1, 655, 0.52, 1.17, 206),
        "Passenger/Ro-Ro Cargo": (12, 9.9, 688, 0.42, 0.73, 212),
        "Passenger": (11.9, 11.8, 697, 0.46, 0.81, 219),
        "Other Dry Cargo": (10.1, 12.8, 755, 0.39, 0.96, 238),
        "Fish Catching": (12.6, 11.4, 678, 0.47, 0.83, 213),
        "Other Fishing": (11.9, 12.2, 721, 0.45, 1.31, 227),
        "Research": (12.7, 11.5, 675, 0.48, 0.85, 212),
        "Towing / Pushing": (12.3, 10.8, 674, 0.42, 0.8, 212),
        "Dredging": (12.7, 11.4, 675, 0.49, 0.84, 212),
    }),
    "maneuvering": _etbl({
        "Liquefied Gas": (8.9, 12.5, 818, 0.67, 1.55, 257),
        "Chemical": (11.9, 12.2, 715, 1.04, 1.6, 225),
        "Oil": (11.2, 12.7, 745, 1.1, 1.82, 235),
        "Other Liquids": (12, 12.2, 715, 0.92, 1.44, 225),
        "Bulk Dry": (12.6, 11.9, 698, 1.3, 1.84, 220),
        "Bulk Dry / Oil": (12.1, 11.5, 712, 1.2, 1.74, 224),
        "General Cargo": (11.9, 12.1, 715, 1.03, 1.59, 225),
        "Passenger/General Cargo": (11.7, 12.3, 720, 0.92, 1.48, 226),
        "Container": (12.3, 12, 705, 1.19, 1.73, 222),
        "Refrigerated Cargo": (12.2, 12, 707, 1.06, 1.58, 223),
        "Ro-Ro Cargo": (11.5, 12.2, 719, 1.06, 1.68, 226),
        "Passenger/Ro-Ro Cargo": (10.6, 11.4, 741, 0.9, 1.57, 233),
        "Passenger": (10.6, 12.6, 747, 0.97, 1.71, 235),
        "Other Dry Cargo": (9.6, 13.4, 788, 0.86, 1.75, 248),
        "Fish Catching": (11.2, 12.3, 730, 0.85, 1.48, 229),
        "Other Fishing": (10.7, 12.9, 760, 0.92, 1.66, 239),
        "Research": (10.9, 12.5, 734, 1.06, 1.8, 231),
        "Towing / Pushing": (10.5, 12, 735, 1.01, 1.87, 231),
        "Dredging": (10.7, 12.5, 736, 1.14, 1.9, 231),
    }),
    "hotelling": _etbl({
        "Liquefied Gas": (8.8, 6.9, 795, 0.6, 1.2, 250),
        "Chemical": (11.6, 5.7, 698, 1, 1.2, 220),
        "Oil": (11, 7.8, 730, 1.1, 1.5, 230),
        "Other Liquids": (11.5, 4.6, 695, 0.9, 1.1, 219),
        "Bulk Dry": (11.5, 1.6, 690, 0.5, 0.5, 217),
        "Bulk Dry / Oil": (11.4, 1.5, 692, 0.5, 0.5, 218),
        "General Cargo": (11.4, 1.2, 691, 0.5, 0.4, 217),
        "Passenger/General Cargo": (11.3, 1, 691, 0.5, 0.4, 217),
        "Container": (11.4, 1.4, 690, 0.5, 0.5, 217),
        "Refrigerated Cargo": (11.4, 1.1, 690, 0.5, 0.4, 217),
        "Ro-Ro Cargo": (11.3, 1.3, 692, 0.5, 0.5, 218),
        "Passenger/Ro-Ro Cargo": (11.2, 1.3, 695, 0.5, 0.4, 219),
        "Passenger": (11.2, 1.5, 696, 0.5, 0.5, 219),
        "Other Dry Cargo": (11.1, 1.6, 702, 0.5, 0.5, 221),
        "Fish Catching": (11.3, 1, 692, 0.4, 0.4, 218),
        "Other Fishing": (11.2, 1.4, 697, 0.5, 0.4, 219),
        "Research": (11.2, 1.6, 695, 0.5, 0.5, 219),
        "Towing / Pushing": (11.1, 2, 697, 0.5, 0.6, 219),
        "Dredging": (11.2, 2, 696, 0.5, 0.6, 219),
    }),
}

#: Average service speed by ship type [knots] (Entec, thesis table 22)
ENTEC_SPEED_KN = {norm(k): v for k, v in {
    "Liquefied Gas": 16.9, "Chemical": 13.7, "Oil": 14, "Other Liquids": 13,
    "Bulk Dry": 14.3, "Bulk Dry / Oil": 13.5, "General Cargo": 12.3,
    "Passenger/General Cargo": 14.6, "Container": 19.3, "Refrigerated Cargo": 17,
    "Ro-Ro Cargo": 15.4, "Passenger/Ro-Ro Cargo": 15.3, "Passenger": 20.8,
    "Other Dry Cargo": 13.6, "Fish Catching": 13.9, "Other Fishing": 13.3,
    "Research": 13.6, "Towing / Pushing": 12.9, "Dredging": 11.5,
}.items()}

#: Default engine load factors [% MCR] (thesis table 20)
ENTEC_LOAD_PCT = {
    "cruise": {"main": 80, "aux": 30},
    "maneuvering": {"main": 20, "aux": 40},
    "hotelling": {"main": 20, "aux": 50},
}
