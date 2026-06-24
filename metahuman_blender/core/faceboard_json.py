from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path


class FaceboardJsonError(RuntimeError):
    pass


@dataclass(slots=True)
class FaceboardAxis:
    axis: str
    src_min: float
    src_max: float


@dataclass(slots=True)
class FaceboardControl:
    name: str
    parent: str | None
    position: tuple[float, float]
    z_order: float = 0.0
    region: str = ""
    axes: list[FaceboardAxis] = field(default_factory=list)


@dataclass(slots=True)
class FaceboardGroup:
    name: str
    parent: str | None
    position: tuple[float, float]
    z_order: float = 0.0


@dataclass(slots=True)
class FaceboardDefinition:
    path: Path
    rig_def: str
    version: str
    gui_groups: list[FaceboardGroup]
    gui_controls: list[FaceboardControl]
    analog_groups: list[FaceboardGroup]
    analog_controls: list[FaceboardControl]
    origin_offset: tuple[float, float, float]
    extents: dict[str, list[float]]

    @property
    def all_controls(self) -> list[FaceboardControl]:
        return [*self.gui_controls, *self.analog_controls]


def load_faceboard_json(path: str | Path) -> FaceboardDefinition:
    json_path = Path(path).expanduser().resolve()
    if not json_path.exists():
        raise FaceboardJsonError(f"Faceboard JSON does not exist: {json_path}")

    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FaceboardJsonError(f"Invalid faceboard JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise FaceboardJsonError("Faceboard JSON root must be an object.")

    gui = payload.get("gui") or {}
    analog = payload.get("analog") or {}
    if not isinstance(gui, dict) or not isinstance(analog, dict):
        raise FaceboardJsonError("Faceboard JSON must contain gui and analog sections.")

    origin = gui.get("origin_offset") or [0.0, 0.0, 0.0]
    extents = gui.get("extents") or {"min": [0.0, 0.0], "max": [0.0, 0.0]}

    return FaceboardDefinition(
        path=json_path,
        rig_def=str(payload.get("rig_def") or ""),
        version=str(payload.get("version") or ""),
        gui_groups=_parse_groups(gui.get("groups")),
        gui_controls=_parse_controls(gui.get("controls")),
        analog_groups=_parse_groups(analog.get("groups")),
        analog_controls=_parse_controls(analog.get("controls")),
        origin_offset=(float(origin[0]), float(origin[1]), float(origin[2])),
        extents=extents,
    )


def bundled_faceboard_json_path() -> Path:
    addon_root = Path(__file__).resolve().parents[1]
    json_path = addon_root / "resources" / "faceboard.json"
    if not json_path.exists():
        raise FaceboardJsonError(
            f"Bundled MetaHuman faceboard is missing from the add-on: {json_path}"
        )
    return json_path


def discover_faceboard_json(start_path: str | Path | None = None) -> Path:
    """Return the bundled faceboard.json shipped with the add-on."""
    return bundled_faceboard_json_path()


def _parse_groups(raw) -> list[FaceboardGroup]:
    if not isinstance(raw, list):
        return []
    groups: list[FaceboardGroup] = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        position = item.get("position") or [0.0, 0.0]
        groups.append(
            FaceboardGroup(
                name=str(item["name"]),
                parent=str(item["parent"]) if item.get("parent") else None,
                position=(float(position[0]), float(position[1])),
                z_order=float(item.get("z_order") or 0.0),
            )
        )
    return groups


def _parse_controls(raw) -> list[FaceboardControl]:
    if not isinstance(raw, list):
        return []
    controls: list[FaceboardControl] = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        position = item.get("position") or [0.0, 0.0]
        axes = []
        for axis in item.get("axes") or []:
            if not isinstance(axis, dict):
                continue
            axes.append(
                FaceboardAxis(
                    axis=str(axis.get("axis") or ""),
                    src_min=float(axis.get("src_min") or 0.0),
                    src_max=float(axis.get("src_max") or 0.0),
                )
            )
        controls.append(
            FaceboardControl(
                name=str(item["name"]),
                parent=str(item["parent"]) if item.get("parent") else None,
                position=(float(position[0]), float(position[1])),
                z_order=float(item.get("z_order") or 0.0),
                region=str(item.get("region") or ""),
                axes=axes,
            )
        )
    return controls


def active_axis_for_control(control: FaceboardControl) -> FaceboardAxis | None:
    for axis in control.axes:
        if axis.src_max > axis.src_min:
            return axis
    return None


def region_group_name(region: str) -> str | None:
    if not region:
        return None
    special = {
        "faceTweakers": "GRP_faceTweakersGUI",
        "lipsControls": "GRP_lipsControlsGUI",
        "mouthSticky": "GRP_mouthStickyGUI",
        "faceAndEyesAimFollowHead": "GRP_faceAndEyesAimFollowHeadGUI",
    }
    if region in special:
        return special[region]
    return f"GRP_{region}GUI"
