from metahuman_blender.core.lod import infer_lod_index


def test_infer_lod_index_from_metahuman_mesh_name():
    assert infer_lod_index("body_lod0_mesh", 9) == 0
    assert infer_lod_index("body_lod3_mesh", 9) == 3
    assert infer_lod_index("head_mesh", 2) == 2
