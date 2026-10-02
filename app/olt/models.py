import re
from dataclasses import dataclass
from typing import Optional, Tuple, List


def parse_numeric_parts(s: str) -> List[Tuple[int, str]]:
    """Helper to extract numbers and strings for natural sorting."""
    parts = re.split(r'(\d+)', str(s))
    result = []
    for part in parts:
        if part.isdigit():
            result.append((int(part), ""))
        else:
            result.append((-1, part))
    return result


@dataclass
class ONT:
    olt: str = ""
    slot: str = ""
    pon: str = ""
    ont_id: str = ""
    serial_number: str = ""
    vendor: str = ""
    model: str = ""
    name: str = ""
    status: str = "offline"  # "online" or "offline"
    rx_power: Optional[float] = None
    tx_power: Optional[float] = None

    @property
    def display_model(self) -> str:
        v = (self.vendor or "").strip()
        m = (self.model or "").strip()
        if v and m:
            return f"{v} {m}"
        if v:
            return v
        if m:
            return m
        return self.serial_number or "-"

    @property
    def is_online(self) -> bool:
        return self.status.lower() == "online"

    @property
    def is_offline(self) -> bool:
        return self.status.lower() == "offline"

    def sort_key(self) -> Tuple:
        """
        Sort key for ordering: OLT -> Slot -> PON -> ONT ID.
        Uses natural sorting so 2 comes before 10.
        """
        olt_key = self.olt or ""
        slot_key = parse_numeric_parts(self.slot or "")
        pon_key = parse_numeric_parts(self.pon or "")
        ont_id_key = parse_numeric_parts(self.ont_id or "")
        return (olt_key, slot_key, pon_key, ont_id_key)
