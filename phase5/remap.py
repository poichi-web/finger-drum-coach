"""パッドノートリマップ: MIDI入力ノート → GM ドラムノートの変換レイヤー"""
import json
from pathlib import Path

PRESETS_DIR = Path(__file__).parent.parent / "presets"

GM_DRUMS: dict[int, str] = {
    35: "Bass Drum 2",
    36: "Bass Drum 1 (Kick)",
    37: "Side Stick",
    38: "Acoustic Snare",
    39: "Hand Clap",
    40: "Electric Snare",
    41: "Low Floor Tom",
    42: "Closed Hi-Hat",
    43: "High Floor Tom",
    44: "Pedal Hi-Hat",
    45: "Low Tom",
    46: "Open Hi-Hat",
    47: "Low-Mid Tom",
    48: "Hi-Mid Tom",
    49: "Crash Cymbal 1",
    50: "High Tom",
    51: "Ride Cymbal 1",
    52: "Chinese Cymbal",
    53: "Ride Bell",
    54: "Tambourine",
    55: "Splash Cymbal",
    56: "Cowbell",
    57: "Crash Cymbal 2",
    58: "Vibraslap",
    59: "Ride Cymbal 2",
}


class Remap:
    def __init__(self, note_map: dict[int, int] | None = None, name: str = "my_kit"):
        self.name = name
        self._map: dict[int, int] = note_map or {}

    def apply(self, note: int) -> int:
        """入力ノートを割当先ノートに変換する"""
        return self._map.get(note, note)

    def set(self, original: int, target: int) -> None:
        self._map[original] = target

    def clear(self, original: int) -> None:
        self._map.pop(original, None)

    def note_map(self) -> dict[int, int]:
        return dict(self._map)

    def save(self, name: str | None = None) -> Path:
        if name:
            self.name = name
        PRESETS_DIR.mkdir(exist_ok=True)
        path = PRESETS_DIR / f"{self.name}.json"
        data = {
            "name": self.name,
            "note_map": {str(k): v for k, v in self._map.items()},
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    @classmethod
    def from_file(cls, path: Path) -> "Remap":
        data = json.loads(path.read_text(encoding="utf-8"))
        note_map = {int(k): int(v) for k, v in data.get("note_map", {}).items()}
        return cls(note_map=note_map, name=data.get("name", path.stem))

    @classmethod
    def list_presets(cls) -> list[Path]:
        if not PRESETS_DIR.exists():
            return []
        return sorted(PRESETS_DIR.glob("*.json"))
