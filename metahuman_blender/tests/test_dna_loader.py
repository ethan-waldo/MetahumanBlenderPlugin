from pathlib import Path
from types import SimpleNamespace

from metahuman_blender.core.dna_loader import asset_from_reader


class FakeReader:
    def getLODCount(self):
        return 1

    def getDBName(self):
        return "MH.4"

    def getJointCount(self):
        return 2

    def getJointName(self, index):
        return ["root", "pelvis"][index]

    def getJointParentIndex(self, index):
        return index if index == 0 else 0

    def getNeutralJointTranslation(self, index):
        return [(0.0, 0.0, 0.0), (0.0, 0.0, 100.0)][index]

    def getNeutralJointRotation(self, index):
        return (0.0, 0.0, 0.0)

    def getJointIndicesForLOD(self, lod):
        return [0, 1]

    def getMeshCount(self):
        return 1

    def getMeshName(self, index):
        return "body_lod0_mesh"

    def getVertexPositionCount(self, mesh_index):
        return 3

    def getVertexPositionXs(self, mesh_index):
        return [0.0, 1.0, 0.0]

    def getVertexPositionYs(self, mesh_index):
        return [0.0, 0.0, 1.0]

    def getVertexPositionZs(self, mesh_index):
        return [0.0, 0.0, 0.0]

    def getFaceCount(self, mesh_index):
        return 1

    def getFaceVertexLayoutIndices(self, mesh_index, face_index):
        return [0, 1, 2]

    def getBlendShapeChannelCount(self):
        return 1

    def getBlendShapeChannelName(self, index):
        return "jawOpen"

    def getMeshBlendShapeChannelMappingCount(self):
        return 1

    def getMeshBlendShapeChannelMapping(self, index):
        return SimpleNamespace(meshIndex=0, blendShapeChannelIndex=0)

    def getRawControlCount(self):
        return 1

    def getRawControlName(self, index):
        return "CTRL_jawOpen"

    def getGUIControlCount(self):
        return 1

    def getGUIControlName(self, index):
        return "gui_jawOpen"


def test_asset_from_reader_extracts_core_metadata():
    asset = asset_from_reader(FakeReader(), Path("/tmp/Ada.dna"))

    assert asset.character_name == "Ada"
    assert asset.db_name == "MH.4"
    assert [joint.name for joint in asset.joints] == ["root", "pelvis"]
    assert asset.joints[0].parent_index is None
    assert asset.joints[1].parent_index == 0
    assert asset.meshes[0].faces == [(0, 1, 2)]
    assert asset.meshes[0].blend_shape_channels == ["jawOpen"]
    assert asset.raw_controls == ["CTRL_jawOpen"]
    assert asset.gui_controls == ["gui_jawOpen"]
