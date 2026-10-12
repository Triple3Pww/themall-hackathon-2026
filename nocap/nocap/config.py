from dataclasses import dataclass
from pathlib import Path

import yaml

from nocap.core.model import FloorConfig, Thresholds

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config" / "mall.yaml"


@dataclass(frozen=True)
class MallConfig:
    floors: list[FloorConfig]  # bottom -> top
    thresholds: Thresholds

    def above(self, floor_id: str) -> FloorConfig | None:
        ids = [f.id for f in self.floors]
        i = ids.index(floor_id)
        return self.floors[i + 1] if i + 1 < len(self.floors) else None


def load_config(path: Path | str = DEFAULT_PATH) -> MallConfig:
    raw = yaml.safe_load(Path(path).read_text())
    floors = [FloorConfig(**f) for f in raw["floors"]]
    if len({f.id for f in floors}) != len(floors):
        raise ValueError("duplicate floor id in config")
    return MallConfig(floors=floors, thresholds=Thresholds(**raw.get("thresholds", {})))
