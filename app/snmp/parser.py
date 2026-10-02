import re
from typing import Dict, List, Optional, Tuple
from app.olt.models import ONT


def extract_oid_suffix(full_oid: str, root_oid: str) -> str:
    """Extract the suffix part of a full OID after the root OID."""
    if not full_oid or not root_oid:
        return ""
    clean_full = "." + full_oid.strip().lstrip(".")
    clean_root = "." + root_oid.strip().lstrip(".")
    if clean_full.startswith(clean_root):
        suffix = clean_full[len(clean_root):].lstrip(".")
        return suffix
    return clean_full.lstrip(".")


def parse_pon_and_ont_id(suffix: str) -> Tuple[str, str, str]:
    """
    Parse OID suffix into (slot, pon, ont_id).
    Supports multi-level index suffixes:
    - single index "5" -> ("1", "1/1/1", "5")
    - 2 parts "2.5" -> ("1", "1/1/2", "5")
    - 3 parts "1.2.5" -> ("1", "1/1/2", "5")
    - 4 parts "1.1.2.5" -> ("1", "1/1/2", "5")
    """
    parts = [p for p in suffix.split(".") if p]
    if not parts:
        return ("1", "1/1/1", "0")

    if len(parts) == 1:
        return ("1", "1/1/1", parts[0])
    elif len(parts) == 2:
        return ("1", f"1/1/{parts[0]}", parts[1])
    elif len(parts) == 3:
        return (parts[0], f"1/{parts[0]}/{parts[1]}", parts[2])
    else:
        # 4 or more parts
        slot = parts[0]
        rack = parts[0]
        shelf = parts[1]
        port = parts[2]
        ont_id = parts[3]
        return (slot, f"{shelf}/{port}", ont_id) if len(parts) == 4 else (slot, f"{parts[0]}/{parts[1]}/{parts[2]}", parts[-1])


def parse_optical_power(val_str: Optional[str], scale: float = 10.0) -> Optional[float]:
    """
    Convert raw SNMP optical power reading to dBm float.
    Handles raw int scaling (e.g. -253 / 10 = -25.3 dBm).
    Handles 16-bit signed integer wraps (e.g. 65283 -> -253).
    Handles invalid/sentinel values (e.g. 65535, 2147483647, "N/A", "--").
    """
    if val_str is None:
        return None

    cleaned = str(val_str).strip()
    if not cleaned or cleaned.upper() in ("N/A", "NONE", "UNKNOWN", "--"):
        return None

    # Handle hex strings or special prefixes if any
    if cleaned.startswith("0x") or cleaned.startswith("0X"):
        try:
            raw_num = int(cleaned, 16)
        except ValueError:
            return None
    else:
        # Extract numeric value
        match = re.search(r'[-+]?\d+(?:\.\d+)?', cleaned)
        if not match:
            return None
        try:
            raw_num = float(match.group(0))
        except ValueError:
            return None

    # Check for common sentinel error codes for invalid optical power
    if raw_num in (65535, 65535.0, 2147483647, 2147483647.0, -999, -999.0):
        return None

    # If 16-bit unsigned value that represents a negative number (e.g. > 32767)
    if 32767 < raw_num <= 65534:
        raw_num = raw_num - 65536

    # Scale conversion
    if scale and scale != 1.0 and abs(raw_num) > 100:
        power = raw_num / scale
    else:
        power = raw_num

    return round(power, 2)


def map_status(val_str: Optional[str], online_vals: List[str], offline_vals: List[str]) -> str:
    """
    Map raw status value string to 'online' or 'offline'.
    """
    if val_str is None:
        return "offline"

    cleaned = str(val_str).strip().lower()

    # Normalize online/offline lists
    norm_online = [str(v).strip().lower() for v in online_vals]
    norm_offline = [str(v).strip().lower() for v in offline_vals]

    if cleaned in norm_online:
        return "online"
    if cleaned in norm_offline:
        return "offline"

    # Default heuristic if not explicitly in online list
    if cleaned in ("1", "up", "online", "active", "working", "enable"):
        return "online"
    return "offline"


def parse_ont_table(
    status_walk: Dict[str, str],
    status_root_oid: str,
    online_vals: List[str],
    offline_vals: List[str],
    olt_name: str = "OLT-UTAMA",
    serial_walk: Optional[Dict[str, str]] = None,
    serial_root_oid: str = "",
    name_walk: Optional[Dict[str, str]] = None,
    name_root_oid: str = "",
    rx_walk: Optional[Dict[str, str]] = None,
    rx_root_oid: str = "",
    tx_walk: Optional[Dict[str, str]] = None,
    tx_root_oid: str = "",
    rx_scale: float = 10.0
) -> List[ONT]:
    """
    Parse multiple SNMP WALK result dicts into a list of ONT domain models.
    """
    onts_map: Dict[str, ONT] = {}

    # 1. Parse Status Walk
    for full_oid, raw_val in status_walk.items():
        suffix = extract_oid_suffix(full_oid, status_root_oid)
        if not suffix:
            continue

        slot, pon, ont_id = parse_pon_and_ont_id(suffix)
        status = map_status(raw_val, online_vals, offline_vals)

        onts_map[suffix] = ONT(
            olt=olt_name,
            slot=slot,
            pon=pon,
            ont_id=ont_id,
            status=status,
            serial_number="-",
            name="-"
        )

    # 2. Parse Serial Numbers
    if serial_walk and serial_root_oid:
        for full_oid, raw_val in serial_walk.items():
            suffix = extract_oid_suffix(full_oid, serial_root_oid)
            if suffix in onts_map:
                onts_map[suffix].serial_number = str(raw_val).strip() or "-"

    # 3. Parse ONT Names
    if name_walk and name_root_oid:
        for full_oid, raw_val in name_walk.items():
            suffix = extract_oid_suffix(full_oid, name_root_oid)
            if suffix in onts_map:
                onts_map[suffix].name = str(raw_val).strip() or "-"

    # 4. Parse RX Power
    if rx_walk and rx_root_oid:
        for full_oid, raw_val in rx_walk.items():
            suffix = extract_oid_suffix(full_oid, rx_root_oid)
            if suffix in onts_map:
                onts_map[suffix].rx_power = parse_optical_power(raw_val, rx_scale)

    # 5. Parse TX Power
    if tx_walk and tx_root_oid:
        for full_oid, raw_val in tx_walk.items():
            suffix = extract_oid_suffix(full_oid, tx_root_oid)
            if suffix in onts_map:
                onts_map[suffix].tx_power = parse_optical_power(raw_val, rx_scale)

    ont_list = list(onts_map.values())
    # Sort according to Section 23: OLT -> Slot -> PON -> ONT ID
    ont_list.sort(key=lambda ont: ont.sort_key())
    return ont_list
