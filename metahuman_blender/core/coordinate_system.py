from __future__ import annotations

from math import floor, radians

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


def dna_basis_to_blender():
    """Axis remap matching dna_location_to_blender for rotation matrices."""
    from mathutils import Matrix

    return Matrix(
        (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, -1.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )
    )


def dna_space_matrix_to_blender(matrix) -> object:
    """Convert a joint world matrix from DNA space into Blender world space."""
    from mathutils import Matrix, Vector

    basis = dna_basis_to_blender().to_3x3()
    rotation = basis @ matrix.to_3x3() @ basis.inverted()
    converted = rotation.to_4x4()
    converted.translation = Vector(dna_location_to_blender(tuple(matrix.translation)))
    return converted


def rest_rotation_bind_offset(target_rest_world, source_rest_world) -> object:
    """Map a source rest-frame world rotation delta into a target rest frame."""
    return target_rest_world.to_3x3() @ source_rest_world.to_3x3().inverted()


def dna_uv_to_blender(u: float, v: float) -> tuple[float, float]:
    """Normalize DNA UVs into tile-local 0-1 space for DCC export textures.

    MetaHuman body DNA often stores U in tile 1002 (e.g. 1.0-2.0) while the DCC
    export ships one PNG per part authored for tile 1001. Subtracting the tile
    offset keeps the same position within the tile but maps it into 0-1.
    """
    return (u - floor(u), v - floor(v))


def udim_tile_number_from_u(u: float) -> int:
    """Return the UDIM tile number (1001-based) containing coordinate U."""
    return int(floor(u)) + 1001


def add_vec(left: Vector3, right: Vector3) -> Vector3:
    return (left[0] + right[0], left[1] + right[1], left[2] + right[2])
