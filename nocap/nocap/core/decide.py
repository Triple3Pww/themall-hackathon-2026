from dataclasses import dataclass, field

from nocap.core.model import Advice, FloorState, Thresholds


def raw_advice(here: FloorState, above: FloorState | None, th: Thresholds) -> Advice:
    """Instantaneous advice for the sign before the ramp fork into `here`.

    Biased toward GO: a wrong GO costs one short loop, a wrong UP can't be undone
    on a one-way ramp.
    """
    if not here.valid:
        return Advice.NO_ADVICE
    if above is None:
        return Advice.GO  # top floor: nothing better to send drivers to
    if not above.valid:
        return Advice.NO_ADVICE
    if (
        here.effective <= th.low_threshold
        and above.effective - here.effective >= th.margin_up
    ):
        return Advice.UP
    return Advice.GO


@dataclass(frozen=True)
class Flip:
    ts: float
    old: Advice
    new: Advice


@dataclass
class SignController:
    """Applies hysteresis so the sign doesn't flicker.

    - GO <-> UP: the new advice must persist `hold_seconds`, and the current one
      must have been shown for `min_dwell_seconds`.
    - Anything -> NO_ADVICE: immediate. Honesty beats stability.
    - NO_ADVICE -> GO/UP: needs `hold_seconds` of steady data, no dwell.
    """

    th: Thresholds
    current: Advice = Advice.NO_ADVICE
    since: float | None = None
    flips: list[Flip] = field(default_factory=list)
    _pending: Advice | None = None
    _pending_since: float = 0.0

    def update(self, advice: Advice, now: float) -> Advice:
        if self.since is None:
            self.since = now

        if advice == self.current:
            self._pending = None
            return self.current

        if advice == Advice.NO_ADVICE:
            self._switch(advice, now)
            return self.current

        if advice != self._pending:
            self._pending, self._pending_since = advice, now

        held = now - self._pending_since >= self.th.hold_seconds
        dwelled = (
            self.current == Advice.NO_ADVICE
            or now - self.since >= self.th.min_dwell_seconds
        )
        if held and dwelled:
            self._switch(advice, now)
        return self.current

    def evaluate(
        self, here: FloorState, above: FloorState | None, now: float
    ) -> Advice:
        return self.update(raw_advice(here, above, self.th), now)

    def _switch(self, advice: Advice, now: float) -> None:
        self.flips.append(Flip(now, self.current, advice))
        self.current, self.since, self._pending = advice, now, None
