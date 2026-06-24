from types import SimpleNamespace

from metahuman_blender.core.scene_model import CharacterInstance, infer_character_name
from metahuman_blender.core.character_assembly import character_from_empty, save_character_to_empty


class FakeEmpty(dict):
    def get(self, key, default=None):
        return super().get(key, default)


def test_infer_character_name_from_dcc_export_folder():
    assert infer_character_name("/exports/OldGuy/body.dna") == "OldGuy"
    assert infer_character_name("/exports/OldGuy/head.dna") == "OldGuy"
    assert infer_character_name("/exports/CustomCharacter.dna") == "CustomCharacter"


def test_character_instance_roundtrip():
    empty = FakeEmpty(
        {
            "character_name": "OldGuy",
            "export_manifest_path": "/exports/OldGuy/ExportManifest.json",
            "body_dna_path": "/exports/OldGuy/body.dna",
            "head_dna_path": "/exports/OldGuy/head.dna",
            "deform_skeleton": "MH_OldGuy_SKEL",
            "body_control_rig": "CTRL_OldGuy_RIG",
            "faceboard_rig": "FaceBoard",
            "body_meshes_json": '["MH_OldGuy_body_lod0_mesh"]',
            "head_meshes_json": '["MH_OldGuy_head_lod0_mesh"]',
            "texture_maps_json": '["/exports/OldGuy/Maps/Head_Basecolor.png"]',
            "texture_masks_json": '[]',
            "thumbnail_path": "/exports/OldGuy/OldGuy.png",
        }
    )
    character = character_from_empty(empty)
    assert character.character_name == "OldGuy"
    assert character.head_meshes == ["MH_OldGuy_head_lod0_mesh"]

    save_character_to_empty(empty, character)
    restored = character_from_empty(empty)
    assert restored == CharacterInstance(
        character_name="OldGuy",
        export_manifest_path="/exports/OldGuy/ExportManifest.json",
        body_dna_path="/exports/OldGuy/body.dna",
        head_dna_path="/exports/OldGuy/head.dna",
        deform_skeleton="MH_OldGuy_SKEL",
        body_control_rig="CTRL_OldGuy_RIG",
        faceboard_rig="FaceBoard",
        head_meshes=["MH_OldGuy_head_lod0_mesh"],
        body_meshes=["MH_OldGuy_body_lod0_mesh"],
        texture_maps=["/exports/OldGuy/Maps/Head_Basecolor.png"],
        texture_masks=[],
        thumbnail_path="/exports/OldGuy/OldGuy.png",
    )
