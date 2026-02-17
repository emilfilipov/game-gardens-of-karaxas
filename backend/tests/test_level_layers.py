from fastapi import HTTPException

from app.api.routes.levels import _derive_wall_cells, _normalize_layers_from_payload
from app.schemas.level import LevelLayerCell, LevelSaveRequest


def test_legacy_wall_payload_is_upgraded_to_layered_data() -> None:
    payload = LevelSaveRequest(
        name="Legacy",
        width=20,
        height=20,
        spawn_x=1,
        spawn_y=1,
        wall_cells=[
            {"x": 2, "y": 3},
            {"x": 1, "y": 1},
            {"x": 2, "y": 3},
        ],
    )

    layers = _normalize_layers_from_payload(payload)
    assert 1 in layers
    assert layers[1] == [
        {"x": 2, "y": 3, "asset_key": "wall_block"},
        {"x": 1, "y": 1, "asset_key": "wall_block"},
    ]

    walls = _derive_wall_cells(layers, width=20, height=20, spawn_x=1, spawn_y=1)
    assert walls == [{"x": 2, "y": 3}]


def test_collision_assets_are_rejected_on_non_collision_layers() -> None:
    payload = LevelSaveRequest(
        name="Invalid",
        width=20,
        height=20,
        layers={
            0: [LevelLayerCell(x=4, y=4, asset_key="wall_block")],
        },
    )

    try:
        _normalize_layers_from_payload(payload)
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail["code"] == "invalid_collision_layer"
    else:
        assert False, "Expected HTTPException for invalid collision layer placement"


def test_collision_derivation_uses_layer_one_collision_assets_only() -> None:
    payload = LevelSaveRequest(
        name="Layers",
        width=20,
        height=20,
        layers={
            0: [LevelLayerCell(x=1, y=1, asset_key="grass_tile")],
            1: [
                LevelLayerCell(x=5, y=5, asset_key="wall_block"),
                LevelLayerCell(x=7, y=8, asset_key="tree_oak"),
                LevelLayerCell(x=6, y=6, asset_key="grass_tile"),
            ],
            2: [LevelLayerCell(x=9, y=9, asset_key="cloud_soft")],
        },
    )

    layers = _normalize_layers_from_payload(payload)
    walls = _derive_wall_cells(layers, width=20, height=20, spawn_x=0, spawn_y=0)
    assert walls == [{"x": 5, "y": 5}, {"x": 7, "y": 8}]
