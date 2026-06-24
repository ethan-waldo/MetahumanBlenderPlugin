from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

Vector3 = tuple[float, float, float]


@dataclass(slots=True)
class MetaHumanJoint:
    index: int
    name: str
    parent_index: int | None
    neutral_translation: Vector3 = (0.0, 0.0, 0.0)
    neutral_rotation: Vector3 = (0.0, 0.0, 0.0)
    lods: tuple[int, ...] = ()


@dataclass(slots=True)
class MeshSpec:
    index: int
    name: str
    vertices: list[Vector3] = field(default_factory=list)
    faces: list[tuple[int, ...]] = field(default_factory=list)
    uvs: list[tuple[float, float]] = field(default_factory=list)
    skin_weights: dict[int, list[tuple[int, float]]] = field(default_factory=dict)
    blend_shape_channels: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DNAAsset:
    path: Path
    db_name: str
    lod_count: int
    meshes: list[MeshSpec] = field(default_factory=list)
    joints: list[MetaHumanJoint] = field(default_factory=list)
    blend_shapes: list[str] = field(default_factory=list)
    raw_controls: list[str] = field(default_factory=list)
    gui_controls: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def character_name(self) -> str:
        stem = self.path.stem if self.path else "Character"
        return sanitize_name(stem)


@dataclass(slots=True)
class RigMap:
    mh_bone: str
    control_bone: str
    constraint_type: str = "COPY_TRANSFORMS"
    transform_space: str = "WORLD"
    axis_remap: dict[str, str] = field(default_factory=dict)
    weight: float = 1.0


@dataclass(slots=True)
class BakeSettings:
    frame_start: int
    frame_end: int
    visual_keying: bool = True
    clear_constraints_after_bake: bool = False


@dataclass(slots=True)
class RigLogicState:
    reader: Any
    rig_logic: Any
    rig_instance: Any
    lod: int = 0
    control_values: dict[str, float] = field(default_factory=dict)


def sanitize_name(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value.strip())
    return safe or "Character"


def flatten_names(items: Iterable[Any]) -> list[str]:
    return [str(item) for item in items]
