from nocap.core.model import FloorReading, FloorState, Thresholds


def compute_floor_state(
    floor_id: str,
    reading: FloorReading | None,
    capacity: int,
    now: float,
    th: Thresholds,
) -> FloorState:
    """Subtract the two feeds: circling = cars on floor (cameras) - parked (bay sensors).

    Returns an invalid state, with a reason, whenever the inputs can't be trusted,
    so the sign can say "no advice" instead of guessing.
    """

    def invalid(reason: str) -> FloorState:
        return FloorState(floor_id=floor_id, valid=False, reason=reason)

    if reading is None:
        return invalid("no_data")
    if now - reading.ts > th.stale_after_s:
        return invalid("stale")
    if reading.sensor_coverage < th.min_coverage:
        return invalid("low_coverage")
    if not 0 <= reading.occupied <= capacity:
        return invalid("occupied_out_of_range")

    circling = reading.cars_on_floor - reading.occupied
    if circling < -th.max_inconsistency:
        # More cars parked than the cameras think are on the floor: one of the feeds is wrong.
        return invalid("cameras_below_parked")
    if circling > capacity:
        return invalid("circling_exceeds_capacity")

    circling = max(0, circling)  # small negatives are counting jitter
    free = capacity - reading.occupied
    return FloorState(
        floor_id=floor_id,
        valid=True,
        free=free,
        circling=circling,
        effective=free - circling,
    )
