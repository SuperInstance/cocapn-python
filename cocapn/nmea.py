"""NMEA 0183 parsing — checksum, GGA, coordinates."""

from dataclasses import dataclass


@dataclass
class GGAData:
    latitude: float
    longitude: float
    fix_quality: int
    satellites: int
    hdop: float
    altitude: float


def verify_checksum(sentence: str) -> bool:
    if not sentence or sentence[0] != "$":
        return False
    calc = 0
    for ch in sentence[1:]:
        if ch == "*":
            break
        calc ^= ord(ch)
    else:
        return False
    try:
        stated = int(sentence.split("*")[1][:2], 16)
    except (ValueError, IndexError):
        return False
    return calc == stated


def parse_coordinate(raw: str, is_latitude: bool) -> float:
    if not raw:
        return 0.0
    val = float(raw)
    degrees = int(val / 100)
    minutes = val - degrees * 100
    return degrees + minutes / 60.0


def _field(sentence: str, n: int) -> str:
    parts = sentence.split(",")
    if n < len(parts):
        return parts[n]
    return ""


def parse_gga(sentence: str) -> GGAData:
    lat_raw = _field(sentence, 2)
    lat_dir = _field(sentence, 3)
    lon_raw = _field(sentence, 4)
    lon_dir = _field(sentence, 5)
    qual = _field(sentence, 6)
    sats = _field(sentence, 7)
    hdop = _field(sentence, 8)
    alt = _field(sentence, 9)

    lat = parse_coordinate(lat_raw, True)
    if lat_dir == "S":
        lat = -lat
    lon = parse_coordinate(lon_raw, False)
    if lon_dir == "W":
        lon = -lon

    return GGAData(
        latitude=lat,
        longitude=lon,
        fix_quality=int(qual) if qual else 0,
        satellites=int(sats) if sats else 0,
        hdop=float(hdop) if hdop else 0.0,
        altitude=float(alt) if alt else 0.0,
    )
