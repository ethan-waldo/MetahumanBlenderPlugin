from metahuman_blender.core.faceboard_json import (
    bundled_faceboard_json_path,
    discover_faceboard_json,
    load_faceboard_json,
    region_group_name,
)


def test_bundled_faceboard_json_exists():
    path = bundled_faceboard_json_path()
    assert path.name == "faceboard.json"
    assert path.exists()
    definition = load_faceboard_json(path)
    assert definition.version
    assert len(definition.gui_controls) > 0


def test_discover_faceboard_json_returns_bundled():
    assert discover_faceboard_json() == bundled_faceboard_json_path()


def test_region_group_name_maps_brow():
    assert region_group_name("brow") == "GRP_browGUI"
    assert region_group_name("faceTweakers") == "GRP_faceTweakersGUI"
