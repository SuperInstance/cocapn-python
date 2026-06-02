"""Bathymetric database with nearest-neighbor lookup and GeoJSON export."""

from dataclasses import dataclass, field
import json
import math


@dataclass
class BathyPoint:
    lat: float
    lon: float
    depth: float


class BathyDatabase:
    def __init__(self):
        self.points: list[BathyPoint] = []

    def record(self, lat: float, lon: float, depth: float):
        self.points.append(BathyPoint(lat, lon, depth))

    def depth_at(self, lat: float, lon: float) -> float | None:
        if not self.points:
            return None
        best = None
        best_dist = float("inf")
        for p in self.points:
            d = (p.lat - lat) ** 2 + (p.lon - lon) ** 2
            if d < best_dist:
                best_dist = d
                best = p.depth
        return best

    def to_geojson(self) -> dict:
        features = []
        for p in self.points:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [p.lon, p.lat]},
                "properties": {"depth": p.depth},
            })
        return {"type": "FeatureCollection", "features": features}

    def to_geojson_str(self) -> str:
        return json.dumps(self.to_geojson(), indent=2)

    def from_csv(self, path: str):
        with open(path) as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 3:
                    try:
                        self.record(float(parts[0]), float(parts[1]), float(parts[2]))
                    except ValueError:
                        continue
