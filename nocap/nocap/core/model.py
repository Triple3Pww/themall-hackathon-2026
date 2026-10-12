from dataclasses import dataclass
from enum import Enum


class Advice(str, Enum):
    GO = "GO"  # เข้าได้เลย
    UP = "UP"  # ขึ้นชั้นบน
    NO_ADVICE = "NO_ADVICE"  # ไม่แนะนำ – ข้อมูลไม่พอ ขอไม่เดา


@dataclass(frozen=True)
class FloorConfig:
    id: str
    capacity: int
    cam_in: str
    cam_out: str


@dataclass(frozen=True)
class Thresholds:
    low_threshold: int = 1
    margin_up: int = 8
    hold_seconds: float = 20
    min_dwell_seconds: float = 60
    stale_after_s: float = 30
    min_coverage: float = 0.90
    max_inconsistency: int = 5


@dataclass(frozen=True)
class FloorReading:
    """Raw inputs for one floor at one moment.

    occupied: bays reported occupied by the existing bay sensors.
    cars_on_floor: ramp camera count, cars in minus cars out.
    sensor_coverage: share of bay sensors currently reporting (0..1).
    """

    ts: float
    occupied: int
    cars_on_floor: int
    sensor_coverage: float = 1.0


@dataclass(frozen=True)
class FloorState:
    """Derived view of one floor. Numbers are None when the data is not trustworthy."""

    floor_id: str
    valid: bool
    free: int | None = None
    circling: int | None = None
    effective: int | None = None  # free - circling; may be negative when over-contended
    reason: str | None = None

    @property
    def display_effective(self) -> int | None:
        """What the sign shows: never a negative space count."""
        return None if self.effective is None else max(0, self.effective)
