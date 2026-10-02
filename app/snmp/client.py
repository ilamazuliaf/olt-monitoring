import time
from typing import Dict, List, Tuple, Optional
import pysnmp.hlapi.asyncio as hl
from app.config import Config
from app.logger import get_logger


class SNMPClient:
    """SNMP Client supporting SNMP v1, v2c, and v3 queries."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
        self.snmp_engine = hl.SnmpEngine()

    def _get_auth_data(self):
        """Construct authentication data based on SNMP version."""
        version = str(self.config.olt_snmp_version).lower()
        if version == "1":
            return hl.CommunityData(self.config.olt_snmp_community, mpModel=0)
        elif version == "3":
            # Basic fallback placeholder for SNMPv3 if extended in future
            return hl.UsmUserData("usr-none-none")
        else:
            # Default to v2c
            return hl.CommunityData(self.config.olt_snmp_community, mpModel=1)

    async def _get_transport_target(self):
        """Create async UDP transport target with host, port, timeout, retries."""
        return await hl.UdpTransportTarget.create(
            (self.config.olt_host, self.config.olt_port),
            timeout=self.config.snmp_timeout,
            retries=self.config.snmp_retries
        )

    async def get(self, oid: str) -> Optional[str]:
        """Perform SNMP GET for a single OID."""
        if not oid or not oid.strip():
            return None

        clean_oid = oid.strip().lstrip(".")
        self.logger.debug(f"SNMP GET: {clean_oid}")

        try:
            auth_data = self._get_auth_data()
            transport_target = await self._get_transport_target()
            context_data = hl.ContextData()

            error_indication, error_status, error_index, var_binds = await hl.get_cmd(
                self.snmp_engine,
                auth_data,
                transport_target,
                context_data,
                hl.ObjectType(hl.ObjectIdentity(clean_oid))
            )

            if error_indication:
                self.logger.error(f"SNMP GET Error Indication for {clean_oid}: {error_indication}")
                return None

            if error_status:
                self.logger.error(
                    f"SNMP GET Error Status: {error_status.prettyPrint()} at {error_index and var_binds[int(error_index) - 1][0] or '?'}"
                )
                return None

            for var_bind in var_binds:
                val = var_bind[1]
                return val.prettyPrint()

            return None

        except Exception as e:
            self.logger.error(f"Exception during SNMP GET {clean_oid}: {e}")
            return None

    async def walk(self, oid: str) -> Dict[str, str]:
        """
        Perform SNMP WALK for an OID tree.
        Returns a dict mapping full OID string -> value string.
        """
        if not oid or not oid.strip():
            return {}

        clean_oid = oid.strip().lstrip(".")
        root_prefix = "." + clean_oid
        self.logger.debug(f"SNMP WALK: {clean_oid}")

        results: Dict[str, str] = {}

        try:
            auth_data = self._get_auth_data()
            transport_target = await self._get_transport_target()
            context_data = hl.ContextData()

            objects = hl.walk_cmd(
                self.snmp_engine,
                auth_data,
                transport_target,
                context_data,
                hl.ObjectType(hl.ObjectIdentity(clean_oid)),
                lexicographicMode=False
            )

            async for error_indication, error_status, error_index, var_binds in objects:
                if error_indication:
                    self.logger.error(f"SNMP WALK Error Indication: {error_indication}")
                    break

                if error_status:
                    self.logger.error(f"SNMP WALK Error Status: {error_status.prettyPrint()}")
                    break

                for var_bind in var_binds:
                    var_oid = "." + str(var_bind[0]).lstrip(".")
                    var_val = var_bind[1].prettyPrint()

                    # Stop if returned OID does not start with root_prefix
                    if not var_oid.startswith(root_prefix):
                        break

                    results[var_oid] = var_val

        except Exception as e:
            self.logger.error(f"Exception during SNMP WALK {clean_oid}: {e}")

        return results

    async def check_connection(self) -> Tuple[bool, str, float]:
        """
        Check connectivity to the OLT SNMP service.
        Returns (is_connected, message, response_time_ms).
        """
        start_time = time.time()
        # Query sysDescr (1.3.6.1.2.1.1.1.0) or custom OID
        target_oid = self.config.oid_ont_status or "1.3.6.1.2.1.1.1.0"
        
        try:
            auth_data = self._get_auth_data()
            transport_target = await self._get_transport_target()
            context_data = hl.ContextData()

            error_indication, error_status, error_index, var_binds = await hl.get_cmd(
                self.snmp_engine,
                auth_data,
                transport_target,
                context_data,
                hl.ObjectType(hl.ObjectIdentity(target_oid))
            )

            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            if error_indication:
                return False, f"SNMP Error: {error_indication}", elapsed_ms

            if error_status:
                return False, f"SNMP Error Status: {error_status.prettyPrint()}", elapsed_ms

            return True, "CONNECTED", elapsed_ms

        except Exception as e:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return False, f"Timeout / Failed: {e}", elapsed_ms

