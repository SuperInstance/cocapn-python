"""Comprehensive test suite for cocapn-python."""

import math
import pytest
from cocapn import (
    Tier, Capability, Device,
    Direction, State, Deadband, DeadbandMonitor,
    PIDController, simulate_heading_hold,
    EscalationChain,
    GGAData, verify_checksum, parse_gga, parse_coordinate,
    BathyPoint, BathyDatabase,
)


# ---- Device ----

class TestDevice:
    def test_capability_check(self):
        esp32 = Device(1, "helm", Tier.REFLEX, Capability.SENSE | Capability.ACT)
        assert esp32.can(Capability.SENSE)
        assert esp32.can(Capability.ACT)
        assert not esp32.can(Capability.PREDICT)

    def test_offline_device(self):
        dead = Device(2, "dead", Tier.BACKBONE, Capability.SENSE, online=False)
        assert not dead.can(Capability.SENSE)

    def test_tier_ordering(self):
        assert Tier.REFLEX.value < Tier.BACKBONE.value < Tier.CORTEX.value < Tier.CLOUD.value


# ---- Deadband ----

class TestDeadband:
    def test_at_center(self):
        db = Deadband(100.0, 0.05)
        assert db.check(100.0) == State.NORMAL

    def test_within_tolerance(self):
        db = Deadband(100.0, 0.05)
        assert db.check(97.0) == State.NORMAL

    def test_exceeded(self):
        db = Deadband(100.0, 0.05)
        assert db.check(106.0) == State.EXCEEDED

    def test_approaching(self):
        db = Deadband(100.0, 0.10)
        assert db.check(91.0) == State.APPROACHING
        assert db.check(109.0) == State.APPROACHING

    def test_one_sided_below(self):
        cons = Deadband(100.0, 0.10, Direction.BELOW_ONLY)
        assert cons.check(115.0) == State.NORMAL
        assert cons.check(85.0) == State.EXCEEDED

    def test_one_sided_above(self):
        over = Deadband(100.0, 0.10, Direction.ABOVE_ONLY)
        assert over.check(85.0) == State.NORMAL
        assert over.check(115.0) == State.EXCEEDED

    def test_zero_center_absolute(self):
        db = Deadband(0.0, 5.0)
        assert db.check(3.0) == State.NORMAL
        assert db.check(6.0) == State.EXCEEDED

    def test_monitor(self):
        mon = DeadbandMonitor({
            "heading": Deadband(90.0, 0.05),
            "speed": Deadband(10.0, 0.10, Direction.BELOW_ONLY),
        })
        results = mon.check_all({"heading": 95.0, "speed": 8.0})
        assert results["heading"] == State.EXCEEDED
        assert results["speed"] == State.EXCEEDED

        triggered = mon.triggered({"heading": 95.0, "speed": 8.0})
        assert "heading" in triggered
        assert "speed" in triggered


# ---- Autopilot ----

class TestAutopilot:
    def test_heading_error(self):
        assert abs(PIDController._heading_error(0, 90) - 90) < 0.01
        assert abs(PIDController._heading_error(350, 10) - 20) < 0.01
        assert abs(PIDController._heading_error(10, 350) - (-20)) < 0.01

    def test_convergence(self):
        history = simulate_heading_hold(initial=0.0, target=90.0)
        assert history[-1]["on_course"]

    def test_wraparound(self):
        history = simulate_heading_hold(initial=350.0, target=10.0)
        assert history[-1]["on_course"]

    def test_anti_windup(self):
        pid = PIDController()
        pid.reset()
        for _ in range(500):
            pid.update(0.0, 180.0, 0.1)
        assert abs(pid.integral) <= pid.max_rudder

    def test_rudder_clamped(self):
        pid = PIDController()
        _, _, _ = pid.update(0.0, 180.0, 0.1)
        # After one step, command should be within limits
        cmd, _, _ = pid.update(0.0, 180.0, 0.1)
        assert abs(cmd) <= pid.max_rudder


# ---- Escalation ----

class TestEscalation:
    def test_full_escalation(self):
        chain = EscalationChain()
        assert chain.escalate() == Tier.BACKBONE
        assert chain.escalate() == Tier.CORTEX
        assert chain.escalate() == Tier.CLOUD
        assert chain.escalate() == Tier.CLOUD  # capped
        assert chain.escalation_count == 3

    def test_deescalation(self):
        chain = EscalationChain(current_tier=Tier.CLOUD)
        assert chain.deescalate() == Tier.CORTEX
        assert chain.deescalate() == Tier.BACKBONE
        assert chain.deescalate() == Tier.REFLEX
        assert chain.deescalate() == Tier.REFLEX  # floored


# ---- NMEA ----

class TestNMEA:
    GGA = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"

    def test_checksum_valid(self):
        assert verify_checksum(self.GGA)

    def test_checksum_invalid(self):
        bad = self.GGA.replace("*47", "*00")
        assert not verify_checksum(bad)

    def test_parse_gga(self):
        fix = parse_gga(self.GGA)
        assert 48.0 < fix.latitude < 49.0
        assert 11.0 < fix.longitude < 12.0
        assert fix.fix_quality == 1
        assert fix.satellites == 8
        assert abs(fix.hdop - 0.9) < 0.1
        assert abs(fix.altitude - 545.4) < 1.0

    def test_parse_coordinate_lat(self):
        lat = parse_coordinate("4807.038", True)
        assert 48.11 < lat < 48.12

    def test_parse_coordinate_lon(self):
        lon = parse_coordinate("01131.000", False)
        assert 11.51 < lon < 11.52


# ---- Bathy ----

class TestBathy:
    def test_record_and_lookup(self):
        db = BathyDatabase()
        db.record(60.0, -147.0, 120.5)
        db.record(60.1, -147.1, 85.3)
        assert abs(db.depth_at(60.0, -147.0) - 120.5) < 0.01
        assert abs(db.depth_at(60.1, -147.1) - 85.3) < 0.01

    def test_nearest_neighbor(self):
        db = BathyDatabase()
        db.record(60.0, -147.0, 100.0)
        db.record(61.0, -148.0, 200.0)
        assert abs(db.depth_at(60.4, -147.4) - 100.0) < 0.01

    def test_empty_db(self):
        db = BathyDatabase()
        assert db.depth_at(0, 0) is None

    def test_geojson(self):
        db = BathyDatabase()
        db.record(60.0, -147.0, 100.0)
        gj = db.to_geojson()
        assert gj["type"] == "FeatureCollection"
        assert len(gj["features"]) == 1
        assert gj["features"][0]["properties"]["depth"] == 100.0
