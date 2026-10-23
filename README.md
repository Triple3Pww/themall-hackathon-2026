# No Cap – ป้ายนี้ไม่มีหลอก

**Parking signs that count the cars still circling, not just the empty bays.**
Team *Urgent Sud Sud* · MUICT × THE MALL Hackathon 2026 ("Smart Retail Solutions for a Sustainable Future")

### ▶ [Open the live 3D simulation](https://triple3pww.github.io/themall-hackathon-2026/mockups/nocap-3d.html)

## The problem

Mall parking signs show **free bays per floor**. At rush hour that number lies: if a floor has 4 free
bays and 4 cars are already circling it, the real number for the driver coming up the ramp is **zero**.
On a one-way up ramp, a wrong "go in" costs a full lap of the floor before the driver can climb again.

## The idea

Add two counting cameras at each floor's ramp turn-off (cars in − cars out). Combined with the existing
per-bay sensors:

```
circling  = cars_on_floor − occupied_bays
effective = free_bays − circling          # what the sign actually shows
```

The sign before each turn-off then says **เข้าได้เลย** (go in), **ขึ้นชั้นบน** (go up), or
**ไม่แนะนำ** (no advice) when the data can't be trusted.

## What's in the repo

| Path | What |
|---|---|
| [`nocap/`](nocap) | The decision core in Python: pure functions + dataclasses, **24 passing tests** |
| [`mockups/nocap-3d.html`](mockups/nocap-3d.html) | Three.js simulation of a floor, the ramp, the sign and the counting cameras, with a click-through "rush hour" scenario (old system vs No Cap) |
| [`mockups/video/`](mockups/video) | Per-step MP4 clips recorded headless from the simulation (scripts in `mockups/tools/`) |
| [`slides/`](slides) | Pitch-deck build that patches raw PPTX XML |

## Design decisions worth noting

- **Biased toward "go in".** A wrong *go up* is irreversible on a one-way ramp, so `UP` is shown only when
  this floor is effectively full **and** the next floor is clearly better (`margin_up`).
- **Honesty beats stability.** A hysteresis controller stops the sign from flickering between GO and UP,
  but switching *to* "no advice" is immediate whenever the data goes bad: stale readings, low sensor
  coverage, or camera counts that contradict the bay sensors.
- **No overclaiming.** The mall has per-bay sensors only; the ramp cameras are what this project adds.

## Run it

```sh
cd nocap
pip install -e '.[dev]'
pytest                      # 24 tests
```

The simulation needs no build: open `mockups/nocap-3d.html` in a browser.

**Stack:** Python 3.11+ · pytest · Three.js · Playwright + ffmpeg (video capture)
