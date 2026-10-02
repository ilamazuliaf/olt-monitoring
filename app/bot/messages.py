import html
from datetime import datetime
from typing import List, Dict
from app.olt.models import ONT


def get_current_timestamp() -> str:
    """Return formatted timestamp for messages."""
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")


def split_message(header: str, blocks: List[str], footer: str, max_len: int = 3800) -> List[str]:
    """
    Split long content into multiple message chunks respecting Telegram length limits.
    """
    if not blocks:
        full_msg = f"{header}\n\n{footer}"
        return [full_msg]

    messages = []
    current_chunk = []
    current_len = len(header) + len(footer) + 50

    for block in blocks:
        block_len = len(block) + 2
        if current_len + block_len > max_len and current_chunk:
            messages.append("\n\n".join(current_chunk))
            current_chunk = []
            current_len = len(header) + len(footer) + 50

        current_chunk.append(block)
        current_len += block_len

    if current_chunk:
        messages.append("\n\n".join(current_chunk))

    total = len(messages)
    if total == 1:
        return [f"{header}\n\n{messages[0]}\n\n{footer}"]

    result = []
    for idx, msg in enumerate(messages, 1):
        page_header = f"📄 <b>Bagian {idx}/{total}</b>\n\n{header}"
        result.append(f"{page_header}\n\n{msg}\n\n{footer}")

    return result


def format_start_message() -> str:
    return (
        "📡 <b>OLT MONITOR</b>\n\n"
        "Bot monitoring OLT melalui SNMP.\n\n"
        "Perintah:\n"
        "/cek_putus - Menampilkan ONT yang sedang offline.\n"
        "/cek_redaman - Menampilkan ONT dengan redaman tinggi.\n"
        "/status - Menampilkan status koneksi aplikasi ke OLT.\n"
        "/help - Menampilkan bantuan."
    )


def format_help_message() -> str:
    return (
        "📖 <b>BANTUAN OLT MONITOR</b>\n\n"
        "Gunakan perintah berikut untuk berinteraksi dengan bot:\n\n"
        "• <b>/cek_putus</b>: Memeriksa dan menampilkan seluruh ONT yang berstatus offline.\n"
        "• <b>/cek_redaman</b>: Memeriksa dan menampilkan ONT dengan nilai RX power melampaui threshold.\n"
        "• <b>/status</b>: Memeriksa konektivitas SNMP dari server monitor ke OLT.\n"
        "• <b>/help</b>: Menampilkan menu bantuan ini."
    )


def format_access_denied_message() -> str:
    return (
        "⛔ <b>Akses ditolak.</b>\n\n"
        "Chat ID Anda tidak terdaftar sebagai pengguna bot."
    )


def format_error_message(detail: str = "") -> str:
    if detail:
        return f"❌ <b>Terjadi Kesalahan:</b>\n{html.escape(detail)}"
    return (
        "❌ <b>Terjadi kesalahan pada aplikasi.</b>\n\n"
        "Silakan periksa log server."
    )


def format_loading_offline() -> str:
    return "🔎 <b>Sedang mengecek ONT putus...</b>\n\nMohon tunggu."


def format_loading_redaman() -> str:
    return "🔎 <b>Sedang mengecek redaman ONT...</b>\n\nMohon tunggu."


def format_loading_status() -> str:
    return "🔎 <b>Sedang mengecek status OLT...</b>\n\nMohon tunggu."


def format_offline_onts_message(ont_list: List[ONT], olt_name: str) -> List[str]:
    timestamp = get_current_timestamp()
    if not ont_list:
        return [
            f"🟢 <b>TIDAK ADA ONT PUTUS</b>\n\n"
            f"OLT: {html.escape(olt_name)}\n"
            f"Semua ONT yang terdeteksi saat pengecekan berstatus ONLINE.\n\n"
            f"⏱ Waktu: {timestamp}"
        ]

    header = (
        f"🔴 <b>ONT PUTUS</b>\n\n"
        f"OLT: {html.escape(olt_name)}\n"
        f"Total: {len(ont_list)} ONT"
    )

    # Group by PON
    grouped: Dict[str, List[ONT]] = {}
    for ont in ont_list:
        pon_key = ont.pon or "1/1/1"
        grouped.setdefault(pon_key, []).append(ont)

    blocks = []
    for pon, items in grouped.items():
        block_lines = [f"<b>PON {html.escape(pon)}</b>"]
        for idx, ont in enumerate(items, 1):
            sn = html.escape(ont.serial_number or "-")
            name_info = f"\n  Nama: {html.escape(ont.name)}" if ont.name and ont.name != "-" else ""
            block_lines.append(
                f"• <b>ONT {html.escape(str(ont.ont_id))}</b>{name_info}\n"
                f"  Status: OFFLINE\n"
                f"  SN: {sn}"
            )
        blocks.append("\n".join(block_lines))

    footer = f"⏱ Waktu pengecekan:\n{timestamp}"
    return split_message(header, blocks, footer)


def format_high_attenuation_message(ont_list: List[ONT], olt_name: str, threshold: float) -> List[str]:
    timestamp = get_current_timestamp()
    if not ont_list:
        return [
            f"🟢 <b>REDAMAN NORMAL</b>\n\n"
            f"OLT: {html.escape(olt_name)}\n"
            f"Tidak ada ONT dengan redaman melampaui batas ({threshold} dBm).\n\n"
            f"⏱ Waktu pengecekan:\n{timestamp}"
        ]

    header = (
        f"⚠️ <b>REDAMAN TINGGI</b>\n\n"
        f"OLT: {html.escape(olt_name)}\n"
        f"Batas: {threshold} dBm\n"
        f"Total: {len(ont_list)} ONT"
    )

    grouped: Dict[str, List[ONT]] = {}
    for ont in ont_list:
        pon_key = ont.pon or "1/1/1"
        grouped.setdefault(pon_key, []).append(ont)

    blocks = []
    for pon, items in grouped.items():
        block_lines = [f"<b>PON {html.escape(pon)}</b>"]
        for ont in items:
            sn = html.escape(ont.serial_number or "-")
            rx_str = f"{ont.rx_power:.2f}" if ont.rx_power is not None else "-"
            status_str = ont.status.upper()
            name_info = f"\n  Nama: {html.escape(ont.name)}" if ont.name and ont.name != "-" else ""
            block_lines.append(
                f"• <b>ONT {html.escape(str(ont.ont_id))}</b>{name_info}\n"
                f"  SN: {sn}\n"
                f"  RX Power: {rx_str} dBm\n"
                f"  Status: {status_str}"
            )
        blocks.append("\n".join(block_lines))

    footer = f"⏱ Waktu pengecekan:\n{timestamp}"
    return split_message(header, blocks, footer)


def format_status_message(
    olt_name: str,
    host: str,
    snmp_version: str,
    is_connected: bool,
    response_time_ms: float,
    error_msg: str = ""
) -> str:
    timestamp = get_current_timestamp()
    if is_connected:
        return (
            f"📡 <b>STATUS OLT MONITOR</b>\n\n"
            f"OLT:\n{html.escape(olt_name)}\n\n"
            f"IP:\n{html.escape(host)}\n\n"
            f"SNMP:\nv{html.escape(snmp_version)}\n\n"
            f"Status:\n🟢 CONNECTED\n\n"
            f"Response:\n{response_time_ms} ms\n\n"
            f"Last check:\n{timestamp}"
        )
    else:
        return (
            f"🔴 <b>SNMP ERROR</b>\n\n"
            f"OLT:\n{html.escape(olt_name)}\n\n"
            f"IP:\n{html.escape(host)}\n\n"
            f"Error:\n{html.escape(error_msg or 'Timeout')}\n\n"
            f"Pastikan:\n"
            f"• IP OLT benar\n"
            f"• SNMP aktif\n"
            f"• Community benar\n"
            f"• UDP 161 tidak diblokir"
        )
