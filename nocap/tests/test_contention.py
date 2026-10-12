import pytest

from nocap.core import FloorReading, Thresholds, compute_floor_state

TH = Thresholds()
CAP = 100
NOW = 1000.0


def state(occupied, cars_on_floor, ts=NOW, coverage=1.0):
    return compute_floor_state(
        "P3", FloorReading(ts, occupied, cars_on_floor, coverage), CAP, NOW, TH
    )


def test_normal_subtraction():
    s = state(occupied=80, cars_on_floor=92)
    assert s.valid
    assert (s.free, s.circling, s.effective) == (20, 12, 8)


def test_over_contended_floor_goes_negative_but_displays_zero():
    s = state(occupied=95, cars_on_floor=105)
    assert s.effective == -5
    assert s.display_effective == 0


def test_small_negative_circling_is_jitter():
    s = state(occupied=80, cars_on_floor=77)
    assert s.valid and s.circling == 0 and s.effective == 20


@pytest.mark.parametrize(
    "kwargs, reason",
    [
        (dict(occupied=80, cars_on_floor=90, ts=NOW - TH.stale_after_s - 1), "stale"),
        (dict(occupied=80, cars_on_floor=90, coverage=0.5), "low_coverage"),
        (dict(occupied=80, cars_on_floor=80 - TH.max_inconsistency - 1), "cameras_below_parked"),
        (dict(occupied=10, cars_on_floor=10 + CAP + 1), "circling_exceeds_capacity"),
        (dict(occupied=CAP + 1, cars_on_floor=CAP + 1), "occupied_out_of_range"),
    ],
)
def test_untrustworthy_data_is_invalid(kwargs, reason):
    s = state(**kwargs)
    assert not s.valid
    assert s.reason == reason
    assert s.effective is None and s.display_effective is None


def test_missing_reading():
    s = compute_floor_state("P3", None, CAP, NOW, TH)
    assert not s.valid and s.reason == "no_data"
