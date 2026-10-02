import os
import sys
from dataclasses import dataclass, field
from typing import Set, List, Optional
from dotenv import load_dotenv


def parse_int_list(val: str) -> Set[int]:
    """Parse comma-separated string into set of integers."""
    if not val or not val.strip():
        return set()
    result = set()
    for item in val.split(","):
        cleaned = item.strip()
        if cleaned:
            try:
                result.add(int(cleaned))
            except ValueError:
                pass
    return result


def parse_string_list(val: str, default: List[str]) -> List[str]:
    """Parse comma-separated string into list of strings."""
    if not val or not val.strip():
        return default
    return [item.strip() for item in val.split(",") if item.strip()]


@dataclass
class Config:
    telegram_bot_token: str
    telegram_allowed_chat_ids: Set[int] = field(default_factory=set)

    olt_name: str = "OLT-UTAMA"
    olt_host: str = "192.168.88.2"
    olt_port: int = 161

    olt_snmp_version: str = "2c"
    olt_snmp_community: str = "public"

    snmp_timeout: float = 5.0
    snmp_retries: int = 2

    olt_rx_power_threshold: float = -25.0
    olt_rx_power_scale: float = 10.0

    oid_ont_status: str = ""
    oid_ont_rx_power: str = ""
    oid_ont_tx_power: str = ""
    oid_ont_serial: str = ""
    oid_ont_vendor: str = ""
    oid_ont_model: str = ""
    oid_ont_name: str = ""

    ont_status_online_values: List[str] = field(default_factory=lambda: ["1"])
    ont_status_offline_values: List[str] = field(default_factory=lambda: ["2", "3", "4"])

    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    @classmethod
    def load(cls, env_path: Optional[str] = None) -> "Config":
        """Load configuration from environment or .env file."""
        if env_path:
            load_dotenv(dotenv_path=env_path, override=True)
        else:
            load_dotenv(override=True)

        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            print("ERROR: TELEGRAM_BOT_TOKEN belum dikonfigurasi.", file=sys.stderr)
            raise ValueError("ERROR: TELEGRAM_BOT_TOKEN belum dikonfigurasi.")

        chat_ids_str = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "")
        allowed_chat_ids = parse_int_list(chat_ids_str)

        olt_name = os.getenv("OLT_NAME", "OLT-UTAMA").strip()
        olt_host = os.getenv("OLT_HOST", "192.168.88.2").strip()

        try:
            olt_port = int(os.getenv("OLT_PORT", "161").strip())
        except ValueError:
            olt_port = 161

        olt_snmp_version = os.getenv("OLT_SNMP_VERSION", "2c").strip()
        olt_snmp_community = os.getenv("OLT_SNMP_COMMUNITY", "public").strip()

        try:
            snmp_timeout = float(os.getenv("SNMP_TIMEOUT", "5").strip())
        except ValueError:
            snmp_timeout = 5.0

        try:
            snmp_retries = int(os.getenv("SNMP_RETRIES", "2").strip())
        except ValueError:
            snmp_retries = 2

        try:
            olt_rx_power_threshold = float(os.getenv("OLT_RX_POWER_THRESHOLD", "-25").strip())
        except ValueError:
            olt_rx_power_threshold = -25.0

        try:
            olt_rx_power_scale = float(os.getenv("OLT_RX_POWER_SCALE", "10").strip())
            if olt_rx_power_scale == 0:
                olt_rx_power_scale = 1.0
        except ValueError:
            olt_rx_power_scale = 10.0

        oid_ont_status = os.getenv("OID_ONT_STATUS", "").strip()
        oid_ont_rx_power = os.getenv("OID_ONT_RX_POWER", "").strip()
        oid_ont_tx_power = os.getenv("OID_ONT_TX_POWER", "").strip()
        oid_ont_serial = os.getenv("OID_ONT_SERIAL", "").strip()
        oid_ont_vendor = os.getenv("OID_ONT_VENDOR", "").strip()
        oid_ont_model = os.getenv("OID_ONT_MODEL", "").strip()
        oid_ont_name = os.getenv("OID_ONT_NAME", "").strip()

        online_raw = os.getenv("ONT_STATUS_ONLINE_VALUES", "1")
        offline_raw = os.getenv("ONT_STATUS_OFFLINE_VALUES", "2,3,4")

        ont_status_online_values = parse_string_list(online_raw, ["1"])
        ont_status_offline_values = parse_string_list(offline_raw, ["2", "3", "4"])

        log_level = os.getenv("LOG_LEVEL", "INFO").strip()
        log_file = os.getenv("LOG_FILE", "logs/app.log").strip()

        return cls(
            telegram_bot_token=token,
            telegram_allowed_chat_ids=allowed_chat_ids,
            olt_name=olt_name,
            olt_host=olt_host,
            olt_port=olt_port,
            olt_snmp_version=olt_snmp_version,
            olt_snmp_community=olt_snmp_community,
            snmp_timeout=snmp_timeout,
            snmp_retries=snmp_retries,
            olt_rx_power_threshold=olt_rx_power_threshold,
            olt_rx_power_scale=olt_rx_power_scale,
            oid_ont_status=oid_ont_status,
            oid_ont_rx_power=oid_ont_rx_power,
            oid_ont_tx_power=oid_ont_tx_power,
            oid_ont_serial=oid_ont_serial,
            oid_ont_vendor=oid_ont_vendor,
            oid_ont_model=oid_ont_model,
            oid_ont_name=oid_ont_name,
            ont_status_online_values=ont_status_online_values,
            ont_status_offline_values=ont_status_offline_values,
            log_level=log_level,
            log_file=log_file,
        )
