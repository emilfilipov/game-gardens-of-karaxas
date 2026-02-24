"""Generate baseline 3D assets (sellsword male/female, ground tile, foliage) via Blender.

Run with:
  python3 tools/blender/run_blender_headless.py --script tools/blender/scripts/generate_sellsword_3d_assets.py
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "assets/3d/generated"
CONCEPT_ART_DIR = ROOT / "concept_art"


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _load_concept_references() -> None:
    """Load concept front/back images as hidden reference empties for proportional guidance."""
    front = CONCEPT_ART_DIR / "sellsword_front.png"
    back = CONCEPT_ART_DIR / "sellsword_back.png"
    if not front.exists() or not back.exists():
        return
    try:
        front_image = bpy.data.images.load(str(front), check_existing=True)
        back_image = bpy.data.images.load(str(back), check_existing=True)
    except RuntimeError:
        return

    bpy.ops.object.empty_add(type="IMAGE", location=(0.0, -2.2, 1.08), rotation=(math.radians(90), 0.0, 0.0))
    front_ref = bpy.context.active_object
    front_ref.name = "ConceptFrontRef"
    front_ref.data = front_image
    front_ref.empty_image_side = "FRONT"
    front_ref.scale = (1.2, 1.2, 1.2)
    front_ref.hide_render = True

    bpy.ops.object.empty_add(type="IMAGE", location=(0.0, 2.2, 1.08), rotation=(math.radians(90), 0.0, math.radians(180)))
    back_ref = bpy.context.active_object
    back_ref.name = "ConceptBackRef"
    back_ref.data = back_image
    back_ref.empty_image_side = "FRONT"
    back_ref.scale = (1.2, 1.2, 1.2)
    back_ref.hide_render = True


def _mat(name: str, rgba: tuple[float, float, float, float], roughness: float = 0.85, metallic: float = 0.0):
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return material


def _primitive(name: str, primitive: str, location=(0, 0, 0), scale=(1, 1, 1), rotation=(0, 0, 0)) -> bpy.types.Object:
    if primitive == "cube":
        bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    elif primitive == "uv_sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(location=location, rotation=rotation, segments=36, ring_count=24)
    elif primitive == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(location=location, rotation=rotation, vertices=24)
    elif primitive == "plane":
        bpy.ops.mesh.primitive_plane_add(location=location, rotation=rotation)
    else:
        raise RuntimeError(f"unknown primitive {primitive}")
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    return obj


def _finish_mesh(obj: bpy.types.Object, smooth=True, bevel=0.015, bevel_segments=2) -> None:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if smooth:
        bpy.ops.object.shade_smooth()
    bev = obj.modifiers.new(name="Bevel", type="BEVEL")
    bev.width = bevel
    bev.segments = bevel_segments
    bev.limit_method = "ANGLE"
    bev.angle_limit = math.radians(35)


def _join_meshes(name: str, objects: list[bpy.types.Object]) -> bpy.types.Object:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    merged = bpy.context.active_object
    merged.name = name
    return merged


def _create_armature(name: str, shoulder_span: float = 0.72, hip_span: float = 0.34) -> bpy.types.Object:
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0.92))
    arm = bpy.context.active_object
    arm.name = name
    bones = arm.data.edit_bones

    root = bones[0]
    root.name = "root"
    root.head = (0.0, 0.0, 0.0)
    root.tail = (0.0, 0.0, 1.0)

    spine = bones.new("spine")
    spine.head = root.tail
    spine.tail = (0.0, 0.0, 1.52)
    spine.parent = root

    neck = bones.new("neck")
    neck.head = spine.tail
    neck.tail = (0.0, 0.0, 1.72)
    neck.parent = spine

    head = bones.new("head")
    head.head = neck.tail
    head.tail = (0.0, 0.0, 2.02)
    head.parent = neck

    upper_arm_l = bones.new("upper_arm.L")
    upper_arm_l.head = (shoulder_span * 0.5, 0.0, 1.48)
    upper_arm_l.tail = (shoulder_span * 0.92, 0.0, 1.28)
    upper_arm_l.parent = spine

    forearm_l = bones.new("forearm.L")
    forearm_l.head = upper_arm_l.tail
    forearm_l.tail = (shoulder_span * 1.18, 0.0, 1.06)
    forearm_l.parent = upper_arm_l

    hand_l = bones.new("hand.L")
    hand_l.head = forearm_l.tail
    hand_l.tail = (shoulder_span * 1.25, 0.0, 0.95)
    hand_l.parent = forearm_l

    upper_arm_r = bones.new("upper_arm.R")
    upper_arm_r.head = (-shoulder_span * 0.5, 0.0, 1.48)
    upper_arm_r.tail = (-shoulder_span * 0.92, 0.0, 1.28)
    upper_arm_r.parent = spine

    forearm_r = bones.new("forearm.R")
    forearm_r.head = upper_arm_r.tail
    forearm_r.tail = (-shoulder_span * 1.18, 0.0, 1.06)
    forearm_r.parent = upper_arm_r

    hand_r = bones.new("hand.R")
    hand_r.head = forearm_r.tail
    hand_r.tail = (-shoulder_span * 1.25, 0.0, 0.95)
    hand_r.parent = forearm_r

    thigh_l = bones.new("thigh.L")
    thigh_l.head = (hip_span * 0.5, 0.0, 0.98)
    thigh_l.tail = (hip_span * 0.5, 0.0, 0.56)
    thigh_l.parent = root

    shin_l = bones.new("shin.L")
    shin_l.head = thigh_l.tail
    shin_l.tail = (hip_span * 0.5, 0.0, 0.16)
    shin_l.parent = thigh_l

    foot_l = bones.new("foot.L")
    foot_l.head = shin_l.tail
    foot_l.tail = (hip_span * 0.5, 0.18, 0.05)
    foot_l.parent = shin_l

    thigh_r = bones.new("thigh.R")
    thigh_r.head = (-hip_span * 0.5, 0.0, 0.98)
    thigh_r.tail = (-hip_span * 0.5, 0.0, 0.56)
    thigh_r.parent = root

    shin_r = bones.new("shin.R")
    shin_r.head = thigh_r.tail
    shin_r.tail = (-hip_span * 0.5, 0.0, 0.16)
    shin_r.parent = thigh_r

    foot_r = bones.new("foot.R")
    foot_r.head = shin_r.tail
    foot_r.tail = (-hip_span * 0.5, 0.18, 0.05)
    foot_r.parent = shin_r

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def _bind_mesh_to_armature(mesh_obj: bpy.types.Object, armature_obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    mesh_obj.select_set(True)
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")


def _key_pose_bone_rotation(armature: bpy.types.Object, action: bpy.types.Action, bone_name: str, keyframes: list[tuple[int, tuple[float, float, float]]]) -> None:
    armature.animation_data_create()
    armature.animation_data.action = action
    pose_bone = armature.pose.bones.get(bone_name)
    if pose_bone is None:
        return
    pose_bone.rotation_mode = "XYZ"
    for frame, euler in keyframes:
        pose_bone.rotation_euler = euler
        pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame)


def _author_actions(armature: bpy.types.Object, action_prefix: str) -> None:
    actions = {
        "idle": {
            "length": 40,
            "bones": {
                "spine": [(1, (0.0, 0.0, 0.0)), (20, (math.radians(2.5), 0.0, 0.0)), (40, (0.0, 0.0, 0.0))],
            },
        },
        "walk": {
            "length": 28,
            "bones": {
                "upper_arm.L": [(1, (math.radians(-24), 0.0, 0.0)), (14, (math.radians(24), 0.0, 0.0)), (28, (math.radians(-24), 0.0, 0.0))],
                "upper_arm.R": [(1, (math.radians(24), 0.0, 0.0)), (14, (math.radians(-24), 0.0, 0.0)), (28, (math.radians(24), 0.0, 0.0))],
                "thigh.L": [(1, (math.radians(18), 0.0, 0.0)), (14, (math.radians(-18), 0.0, 0.0)), (28, (math.radians(18), 0.0, 0.0))],
                "thigh.R": [(1, (math.radians(-18), 0.0, 0.0)), (14, (math.radians(18), 0.0, 0.0)), (28, (math.radians(-18), 0.0, 0.0))],
            },
        },
        "run": {
            "length": 20,
            "bones": {
                "upper_arm.L": [(1, (math.radians(-42), 0.0, 0.0)), (10, (math.radians(42), 0.0, 0.0)), (20, (math.radians(-42), 0.0, 0.0))],
                "upper_arm.R": [(1, (math.radians(42), 0.0, 0.0)), (10, (math.radians(-42), 0.0, 0.0)), (20, (math.radians(42), 0.0, 0.0))],
                "thigh.L": [(1, (math.radians(28), 0.0, 0.0)), (10, (math.radians(-28), 0.0, 0.0)), (20, (math.radians(28), 0.0, 0.0))],
                "thigh.R": [(1, (math.radians(-28), 0.0, 0.0)), (10, (math.radians(28), 0.0, 0.0)), (20, (math.radians(-28), 0.0, 0.0))],
            },
        },
        "attack": {
            "length": 24,
            "bones": {
                "upper_arm.R": [(1, (math.radians(18), 0.0, 0.0)), (10, (math.radians(-82), 0.0, 0.0)), (24, (math.radians(18), 0.0, 0.0))],
                "forearm.R": [(1, (0.0, 0.0, 0.0)), (10, (math.radians(-32), 0.0, 0.0)), (24, (0.0, 0.0, 0.0))],
                "spine": [(1, (0.0, 0.0, 0.0)), (10, (0.0, 0.0, math.radians(-8))), (24, (0.0, 0.0, 0.0))],
            },
        },
        "cast": {
            "length": 28,
            "bones": {
                "upper_arm.L": [(1, (math.radians(-10), 0.0, 0.0)), (14, (math.radians(-62), 0.0, 0.0)), (28, (math.radians(-10), 0.0, 0.0))],
                "upper_arm.R": [(1, (math.radians(-10), 0.0, 0.0)), (14, (math.radians(-62), 0.0, 0.0)), (28, (math.radians(-10), 0.0, 0.0))],
            },
        },
        "hurt": {
            "length": 16,
            "bones": {
                "spine": [(1, (0.0, 0.0, 0.0)), (8, (math.radians(-20), 0.0, 0.0)), (16, (0.0, 0.0, 0.0))],
            },
        },
        "death": {
            "length": 42,
            "bones": {
                "root": [(1, (0.0, 0.0, 0.0)), (42, (0.0, 0.0, math.radians(90)))],
                "spine": [(1, (0.0, 0.0, 0.0)), (42, (math.radians(-20), 0.0, 0.0))],
            },
        },
    }

    for name, payload in actions.items():
        action = bpy.data.actions.new(name=f"{action_prefix}_{name}")
        action.use_fake_user = True
        frame_end = int(payload["length"])
        for bone_name, keys in payload["bones"].items():
            _key_pose_bone_rotation(armature, action, bone_name, keys)
        for fcurve in action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "LINEAR"
        action.frame_range = (1.0, float(frame_end))


def _build_sellsword(label: str, female: bool) -> bpy.types.Object:
    skin = _mat(f"Skin_{label}", (0.92, 0.78, 0.67, 1.0) if not female else (0.95, 0.82, 0.74, 1.0), 0.72)
    cloth = _mat(f"Cloth_{label}", (0.16, 0.18, 0.20, 1.0), 0.9)
    leather = _mat(f"Leather_{label}", (0.29, 0.18, 0.11, 1.0), 0.84)
    hair = _mat(f"Hair_{label}", (0.26, 0.17, 0.11, 1.0), 0.8)
    metal = _mat(f"Metal_{label}", (0.65, 0.66, 0.67, 1.0), 0.35, 0.25)
    scarf = _mat(f"Scarf_{label}", (0.46, 0.21, 0.14, 1.0), 0.78)
    fur = _mat(f"Fur_{label}", (0.48, 0.43, 0.34, 1.0), 0.96)

    pieces: list[bpy.types.Object] = []

    torso = _primitive(f"{label}_Torso", "cube", location=(0, 0, 1.03), scale=(0.38 if not female else 0.34, 0.22, 0.41))
    torso.data.materials.append(leather)
    _finish_mesh(torso)
    pieces.append(torso)

    chest = _primitive(f"{label}_Chest", "cube", location=(0, 0.02, 1.21), scale=(0.29, 0.18, 0.20))
    chest.data.materials.append(cloth)
    _finish_mesh(chest)
    pieces.append(chest)

    chest_plate = _primitive(f"{label}_ChestPlate", "cube", location=(0, 0.06, 1.18), scale=(0.24, 0.08, 0.15))
    chest_plate.data.materials.append(metal)
    _finish_mesh(chest_plate, bevel=0.01, bevel_segments=1)
    pieces.append(chest_plate)

    head = _primitive(f"{label}_Head", "uv_sphere", location=(0, 0, 1.72), scale=(0.19, 0.19, 0.22))
    head.data.materials.append(skin)
    _finish_mesh(head)
    pieces.append(head)

    hair_cap = _primitive(f"{label}_Hair", "uv_sphere", location=(0, 0.01, 1.85), scale=(0.20, 0.20, 0.11))
    hair_cap.data.materials.append(hair)
    _finish_mesh(hair_cap)
    pieces.append(hair_cap)

    if not female:
        beard = _primitive(f"{label}_Beard", "uv_sphere", location=(0.0, 0.10, 1.63), scale=(0.13, 0.08, 0.10))
        beard.data.materials.append(hair)
        _finish_mesh(beard, bevel=0.005, bevel_segments=1)
        pieces.append(beard)

    fur_collar = _primitive(f"{label}_FurCollar", "uv_sphere", location=(0, 0.0, 1.46), scale=(0.45, 0.30, 0.12))
    fur_collar.data.materials.append(fur)
    _finish_mesh(fur_collar, bevel=0.008, bevel_segments=1)
    pieces.append(fur_collar)

    scarf_wrap = _primitive(f"{label}_Scarf", "cylinder", location=(0.0, 0.05, 1.40), scale=(0.22, 0.22, 0.08), rotation=(math.radians(90), 0.0, 0.0))
    scarf_wrap.data.materials.append(scarf)
    _finish_mesh(scarf_wrap, bevel=0.007, bevel_segments=1)
    pieces.append(scarf_wrap)

    arm_l = _primitive(f"{label}_ArmL", "cylinder", location=(0.45, 0, 1.25), scale=(0.09, 0.09, 0.24), rotation=(0, 0, math.radians(90)))
    arm_l.data.materials.append(cloth)
    _finish_mesh(arm_l)
    pieces.append(arm_l)

    arm_r = _primitive(f"{label}_ArmR", "cylinder", location=(-0.45, 0, 1.25), scale=(0.09, 0.09, 0.24), rotation=(0, 0, math.radians(90)))
    arm_r.data.materials.append(cloth)
    _finish_mesh(arm_r)
    pieces.append(arm_r)

    pauldron_l = _primitive(f"{label}_PauldronL", "uv_sphere", location=(0.38, 0.0, 1.42), scale=(0.17, 0.15, 0.10))
    pauldron_l.data.materials.append(metal)
    _finish_mesh(pauldron_l, bevel=0.008, bevel_segments=1)
    pieces.append(pauldron_l)

    pauldron_r = _primitive(f"{label}_PauldronR", "uv_sphere", location=(-0.38, 0.0, 1.42), scale=(0.17, 0.15, 0.10))
    pauldron_r.data.materials.append(metal)
    _finish_mesh(pauldron_r, bevel=0.008, bevel_segments=1)
    pieces.append(pauldron_r)

    bracer_l = _primitive(f"{label}_BracerL", "cube", location=(0.58, 0.02, 0.96), scale=(0.09, 0.08, 0.15))
    bracer_l.data.materials.append(metal)
    _finish_mesh(bracer_l, bevel=0.006, bevel_segments=1)
    pieces.append(bracer_l)

    bracer_r = _primitive(f"{label}_BracerR", "cube", location=(-0.58, 0.02, 0.96), scale=(0.09, 0.08, 0.15))
    bracer_r.data.materials.append(metal)
    _finish_mesh(bracer_r, bevel=0.006, bevel_segments=1)
    pieces.append(bracer_r)

    belt = _primitive(f"{label}_Belt", "cube", location=(0.0, 0.05, 0.93), scale=(0.38, 0.08, 0.07))
    belt.data.materials.append(leather)
    _finish_mesh(belt, bevel=0.006, bevel_segments=1)
    pieces.append(belt)

    pouch = _primitive(f"{label}_Pouch", "cube", location=(0.32, 0.10, 0.88), scale=(0.10, 0.06, 0.10))
    pouch.data.materials.append(leather)
    _finish_mesh(pouch, bevel=0.004, bevel_segments=1)
    pieces.append(pouch)

    leg_l = _primitive(f"{label}_LegL", "cylinder", location=(0.15, 0, 0.56), scale=(0.11, 0.11, 0.36))
    leg_l.data.materials.append(cloth)
    _finish_mesh(leg_l)
    pieces.append(leg_l)

    leg_r = _primitive(f"{label}_LegR", "cylinder", location=(-0.15, 0, 0.56), scale=(0.11, 0.11, 0.36))
    leg_r.data.materials.append(cloth)
    _finish_mesh(leg_r)
    pieces.append(leg_r)

    knee_l = _primitive(f"{label}_KneeL", "uv_sphere", location=(0.15, 0.09, 0.45), scale=(0.12, 0.08, 0.08))
    knee_l.data.materials.append(metal)
    _finish_mesh(knee_l, bevel=0.005, bevel_segments=1)
    pieces.append(knee_l)

    knee_r = _primitive(f"{label}_KneeR", "uv_sphere", location=(-0.15, 0.09, 0.45), scale=(0.12, 0.08, 0.08))
    knee_r.data.materials.append(metal)
    _finish_mesh(knee_r, bevel=0.005, bevel_segments=1)
    pieces.append(knee_r)

    boot_l = _primitive(f"{label}_BootL", "cube", location=(0.15, 0.13, 0.15), scale=(0.12, 0.23, 0.09))
    boot_l.data.materials.append(leather)
    _finish_mesh(boot_l)
    pieces.append(boot_l)

    boot_r = _primitive(f"{label}_BootR", "cube", location=(-0.15, 0.13, 0.15), scale=(0.12, 0.23, 0.09))
    boot_r.data.materials.append(leather)
    _finish_mesh(boot_r)
    pieces.append(boot_r)

    boot_fur_l = _primitive(f"{label}_BootFurL", "uv_sphere", location=(0.15, 0.0, 0.30), scale=(0.15, 0.15, 0.07))
    boot_fur_l.data.materials.append(fur)
    _finish_mesh(boot_fur_l, bevel=0.004, bevel_segments=1)
    pieces.append(boot_fur_l)

    boot_fur_r = _primitive(f"{label}_BootFurR", "uv_sphere", location=(-0.15, 0.0, 0.30), scale=(0.15, 0.15, 0.07))
    boot_fur_r.data.materials.append(fur)
    _finish_mesh(boot_fur_r, bevel=0.004, bevel_segments=1)
    pieces.append(boot_fur_r)

    sword = _primitive(f"{label}_Sword", "cube", location=(-0.60, 0.0, 1.02), scale=(0.03, 0.03, 0.44), rotation=(0, 0, math.radians(-35)))
    sword.data.materials.append(metal)
    _finish_mesh(sword, bevel=0.006, bevel_segments=1)
    pieces.append(sword)

    if female:
        pony = _primitive(f"{label}_Ponytail", "cylinder", location=(0, -0.12, 1.64), scale=(0.04, 0.04, 0.16), rotation=(math.radians(24), 0, 0))
        pony.data.materials.append(hair)
        _finish_mesh(pony, bevel=0.007, bevel_segments=1)
        pieces.append(pony)

    body_mesh = _join_meshes(f"Sellsword_{label}_Body", pieces)

    armature = _create_armature(f"Sellsword_{label}_Rig", shoulder_span=0.74 if not female else 0.70, hip_span=0.34 if not female else 0.32)
    _bind_mesh_to_armature(body_mesh, armature)
    _author_actions(armature, f"sellsword_{label.lower()}")
    armature.name = f"Sellsword_{label}"
    return armature


def _build_ground_tile() -> bpy.types.Object:
    mat_stone = _mat("GroundStone", (0.21, 0.22, 0.21, 1.0), 0.94)
    mat_dirt = _mat("GroundDirt", (0.15, 0.12, 0.09, 1.0), 0.97)

    tile = _primitive("GroundTileStone", "cube", location=(0, 0, 0), scale=(1.0, 1.0, 0.06))
    tile.data.materials.append(mat_stone)
    _finish_mesh(tile, bevel=0.02, bevel_segments=2)

    dirt = _primitive("GroundTileDirt", "plane", location=(0, 0, 0.065), scale=(0.92, 0.92, 1.0), rotation=(0, 0, math.radians(13)))
    dirt.data.materials.append(mat_dirt)
    _finish_mesh(dirt, bevel=0.001, bevel_segments=1)

    return _join_meshes("GroundTileStoneA", [tile, dirt])


def _build_foliage() -> tuple[bpy.types.Object, bpy.types.Object]:
    grass_mat = _mat("GrassMat", (0.22, 0.41, 0.22, 1.0), 0.86)
    tree_mat = _mat("TreeMat", (0.29, 0.22, 0.16, 1.0), 0.9)

    grass_blades: list[bpy.types.Object] = []
    for i in range(7):
        blade = _primitive(
            f"GrassBlade_{i}",
            "cube",
            location=((i - 3) * 0.03, 0, 0.13 + (i % 2) * 0.01),
            scale=(0.014, 0.004, 0.15 + (i % 3) * 0.02),
            rotation=(0, math.radians((i - 3) * 8), math.radians(-14 + i * 5)),
        )
        blade.data.materials.append(grass_mat)
        _finish_mesh(blade, bevel=0.002, bevel_segments=1)
        grass_blades.append(blade)
    grass = _join_meshes("FoliageGrassA", grass_blades)

    trunk = _primitive("TreeTrunk", "cylinder", location=(0, 0, 1.45), scale=(0.23, 0.23, 1.45))
    trunk.data.materials.append(tree_mat)
    _finish_mesh(trunk, bevel=0.015, bevel_segments=2)

    branch_a = _primitive("TreeBranchA", "cylinder", location=(0.26, 0.0, 2.28), scale=(0.08, 0.08, 0.78), rotation=(0, math.radians(16), math.radians(52)))
    branch_a.data.materials.append(tree_mat)
    _finish_mesh(branch_a, bevel=0.008, bevel_segments=1)

    branch_b = _primitive("TreeBranchB", "cylinder", location=(-0.24, 0.0, 2.04), scale=(0.07, 0.07, 0.66), rotation=(0, math.radians(-20), math.radians(-48)))
    branch_b.data.materials.append(tree_mat)
    _finish_mesh(branch_b, bevel=0.008, bevel_segments=1)

    tree = _join_meshes("FoliageTreeDeadA", [trunk, branch_a, branch_b])

    return grass, tree


def _select_hierarchy(obj: bpy.types.Object) -> None:
    obj.select_set(True)
    for child in obj.children_recursive:
        child.select_set(True)


def _export_object(obj: bpy.types.Object, path: Path) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    _select_hierarchy(obj)
    bpy.context.view_layer.objects.active = obj
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_animations=True,
        export_frame_range=False,
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _clear_scene()
    _load_concept_references()

    male = _build_sellsword("Male", female=False)
    female = _build_sellsword("Female", female=True)
    ground = _build_ground_tile()
    grass, tree = _build_foliage()

    _export_object(male, OUT_DIR / "sellsword_male.glb")
    _export_object(female, OUT_DIR / "sellsword_female.glb")
    _export_object(ground, OUT_DIR / "ground_tile_stone.glb")
    _export_object(grass, OUT_DIR / "foliage_grass_a.glb")
    _export_object(tree, OUT_DIR / "foliage_tree_dead_a.glb")

    print(f"[blender-generate] exported assets to {OUT_DIR}")


if __name__ == "__main__":
    main()
