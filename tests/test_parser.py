import pytest
from app.snmp.parser import (
    extract_oid_suffix,
    parse_pon_and_ont_id,
    parse_optical_power,
    map_status,
    parse_ont_table
)


def test_extract_oid_suffix():
    assert extract_oid_suffix("1.3.6.1.4.1.3902.1012.3.28.1.1.3.1.2.5", "1.3.6.1.4.1.3902.1012.3.28.1.1.3") == "1.2.5"
    assert extract_oid_suffix(".1.3.6.1.4.1.3902.1.2.5", "1.3.6.1.4.1.3902") == "1.2.5"


def test_parse_pon_and_ont_id():
    assert parse_pon_and_ont_id("5") == ("1", "1/1/1", "5")
    assert parse_pon_and_ont_id("2.5") == ("1", "1/1/2", "5")
    assert parse_pon_and_ont_id("1.2.5") == ("1", "1/1/2", "5")
    assert parse_pon_and_ont_id("1.1.2.5") == ("1", "1/2", "5")
    # HSGQ 32-bit packed int 16777473 (0x01000101 -> slot 1, pon 1, ont 1)
    assert parse_pon_and_ont_id("16777473") == ("1", "1/1/1", "1")
    assert parse_pon_and_ont_id("16777729") == ("1", "1/1/2", "1")


def test_parse_hsgq_ont_table():
    # Test HSGQ OLT private MIB data structure
    status_walk = {
        "1.3.6.1.4.1.50224.3.3.2.1.8.16777473": "INTEGER: 1",
        "1.3.6.1.4.1.50224.3.3.2.1.8.16777474": "INTEGER: 1",
        "1.3.6.1.4.1.50224.3.3.2.1.8.16777510": "INTEGER: 2",  # Offline
    }
    name_walk = {
        "1.3.6.1.4.1.50224.3.3.2.1.2.16777473": 'STRING: "SUBAIDI"',
        "1.3.6.1.4.1.50224.3.3.2.1.2.16777474": 'STRING: "TOLAK"',
        "1.3.6.1.4.1.50224.3.3.2.1.2.16777510": 'STRING: "AMIR"',
    }
    rx_walk = {
        "1.3.6.1.4.1.50224.3.3.3.1.4.16777473.0.0": "INTEGER: -2455",
        "1.3.6.1.4.1.50224.3.3.3.1.4.16777474.0.0": "INTEGER: -2958",
    }

    onts = parse_ont_table(
        status_walk=status_walk,
        status_root_oid="1.3.6.1.4.1.50224.3.3.2.1.8",
        online_vals=["1"],
        offline_vals=["2"],
        olt_name="HSGQ-OLT",
        name_walk=name_walk,
        name_root_oid="1.3.6.1.4.1.50224.3.3.2.1.2",
        rx_walk=rx_walk,
        rx_root_oid="1.3.6.1.4.1.50224.3.3.3.1.4",
        rx_scale=100.0
    )

    assert len(onts) == 3
    assert onts[0].ont_id == "1"
    assert onts[0].name == "SUBAIDI"
    assert onts[0].rx_power == -24.55

    assert onts[1].ont_id == "2"
    assert onts[1].name == "TOLAK"
    assert onts[1].rx_power == -29.58

    assert onts[2].status == "offline"
    assert onts[2].name == "AMIR"
    assert onts[2].rx_power is None


def test_parse_optical_power():
    # Scaled integer (-253 / 10 = -25.3)
    assert parse_optical_power("-253", scale=10.0) == -25.3
    assert parse_optical_power("-2741", scale=100.0) == -27.41
    # Float string
    assert parse_optical_power("-24.50 dBm", scale=10.0) == -24.5
    # Sentinel error code 65535
    assert parse_optical_power("65535", scale=10.0) is None
    # Empty / Invalid
    assert parse_optical_power("N/A") is None
    assert parse_optical_power(None) is None


def test_map_status():
    online_vals = ["1", "up"]
    offline_vals = ["2", "3", "down"]

    assert map_status("1", online_vals, offline_vals) == "online"
    assert map_status("UP", online_vals, offline_vals) == "online"
    assert map_status("2", online_vals, offline_vals) == "offline"
    assert map_status("down", online_vals, offline_vals) == "offline"
    assert map_status("unknown", online_vals, offline_vals) == "offline"


def test_parse_ont_table():
    status_walk = {
        ".1.3.6.1.4.1.3902.1.1.1": "1",
        ".1.3.6.1.4.1.3902.1.1.2": "2",
        ".1.3.6.1.4.1.3902.1.1.3": "1"
    }
    serial_walk = {
        ".1.3.6.1.4.1.3902.2.1.1": "ZTEG1111",
        ".1.3.6.1.4.1.3902.2.1.2": "ZTEG2222",
        ".1.3.6.1.4.1.3902.2.1.3": "ZTEG3333"
    }
    rx_walk = {
        ".1.3.6.1.4.1.3902.3.1.1": "-210",
        ".1.3.6.1.4.1.3902.3.1.2": "-280",
        ".1.3.6.1.4.1.3902.3.1.3": "-260"
    }

    onts = parse_ont_table(
        status_walk=status_walk,
        status_root_oid="1.3.6.1.4.1.3902.1.1",
        online_vals=["1"],
        offline_vals=["2"],
        olt_name="OLT-UTAMA",
        serial_walk=serial_walk,
        serial_root_oid="1.3.6.1.4.1.3902.2.1",
        rx_walk=rx_walk,
        rx_root_oid="1.3.6.1.4.1.3902.3.1",
        rx_scale=10.0
    )

    assert len(onts) == 3
    assert onts[0].ont_id == "1"
    assert onts[0].status == "online"
    assert onts[0].rx_power == -21.0
    assert onts[1].ont_id == "2"
    assert onts[1].status == "offline"
    assert onts[1].rx_power == -28.0
