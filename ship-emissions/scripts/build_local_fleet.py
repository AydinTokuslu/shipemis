"""Build a ship-by-ship input table for the 2015 Istanbul local (ferry) fleet.

Sources, in order of precedence:
1. The firms' emission-inventory sheets ("... EMİSYON ENVANTERİ.xlsx"): annual
   distance [nm], gross tonnage, engine type class, service speed and, where
   given, main/auxiliary engine power.
2. Thesis appendices EK 1-6 (ship lists): main/auxiliary engine power and speed
   where the inventory sheet has none (encoded below).
3. Manufacturer ratings for İDO engine models that appear in neither source
   (``ENGINE_MODEL_KW``), or the rating of a sister ship listed in EK 2.
4. Documented defaults (``DEFAULTS``) for the remaining gaps.

Every row carries ``main_kw_source``, ``aux_kw_source`` and ``speed_source``.

    python scripts/build_local_fleet.py data/raw/envanter -o data/local_fleet_2015.csv
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

DEFAULTS = {"aux_kw": 530.0, "speed_kn": 14.0, "main_kw": 1500.0}

# --- EK 1-6 (thesis) -------------------------------------------------------
EK_SPEED = {
    "TURYOL": [15, 15, 13, 14, 15, 17, 15, 14, 15, 14, 12, 14.5, 14, 14, 14, 13, 15, 8, 15, 13,
               9, 15, 14, 15, 13, 15, 14, 14, 14, 14, 14, 15, 14, 14, 13, 13, 13, 8, 14, 9,
               14, 14, 10, 14, 14, 14, 14, 12, 14, 12, 14, 10],
    "MAVI MARMARA": [15, 15, 15, 15, 15, 14, 14, 14, 14, 15, 14, 14, 12, 15, 14, 12, 14, 12, 12,
                     12, 12, 12, 12, 12, 9, 12, 12, 12, 10],
}
EK_SEHIR_HATLARI_MAIN = {"HASKÖY": 958, "KASIMPAŞA": 958, "SÜTLÜCE": 958,
                         "M/S AHMET H.YILDIRIM": 1696, "M/S EMİN KUL": 3000, "M/S FAHRİ S.KORUTÜRK": 3000}
EK_SEHIR_HATLARI_SPEED = {"HASKÖY": 10, "KASIMPAŞA": 10, "SÜTLÜCE": 10}
EK_IDO = {  # name -> (main kW, aux kW, speed kn)
    **{n: (2440, 1120, s) for n, s in [("MEHMET REIS – 11", 30.9), ("MURAT REIS – 7", 30.9),
       ("UMUR BEY", 32), ("TEMEL REIS II", 32), ("HIZIR REIS III", 32), ("SOKULLU MEHMET PAŞA", 32),
       ("BARBAROS HAYRETTIN PAŞA", 32), ("PIYALE PAŞA", 34), ("SINAN PAŞA", 34)]},
    **{n: (3044, 530, 11) for n in ["ESKIHISAR-1", "HALIDERE", "HEREKE-III", "KARAMÜRSEL",
       "KAPTAN ŞEFIK GÖĞEN", "TOPÇULAR-I", "GAYRETTEPE", "GALATASARAY", "OKMEYDANI", "TOPKAPI",
       "ZEYTINBURNU", "BOZCAADA"]},
}
EK_FLEET_DEFAULT = {"DENTUR": (1500, 530), "BOGAZICI": (1500, 530)}   # 750 kW x 2, 265 kW x 2

# --- Manufacturer ratings (kW per engine) for İDO models not in EK 2 ---------
ENGINE_MODEL_KW = {
    "MTU 20V 8000 M70R": (7200, "MTU fast-ferry reference list (Osman Gazi I: 4 x 7200 kW)"),
    "MTU 20V 1163 TB 73L": (6500, "MTU fast-ferry reference list (20V 1163: 6500 kW per engine)"),
    "CAT 3516B -HD": (1920, "Cat 3516B marine propulsion data sheet, 1920 bkW"),
    "MTU 12V 396TE 74L": (1470, "MTU 12V 396 TE74L, 1470 kW @ 2000 rpm"),
    "MTU 12V 396 TE74": (1470, "assumed equal to 12V 396 TE74L"),
    "CAT C32 ACERT": (1081, "Cat C32 marine propulsion (IMO II), 1081 bkW"),
}
SISTER_MODELS = {"MTU 16V 396 TE74": 2440, "MTU 16V 396 TE74L": 2440, "MTU 12V 183 TE72": 2440,
                 "ABC 8 MDXC 750-100K": 3044, "SULZER 8 AL 20/24": 3044}

FIRMS = {"EH_R_HATLARI": "SEHIR HATLARI", "MAV__MARMARA": "MAVI MARMARA", "TURYOL": "TURYOL",
         "_DO_DEN": "IDO", "BEYDEN": "BEYDEN", "DENTUR": "DENTUR", "BO_AZ": "BOGAZICI"}


def _up(s):
    return " ".join(str(s).replace("\xa0", " ").replace("İ", "I").upper().split()) if s is not None else ""


def _kw(text):
    """'2X750' -> 1500, '552+1200' -> 1752, '760*MAN' -> 760, '4X' -> None."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None
    t = str(text).upper().replace(" ", "")
    m = re.fullmatch(r"(\d+)X(\d+(?:[.,]\d+)?)", t)
    if m:
        return float(m[1]) * float(m[2].replace(",", "."))
    if "+" in t:
        return sum(float(x) for x in re.findall(r"\d+", t))
    m = re.match(r"(\d+)\*", t)
    if m:
        return float(m[1])
    return float(t) if re.fullmatch(r"\d+(\.\d+)?", t) else None


def _speed(text):
    m = re.search(r"(\d+(?:\.\d+)?)", str(text or ""))
    return float(m[1]) if m else None


def _model_kw(model):
    m = re.match(r"\s*(\d+)\s*x\s*(.+)", str(model), re.I)
    if not m:
        return None, None
    n, name = int(m[1]), " ".join(m[2].split())
    for key, (kw, src) in ENGINE_MODEL_KW.items():
        if _up(key) == _up(name):
            return n * kw, src
    for key, kw in SISTER_MODELS.items():
        if _up(key) == _up(name):
            return kw, "sister ship in thesis EK 2"
    return None, None


def build(folder: Path) -> pd.DataFrame:
    rows = []
    for f in sorted(folder.glob("*.xlsx")):
        firm = next((v for k, v in FIRMS.items() if k in f.name), None)
        if firm is None:
            continue
        raw = pd.read_excel(f, sheet_name="Sayfa1", header=0, skiprows=1, dtype=object)
        raw.columns = [_up(c) for c in raw.columns]
        raw = raw[raw["DISTANCE TRAVELED"].notna()].reset_index(drop=True)
        for i, r in raw.iterrows():
            name = str(r["VESSEL NAME"]).strip()
            gt = float(str(r["TONNAGE"]).replace(",", "."))
            rec = dict(firm=firm, vessel=name, trozzi_type=_up(r["TYPE OF VESSEL"]), gt=gt,
                       distance_nm=float(r["DISTANCE TRAVELED"]), engine=_up(r["TYPE OF ENGINE"]))
            main = aux = speed = None
            ms = as_ = ss = None
            if firm == "TURYOL":       # columns hold engine 1 and engine 2 (kW*make)
                e1, e2 = _kw(r.get("ANA MAKINE TIPI")), _kw(r.get("ANA MAKINE GÜCÜ"))
                main, ms = (e1 or 0) + (e2 or 0), "inventory (engine 1 + engine 2)"
                speed, ss = EK_SPEED[firm][i], "thesis EK 3"
            elif firm == "MAVI MARMARA":
                main, ms = _kw(r.get("ANA MAKINE GÜCÜ")), "inventory"
                speed, ss = EK_SPEED[firm][i], "thesis EK 6"
            elif firm == "SEHIR HATLARI":
                main, ms = _kw(r.get("ANA MAKINE GÜCÜ")), "inventory"
                if main is None and _up(name) in EK_SEHIR_HATLARI_MAIN:
                    main, ms = EK_SEHIR_HATLARI_MAIN[_up(name)], "thesis EK 1"
                aux = _kw(r.get("YARDIMCI MAKINE GÜCÜ"))
                as_ = "inventory" if aux else None
                speed = _speed(r.get("SPEED"))
                ss = "inventory" if speed else None
                if speed is None and _up(name) in EK_SEHIR_HATLARI_SPEED:
                    speed, ss = EK_SEHIR_HATLARI_SPEED[_up(name)], "thesis EK 1"
            elif firm == "IDO":
                speed, ss = _speed(r.get("SPEED")), "inventory"
                key = _up(name)
                if key in EK_IDO:
                    main, aux, _ = EK_IDO[key]
                    ms = as_ = "thesis EK 2"
                else:
                    main, ms = _model_kw(r.get("ANA MAKINE TIP VE GÜCÜ"))
            elif firm in EK_FLEET_DEFAULT:
                main, aux = EK_FLEET_DEFAULT[firm]
                ms = as_ = "thesis EK 4/5 (750 kW x 2, 265 kW x 2)"
            if main is None:
                main, ms = DEFAULTS["main_kw"], "default (no data)"
            if aux is None:
                aux, as_ = DEFAULTS["aux_kw"], as_ or "thesis EK default (265 kW x 2)"
            if speed is None:
                speed, ss = DEFAULTS["speed_kn"], "default (no data)"
            entec_type = "Passenger/Ro-Ro Cargo" if rec["trozzi_type"] == "PASSENGER/RO-RO/CARGO" else "Passenger"
            rec.update(entec_type=entec_type, main_kw=main, aux_kw=aux, speed_kn=speed,
                       main_kw_source=ms, aux_kw_source=as_, speed_source=ss)
            rows.append(rec)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("-o", "--output", default="data/local_fleet_2015.csv")
    a = ap.parse_args()
    df = build(Path(a.folder))
    df.to_csv(a.output, index=False)
    print(df.groupby("firm").agg(ships=("vessel", "size"), nm=("distance_nm", "sum"),
                                 main_kw=("main_kw", "mean")).round(0).to_string())
    print(df.main_kw_source.value_counts().to_string())


if __name__ == "__main__":
    main()
