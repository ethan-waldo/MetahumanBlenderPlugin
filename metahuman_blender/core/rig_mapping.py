from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json

from .scene_model import RigMap

BODY_BONE_EXACT = {
    "root",
    "pelvis",
    "spine_01",
    "spine_02",
    "spine_03",
    "spine_04",
    "spine_05",
    "neck_01",
    "neck_02",
    "head",
}

BODY_BONE_TOKENS = (
    "clavicle",
    "upperarm",
    "lowerarm",
    "hand",
    "thigh",
    "calf",
    "foot",
    "ball",
)


@dataclass(slots=True)
class MappingReport:
    maps: list[RigMap]
    missing_controls: list[str] = field(default_factory=list)
    skipped_bones: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.missing_controls and bool(self.maps)


def is_body_bone(name: str) -> bool:
    lowered = name.lower()
    if lowered.startswith("facial_") or lowered.startswith("teeth") or lowered.startswith("eye"):
        return False
    return lowered in BODY_BONE_EXACT or any(token in lowered for token in BODY_BONE_TOKENS)


def control_name_for_bone(mh_bone_name: str) -> str:
    return f"CTRL_{mh_bone_name}"


def infer_body_rig_map(mh_armature, control_armature) -> MappingReport:
    control_names = {bone.name for bone in control_armature.data.bones}
    maps: list[RigMap] = []
    missing: list[str] = []
    skipped: list[str] = []
    for bone in mh_armature.data.bones:
        if not is_body_bone(bone.name):
            skipped.append(bone.name)
            continue
        control_name = control_name_for_bone(bone.name)
        if control_name in control_names:
            maps.append(RigMap(mh_bone=bone.name, control_bone=control_name))
        else:
            missing.append(bone.name)
    return MappingReport(maps=maps, missing_controls=missing, skipped_bones=skipped)


def rig_maps_to_json(maps: list[RigMap]) -> str:
    return json.dumps([asdict(item) for item in maps], indent=2, sort_keys=True)


def rig_maps_from_json(value: str) -> list[RigMap]:
    if not value:
        return []
    return [RigMap(**item) for item in json.loads(value)]
