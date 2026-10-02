from typing import List, Tuple
from app.config import Config
from app.logger import get_logger
from app.olt.models import ONT
from app.snmp.client import SNMPClient
from app.snmp.parser import parse_ont_table


class OLTMonitor:
    """High-level monitoring manager for OLT ONT statuses and signal levels."""

    def __init__(self, config: Config, snmp_client: SNMPClient):
        self.config = config
        self.snmp_client = snmp_client
        self.logger = get_logger()

    async def check_connection(self) -> Tuple[bool, str, float]:
        """Check connection to OLT."""
        return await self.snmp_client.check_connection()

    async def get_all_onts(self) -> List[ONT]:
        """Fetch all ONTs from OLT via SNMP WALK operations."""
        status_oid = self.config.oid_ont_status
        if not status_oid:
            self.logger.warning("OID_ONT_STATUS belum dikonfigurasi.")
            return []

        # Walk status tree
        status_walk = await self.snmp_client.walk(status_oid)
        if not status_walk:
            self.logger.warning(f"SNMP walk return kosong untuk OID_ONT_STATUS: {status_oid}")
            return []

        # Optional walks for extra fields
        serial_walk = {}
        if self.config.oid_ont_serial:
            serial_walk = await self.snmp_client.walk(self.config.oid_ont_serial)

        vendor_walk = {}
        if self.config.oid_ont_vendor:
            vendor_walk = await self.snmp_client.walk(self.config.oid_ont_vendor)

        model_walk = {}
        if self.config.oid_ont_model:
            model_walk = await self.snmp_client.walk(self.config.oid_ont_model)

        name_walk = {}
        if self.config.oid_ont_name:
            name_walk = await self.snmp_client.walk(self.config.oid_ont_name)

        rx_walk = {}
        if self.config.oid_ont_rx_power:
            rx_walk = await self.snmp_client.walk(self.config.oid_ont_rx_power)

        tx_walk = {}
        if self.config.oid_ont_tx_power:
            tx_walk = await self.snmp_client.walk(self.config.oid_ont_tx_power)

        onts = parse_ont_table(
            status_walk=status_walk,
            status_root_oid=status_oid,
            online_vals=self.config.ont_status_online_values,
            offline_vals=self.config.ont_status_offline_values,
            olt_name=self.config.olt_name,
            serial_walk=serial_walk,
            serial_root_oid=self.config.oid_ont_serial,
            vendor_walk=vendor_walk,
            vendor_root_oid=self.config.oid_ont_vendor,
            model_walk=model_walk,
            model_root_oid=self.config.oid_ont_model,
            name_walk=name_walk,
            name_root_oid=self.config.oid_ont_name,
            rx_walk=rx_walk,
            rx_root_oid=self.config.oid_ont_rx_power,
            tx_walk=tx_walk,
            tx_root_oid=self.config.oid_ont_tx_power,
            rx_scale=self.config.olt_rx_power_scale
        )

        return onts

    async def get_ont_status(self) -> List[ONT]:
        """Get list of all ONTs with their statuses."""
        return await self.get_all_onts()

    async def get_offline_onts(self) -> List[ONT]:
        """
        Get list of ONTs that are currently OFFLINE.
        AC-03, AC-04: Returns ONLY offline ONTs, sorted by OLT -> Slot -> PON -> ONT ID.
        """
        all_onts = await self.get_all_onts()
        offline_onts = [ont for ont in all_onts if ont.is_offline]
        offline_onts.sort(key=lambda ont: ont.sort_key())
        self.logger.info(f"Ditemukan {len(offline_onts)} ONT offline dari total {len(all_onts)} ONT.")
        return offline_onts

    async def get_ont_optical_power(self) -> List[ONT]:
        """Get list of ONTs with optical power values."""
        all_onts = await self.get_all_onts()
        return [ont for ont in all_onts if ont.rx_power is not None]

    async def get_high_attenuation_onts(self) -> List[ONT]:
        """
        Get list of ONTs with optical RX power exceeding threshold (rx_power <= threshold).
        AC-06: Returns ONLY ONTs with rx_power <= threshold.
        """
        all_onts = await self.get_all_onts()
        threshold = self.config.olt_rx_power_threshold
        high_attenuation_onts = [
            ont for ont in all_onts
            if ont.rx_power is not None and ont.rx_power <= threshold
        ]
        high_attenuation_onts.sort(key=lambda ont: ont.sort_key())
        self.logger.info(
            f"Ditemukan {len(high_attenuation_onts)} ONT dengan redaman tinggi (<= {threshold} dBm)."
        )
        return high_attenuation_onts
