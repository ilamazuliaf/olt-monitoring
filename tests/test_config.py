import os
import pytest
from app.config import Config, parse_int_list, parse_string_list


def test_parse_int_list():
    assert parse_int_list("123,456,789") == {123, 456, 789}
    assert parse_int_list("123, invalid, 789 ") == {123, 789}
    assert parse_int_list("") == set()


def test_parse_string_list():
    assert parse_string_list("1, 2, 3", ["1"]) == ["1", "2", "3"]
    assert parse_string_list("", ["default"]) == ["default"]


def test_config_missing_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN belum dikonfigurasi"):
        Config.load()


def test_config_valid_loading(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57")
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "111,222")
    monkeypatch.setenv("OLT_NAME", "OLT-TEST")
    monkeypatch.setenv("OLT_RX_POWER_THRESHOLD", "-27.5")
    monkeypatch.setenv("OLT_RX_POWER_SCALE", "10")
    monkeypatch.setenv("ONT_STATUS_ONLINE_VALUES", "1,up")
    monkeypatch.setenv("ONT_STATUS_OFFLINE_VALUES", "2,3,down")

    cfg = Config.load()
    assert cfg.telegram_bot_token == "123456:ABC-DEF1234ghIkl-zyx57"
    assert cfg.telegram_allowed_chat_ids == {111, 222}
    assert cfg.olt_name == "OLT-TEST"
    assert cfg.olt_rx_power_threshold == -27.5
    assert cfg.olt_rx_power_scale == 10.0
    assert cfg.ont_status_online_values == ["1", "up"]
    assert cfg.ont_status_offline_values == ["2", "3", "down"]
