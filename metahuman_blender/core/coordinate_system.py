from __future__ import annotations

from math import radians

from .scene_model import Vector3

UNREAL_CENTIMETERS_TO_BLENDER_METERS = 0.01


def dna_location_to_blender(value: Vector3, scale: float = UNREAL_CENTIMETERS_TO_BLENDER_METERS) -> Vector3:
    """Convert DNA character coordinates into Blender's default Z-up axes."""
    x, y, z = value
    return (x * scale, -z * scale, y * scale)


def dna_rotation_to_blender_euler(value: Vector3) -> Vector3:
    """Convert DNA neutral rotations to a Blender-friendly XYZ Euler approximation."""
    x, y, z = value
    return (radians(y), radians(-x), radians(z))


def add_vec(left: Vector3, right: Vector3) -> Vector3:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])
