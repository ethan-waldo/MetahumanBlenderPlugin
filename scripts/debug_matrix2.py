import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import bpy
from metahuman_blender.core.dna_loader import load_dna
from metahuman_blender.core.joint_matrices import compute_joint_armature_matrices_blender, compute_joint_world_matrices
from metahuman_blender.ui.properties import _binding_paths_from_preferences

dna_path = Path.home() / "Downloads/OldGuy/NewMetaHumanCharacter/body.dna"
asset = load_dna(str(dna_path), _binding_paths_from_preferences(bpy.context))
armature = compute_joint_armature_matrices_blender(asset.joints)
world = compute_joint_world_matrices(asset.joints)

arm = bpy.data.armatures.new("T")
obj = bpy.data.objects.new("T", arm)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')

root = arm.edit_bones.new('root')
root.matrix = armature[[j.index for j in asset.joints if j.name=='root'][0]]
spine = arm.edit_bones.new('spine_01')
spine.parent = root
spine.matrix = armature[[j.index for j in asset.joints if j.name=='spine_01'][0]]

bpy.ops.object.mode_set(mode='OBJECT')
b = obj.data.bones['spine_01']
j = next(j for j in asset.joints if j.name=='spine_01')
d_local = max(abs(float(b.matrix_local[i][j]) - float(armature[j.index][i][j])) for i in range(4) for j in range(4))
print('matrix_local diff using edit armature assign', d_local)
w_expected = world[j.index]
d_world = max(abs(float(b.matrix[i][j]) - float(w_expected[i][j])) for i in range(4) for j in range(4))
print('matrix (pose rest world?) diff', d_world)
bpy.data.objects.remove(obj, do_unlink=True)
