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


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _mat(name: str, rgba: tuple[float, float, float, float], roughness: float = 0.85, metallic: float = 0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def _primitive(name: str, primitive: str, location=(0, 0, 0), scale=(1, 1, 1), rotation=(0, 0, 0)):
    if primitive == "cube":
        bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    elif primitive == "uv_sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(location=location, rotation=rotation, segments=24, ring_count=12)
    elif primitive == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(location=location, rotation=rotation, vertices=16)
    elif primitive == "capsule":
        bpy.ops.mesh.primitive_uv_sphere_add(location=location, rotation=rotation, segments=18, ring_count=10)
    else:
        raise RuntimeError(f"unknown primitive {primitive}")
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    return obj


def _build_sellsword(label: str, female: bool) -> bpy.types.Object:
    root = bpy.data.objects.new(f"Sellsword_{label}", None)
    bpy.context.collection.objects.link(root)

    skin = _mat(f"Skin_{label}", (0.92, 0.78, 0.67, 1.0) if not female else (0.95, 0.82, 0.74, 1.0), 0.72)
    cloth = _mat(f"Cloth_{label}", (0.30, 0.46, 0.36, 1.0), 0.9)
    leather = _mat(f"Leather_{label}", (0.45, 0.29, 0.18, 1.0), 0.84)
    hair = _mat(f"Hair_{label}", (0.26, 0.17, 0.11, 1.0), 0.8)

    parts = []
    parts.append((_primitive(f"{label}_Head", "uv_sphere", location=(0, 0, 1.45), scale=(0.18, 0.18, 0.20)), skin))
    parts.append((_primitive(f"{label}_Hair", "uv_sphere", location=(0, 0.01, 1.55), scale=(0.20, 0.20, 0.10)), hair))
    parts.append((_primitive(f"{label}_Torso", "cube", location=(0, 0, 1.00), scale=(0.30, 0.20, 0.30 if not female else 0.28)), leather))
    parts.append((_primitive(f"{label}_Chest", "cube", location=(0, 0.02, 1.15), scale=(0.24, 0.16, 0.16)), cloth))
    parts.append((_primitive(f"{label}_ArmL", "cylinder", location=(-0.36, 0, 0.98), scale=(0.07, 0.07, 0.23), rotation=(0, 0, math.radians(90))), cloth))
    parts.append((_primitive(f"{label}_ArmR", "cylinder", location=(0.36, 0, 0.98), scale=(0.07, 0.07, 0.23), rotation=(0, 0, math.radians(90))), cloth))
    parts.append((_primitive(f"{label}_LegL", "cylinder", location=(-0.14, 0, 0.45), scale=(0.09, 0.09, 0.28)), cloth))
    parts.append((_primitive(f"{label}_LegR", "cylinder", location=(0.14, 0, 0.45), scale=(0.09, 0.09, 0.28)), cloth))

    if female:
        parts.append((_primitive(f"{label}_Ponytail", "cylinder", location=(0, -0.12, 1.35), scale=(0.04, 0.04, 0.14), rotation=(math.radians(24), 0, 0)), hair))

    for obj, material in parts:
        obj.parent = root
        if len(obj.data.materials) == 0:
            obj.data.materials.append(material)
        else:
            obj.data.materials[0] = material

    return root


def _build_ground_tile() -> bpy.types.Object:
    mat = _mat("GroundStone", (0.23, 0.24, 0.23, 1.0), 0.96)
    tile = _primitive("GroundTileStone", "cube", location=(0, 0, 0), scale=(1.0, 1.0, 0.05))
    tile.data.materials.append(mat)
    return tile


def _build_foliage() -> tuple[bpy.types.Object, bpy.types.Object]:
    grass_mat = _mat("GrassMat", (0.22, 0.41, 0.22, 1.0), 0.86)
    tree_mat = _mat("TreeMat", (0.29, 0.22, 0.16, 1.0), 0.9)

    grass_root = bpy.data.objects.new("FoliageGrassA", None)
    bpy.context.collection.objects.link(grass_root)
    for i in range(3):
        blade = _primitive(
            f"GrassBlade_{i}",
            "cube",
            location=((i - 1) * 0.04, 0, 0.12),
            scale=(0.02, 0.004, 0.12),
            rotation=(0, 0, math.radians(-7 + i * 7)),
        )
        blade.parent = grass_root
        blade.data.materials.append(grass_mat)

    tree_root = bpy.data.objects.new("FoliageTreeDeadA", None)
    bpy.context.collection.objects.link(tree_root)
    trunk = _primitive("TreeTrunk", "cylinder", location=(0, 0, 1.4), scale=(0.24, 0.24, 1.4))
    trunk.parent = tree_root
    trunk.data.materials.append(tree_mat)
    branch = _primitive("TreeBranch", "cylinder", location=(0.24, 0, 2.4), scale=(0.07, 0.07, 0.72), rotation=(0, math.radians(10), math.radians(52)))
    branch.parent = tree_root
    branch.data.materials.append(tree_mat)

    return grass_root, tree_root


def _export_object(obj: bpy.types.Object, path: Path) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _clear_scene()

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
