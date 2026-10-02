import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.config import Config
from app.olt.models import ONT
from app.olt.monitor import OLTMonitor


@pytest.fixture
def dummy_config():
    return Config(
        telegram_bot_token="test:token",
        olt_name="OLT-TEST",
        olt_host="127.0.0.1",
        olt_rx_power_threshold=-25.0,
        oid_ont_status="1.3.6.1.4.1.3902.1.1",
        oid_ont_serial="1.3.6.1.4.1.3902.2.1",
        oid_ont_rx_power="1.3.6.1.4.1.3902.3.1"
    )


def test_monitor_get_offline_onts(dummy_config):
    async def run_test():
        mock_snmp = MagicMock()
        mock_snmp.walk = AsyncMock()

        # Mock walks
        mock_snmp.walk.side_effect = [
            # status_walk: ONT 1 online (1), ONT 2 offline (2), ONT 3 offline (2)
            {".1.3.6.1.4.1.3902.1.1.1": "1", ".1.3.6.1.4.1.3902.1.1.2": "2", ".1.3.6.1.4.1.3902.1.1.3": "2"},
            # serial_walk
            {".1.3.6.1.4.1.3902.2.1.1": "SN1", ".1.3.6.1.4.1.3902.2.1.2": "SN2", ".1.3.6.1.4.1.3902.2.1.3": "SN3"},
            # rx_walk
            {".1.3.6.1.4.1.3902.3.1.1": "-200", ".1.3.6.1.4.1.3902.3.1.2": "-260", ".1.3.6.1.4.1.3902.3.1.3": "-240"}
        ]

        monitor = OLTMonitor(dummy_config, mock_snmp)
        offline_onts = await monitor.get_offline_onts()

        # AC-03, AC-04: returns ONLY offline ONTs
        assert len(offline_onts) == 2
        assert all(ont.is_offline for ont in offline_onts)
        assert [ont.ont_id for ont in offline_onts] == ["2", "3"]

    asyncio.run(run_test())


def test_monitor_get_high_attenuation_onts(dummy_config):
    async def run_test():
        mock_snmp = MagicMock()
        mock_snmp.walk = AsyncMock()

        mock_snmp.walk.side_effect = [
            # status_walk: all online
            {".1.3.6.1.4.1.3902.1.1.1": "1", ".1.3.6.1.4.1.3902.1.1.2": "1", ".1.3.6.1.4.1.3902.1.1.3": "1"},
            # serial_walk
            {".1.3.6.1.4.1.3902.2.1.1": "SN1", ".1.3.6.1.4.1.3902.2.1.2": "SN2", ".1.3.6.1.4.1.3902.2.1.3": "SN3"},
            # rx_walk: -21.0 dBm (normal), -26.0 dBm (exceeds threshold <= -25), -29.5 dBm (exceeds threshold <= -25)
            {".1.3.6.1.4.1.3902.3.1.1": "-210", ".1.3.6.1.4.1.3902.3.1.2": "-260", ".1.3.6.1.4.1.3902.3.1.3": "-295"}
        ]

        monitor = OLTMonitor(dummy_config, mock_snmp)
        high_att_onts = await monitor.get_high_attenuation_onts()

        # AC-06: returns ONLY ONTs with rx_power <= threshold (-25.0)
        assert len(high_att_onts) == 2
        assert [ont.ont_id for ont in high_att_onts] == ["2", "3"]
        assert high_att_onts[0].rx_power == -26.0
        assert high_att_onts[1].rx_power == -29.5

    asyncio.run(run_test())


def test_ont_sorting_order():
    ont1 = ONT(olt="OLT-UTAMA", slot="1", pon="1/1/2", ont_id="10")
    ont2 = ONT(olt="OLT-UTAMA", slot="1", pon="1/1/1", ont_id="3")
    ont3 = ONT(olt="OLT-UTAMA", slot="1", pon="1/1/2", ont_id="2")

    ont_list = [ont1, ont2, ont3]
    ont_list.sort(key=lambda x: x.sort_key())

    # Order expected: PON 1/1/1 ONT 3 -> PON 1/1/2 ONT 2 -> PON 1/1/2 ONT 10
    assert [ont.ont_id for ont in ont_list] == ["3", "2", "10"]
