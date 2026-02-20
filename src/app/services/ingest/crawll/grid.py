from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class BBox:
    north: float
    south: float
    east: float
    west: float


def generate_grid(target: BBox) -> list[BBox]:
    tile_lat_delta = 0.0145
    tile_lon_delta = 0.0172

    target_north = max(target.north, target.south)
    target_south = min(target.north, target.south)
    target_east = max(target.east, target.west)
    target_west = min(target.east, target.west)

    epsilon = 1e-9

    def snap_floor(value: float, delta: float) -> float:
        ratio = value / delta
        if abs(ratio - round(ratio)) < epsilon:
            ratio = round(ratio)
        return math.floor(ratio) * delta

    def snap_ceil(value: float, delta: float) -> float:
        ratio = value / delta
        if abs(ratio - round(ratio)) < epsilon:
            ratio = round(ratio)
        return math.ceil(ratio) * delta

    grid_south = snap_floor(target_south, tile_lat_delta)
    grid_west = snap_floor(target_west, tile_lon_delta)
    grid_north = snap_ceil(target_north, tile_lat_delta)
    grid_east = snap_ceil(target_east, tile_lon_delta)

    lat_span = grid_north - grid_south
    lon_span = grid_east - grid_west

    lat_steps = int(round(lat_span / tile_lat_delta)) or 1
    lon_steps = int(round(lon_span / tile_lon_delta)) or 1

    tiles: list[BBox] = []
    for i in range(lat_steps):
        for j in range(lon_steps):
            tile_south = grid_south + (i * tile_lat_delta)
            tile_west = grid_west + (j * tile_lon_delta)
            tile_north = tile_south + tile_lat_delta
            tile_east = tile_west + tile_lon_delta
            tiles.append(BBox(north=tile_north, south=tile_south, east=tile_east, west=tile_west))
    return tiles
