"""Hand-calculated checks of the unit-consistent ("corrected") methods."""
import math

import numpy as np
import pandas as pd
import pytest

from shipemis import entec, factors, trozzi


def test_entec_hand_calculation():
    df = pd.DataFrame([dict(ship_type="Passenger", distance_nm=493, main_kw=1500, aux_kw=530,
                            maneuvering_h=3, hotelling_h=3)])
    r = entec.estimate(df).iloc[0]
    cruise_kwh = 493 / 20.8 * (1500 * 0.8 + 530 * 0.3)
    man_kwh = 3 * (1500 * 0.2 + 530 * 0.4)
    hot_kwh = 3 * 530 * 0.5
    assert r.energy_cruise_kwh == pytest.approx(cruise_kwh)
    assert r.NOx_t == pytest.approx((cruise_kwh * 11.9 + man_kwh * 10.6 + hot_kwh * 11.2) / 1e6)
    assert r.fuel_t == pytest.approx((cruise_kwh * 219 + man_kwh * 235 + hot_kwh * 219) / 1e6)


def test_entec_co2_to_fuel_ratio_is_physical():
    df = pd.read_csv("examples/turyol_entec.csv")
    r = entec.estimate(df)
    ratio = r.CO2_t.sum() / r.fuel_t.sum()
    assert 3.1 < ratio < 3.25          # ~3.17-3.21 t CO2 per t marine fuel


def test_trozzi_hand_calculation_cruise():
    df = pd.DataFrame([dict(ship_type="PASSENGER", gt=300, cruise_days=1,
                            cruise_engine="MEDIUM SPEED DIESEL ENGINES")])
    r = trozzi.estimate(df).iloc[0]
    C = 16.904 + 0.00198 * 300
    assert r.fuel_t == pytest.approx(C * 0.8)
    assert r.NOx_t == pytest.approx(C * 0.8 * 57 / 1000)
    assert r.CO2_t / r.fuel_t == pytest.approx(3.2)


def test_trozzi_distance_to_days():
    df = pd.DataFrame([dict(ship_type="SOLID BULK", gt=20000, distance_nm=17,
                            cruise_engine="SLOW SPEED DIESEL ENGINES")])
    r = trozzi.estimate(df).iloc[0]
    days = 17 / 14.32 / 24
    assert r.fuel_t == pytest.approx((20.186 + 0.00049 * 20000) * 0.8 * days)


def test_trozzi_hotelling_fraction_by_type():
    df = pd.DataFrame([dict(ship_type=t, gt=1000, hotelling_days=1,
                            hotelling_engine="MEDIUM SPEED DIESEL ENGINES")
                       for t in ("PASSENGER", "LIQUID BULK", "CONTAINER")])
    r = trozzi.estimate(df)
    C = trozzi.full_power_consumption(df["ship_type"], df["gt"])
    np.testing.assert_allclose(r.fuel_t / C, [0.32, 0.20, 0.12])
    np.testing.assert_allclose(trozzi.estimate(df, hotelling_fraction=0.2).fuel_t / C, 0.2)


def test_generator_table_interpolation_hits_grid_points():
    ef = factors.trozzi_generator_ef_table([20, 200, 500], [0, 50, 75])
    assert ef["NOx"].tolist() == pytest.approx([60.89, 19.67, 51.05])


def test_generator_nox_polynomial_is_negative_mid_range():
    # documented limitation of the MEET regression – reason the table is the default
    assert factors.trozzi_generator_ef_polynomial(70, 40)["NOx"] < 0


def test_missing_optional_hours_are_zero():
    df = pd.DataFrame([dict(ship_type="Bulk Dry", distance_nm=17, main_kw=4397, aux_kw=5880),
                       dict(ship_type="Container", distance_nm=17, main_kw=14871, aux_kw=5880,
                            maneuvering_h=1.5, hotelling_h=12)])
    r = entec.estimate(df)
    assert r[["fuel_t", "CO2_t"]].notna().all().all()
    assert r.loc[0, "CO2_maneuvering_t"] == 0


def test_unknown_category_raises():
    with pytest.raises(KeyError):
        entec.estimate(pd.DataFrame([dict(ship_type="Submarine", distance_nm=1, main_kw=1, aux_kw=1)]))


def test_trozzi_speed_override():
    df = pd.DataFrame([dict(ship_type="ALL SHIPS", gt=300, distance_nm=240, speed_kn=10,
                            cruise_engine="MEDIUM SPEED DIESEL ENGINES")])
    r = trozzi.estimate(df).iloc[0]
    assert r.fuel_t == pytest.approx((16.263 + 0.001 * 300) * 0.8 * 240 / 10 / 24)
