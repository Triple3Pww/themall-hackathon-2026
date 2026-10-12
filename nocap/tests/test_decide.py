import pytest

from nocap.config import load_config
from nocap.core import Advice, FloorState, SignController, Thresholds, raw_advice

TH = Thresholds(low_threshold=1, margin_up=8, hold_seconds=20, min_dwell_seconds=60)


def fs(effective, valid=True):
    if not valid:
        return FloorState("X", valid=False, reason="stale")
    return FloorState("X", valid=True, free=effective, circling=0, effective=effective)


@pytest.mark.parametrize(
    "here, above, expected",
    [
        (fs(14), fs(9), Advice.GO),  # plenty here
        (fs(1), fs(23), Advice.UP),  # nearly gone here, clearly better above
        (fs(1), fs(5), Advice.GO),  # above not clearly better -> bias to turn in
        (fs(4), fs(40), Advice.GO),  # still above low threshold -> turn in
        (fs(2), fs(30), Advice.GO),  # 2 left is still worth turning in
        (fs(-6), fs(2), Advice.UP),  # over-contended here, above has room by margin
        (fs(0), None, Advice.GO),  # top floor
        (fs(0, valid=False), fs(30), Advice.NO_ADVICE),
        (fs(1), fs(0, valid=False), Advice.NO_ADVICE),
    ],
)
def test_raw_advice(here, above, expected):
    assert raw_advice(here, above, TH) == expected


def run(ctrl, seq):
    """seq: list of (t, advice). Returns shown advice at each t."""
    return [ctrl.update(a, t) for t, a in seq]


def test_starts_honest_then_needs_hold_to_show_advice():
    c = SignController(TH)
    assert c.update(Advice.GO, 0) == Advice.NO_ADVICE
    assert c.update(Advice.GO, 19) == Advice.NO_ADVICE
    assert c.update(Advice.GO, 20) == Advice.GO


def test_flapping_input_does_not_flip_sign():
    c = SignController(TH)
    run(c, [(0, Advice.GO), (20, Advice.GO)])
    flaps = [(t, Advice.UP if (t // 10) % 2 else Advice.GO) for t in range(21, 300)]
    shown = run(c, flaps)
    assert set(shown) == {Advice.GO}
    assert len(c.flips) == 1  # only NO_ADVICE -> GO at start


def test_switch_waits_for_dwell_and_hold():
    c = SignController(TH)
    run(c, [(0, Advice.GO), (20, Advice.GO)])  # GO shown since t=20
    assert c.update(Advice.UP, 30) == Advice.GO  # pending
    assert c.update(Advice.UP, 55) == Advice.GO  # held 25s but dwell only 35s
    assert c.update(Advice.UP, 80) == Advice.UP  # dwell 60s reached


def test_no_advice_is_immediate():
    c = SignController(TH)
    run(c, [(0, Advice.GO), (20, Advice.GO)])
    assert c.update(Advice.NO_ADVICE, 21) == Advice.NO_ADVICE
    assert [f.new for f in c.flips] == [Advice.GO, Advice.NO_ADVICE]


def test_evaluate_end_to_end():
    c = SignController(TH)
    c.evaluate(fs(1), fs(23), 0)
    assert c.evaluate(fs(1), fs(23), 20) == Advice.UP


def test_default_config_loads():
    cfg = load_config()
    assert [f.id for f in cfg.floors][:2] == ["P1", "P2"]
    assert cfg.above("P3").id == "P4"
    assert cfg.above(cfg.floors[-1].id) is None
