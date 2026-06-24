from metahuman_blender.core.scene_model import BakeSettings


def test_bake_settings_defaults_to_visual_keying():
    settings = BakeSettings(frame_start=1, frame_end=30)

    assert settings.visual_keying is True
    assert settings.clear_constraints_after_bake is False
