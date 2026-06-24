from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ControlMap:
    gui_controls: dict[str, int]
    raw_controls: dict[str, int]

    @classmethod
    def from_names(cls, gui_controls: list[str], raw_controls: list[str]) -> "ControlMap":
        return cls(
            gui_controls={name: index for index, name in enumerate(gui_controls)},
            raw_controls={name: index for index, name in enumerate(raw_controls)},
        )

    def gui_index(self, name: str) -> int | None:
        return self.gui_controls.get(name)

    def raw_index(self, name: str) -> int | None:
        return self.raw_controls.get(name)
