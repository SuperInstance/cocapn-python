# cocapn-python

CoCapn in Python — the data exploration layer. NumPy for signal processing, Matplotlib for bathy charts, Jupyter for interactive analysis.

## Why Python?

Python is where the researcher meets the keeper's data. The ESP32 collects depth readings. The Python notebook plots the contour map. The deadband runs in Rust on bare metal, but the deadband's history gets analyzed in Python.

## Installation

```bash
pip install cocapn
```

## Quick Start

```python
from cocapn import Deadband, Direction, State, PIDController, simulate_heading_hold

# Deadband check
db = Deadband(100.0, 0.05)  # 5% tolerance
print(db.check(97.0))   # State.NORMAL
print(db.check(106.0))  # State.EXCEEDED

# Conservation deadband — only flag decreases
cons = Deadband(100.0, 0.10, Direction.BELOW_ONLY)
print(cons.check(115.0))  # State.NORMAL (increase is fine)
print(cons.check(85.0))   # State.EXCEEDED (decrease!)

# PID heading simulation
history = simulate_heading_hold(initial=0.0, target=90.0)
print(f"Converged in {len(history)} steps")
```

## What's Included

| Module | Purpose |
|--------|---------|
| `device` | Tier/Capability enums, Device dataclass |
| `deadband` | Deadband + DeadbandMonitor (multi-deadband tracking) |
| `autopilot` | PID controller + heading hold simulation |
| `escalation` | Tier escalation chain |
| `nmea` | NMEA 0183 checksum, GGA parser, coordinate conversion |
| `bathy` | Bathymetric database with GeoJSON export |

## The DeadbandMonitor

Track multiple deadbands simultaneously:

```python
from cocapn import DeadbandMonitor, Deadband, Direction

mon = DeadbandMonitor({
    "heading": Deadband(90.0, 0.05),
    "speed": Deadband(10.0, 0.10, Direction.BELOW_ONLY),
    "depth": Deadband(50.0, 0.15),
})

values = {"heading": 92.0, "speed": 8.5, "depth": 48.0}
triggered = mon.triggered(values)
# ["speed"] — only speed exceeded
```

## Bathymetry + GeoJSON

```python
from cocapn import BathyDatabase

db = BathyDatabase()
db.record(60.0, -147.0, 120.5)
db.record(60.1, -147.1, 85.3)

print(db.depth_at(60.05, -147.05))  # nearest neighbor
print(db.to_geojson_str())  # GeoJSON FeatureCollection
```

## License

MIT
