import functools
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.config import Config
from app.logger import get_logger
from app.olt.monitor import OLTMonitor
from app.bot.messages import (
    format_start_message,
    format_help_message,
    format_access_denied_message,
    format_error_message,
    format_loading_offline,
    format_loading_redaman,
    format_loading_status,
    format_offline_onts_message,
    format_high_attenuation_message,
    format_status_message,
)

logger = get_logger()


def restricted(func):
    """
    Decorator to restrict bot commands to chat IDs specified in TELEGRAM_ALLOWED_CHAT_IDS.
    If TELEGRAM_ALLOWED_CHAT_IDS is empty, access is allowed for all.
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        config: Config = context.bot_data.get("config")
        user_chat_id = update.effective_chat.id if update.effective_chat else None

        if config and config.telegram_allowed_chat_ids:
            if user_chat_id not in config.telegram_allowed_chat_ids:
                logger.warning(f"Akses ditolak untuk Chat ID: {user_chat_id}")
                if update.message:
                    await update.message.reply_text(
                        format_access_denied_message(),
                        parse_mode=ParseMode.HTML
                    )
                return

        return await func(update, context, *args, **kwargs)

    return wrapper


@restricted
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    logger.info(f"/start dipanggil oleh Chat ID: {update.effective_chat.id}")
    await update.message.reply_text(
        format_start_message(),
        parse_mode=ParseMode.HTML
    )


@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command."""
    logger.info(f"/help dipanggil oleh Chat ID: {update.effective_chat.id}")
    await update.message.reply_text(
        format_help_message(),
        parse_mode=ParseMode.HTML
    )


@restricted
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /status command."""
    logger.info(f"/status dipanggil oleh Chat ID: {update.effective_chat.id}")
    monitor: OLTMonitor = context.bot_data["monitor"]
    config: Config = context.bot_data["config"]

    loading_msg = await update.message.reply_text(
        format_loading_status(),
        parse_mode=ParseMode.HTML
    )

    try:
        is_conn, msg_or_err, response_ms = await monitor.check_connection()
        text = format_status_message(
            olt_name=config.olt_name,
            host=config.olt_host,
            snmp_version=config.olt_snmp_version,
            is_connected=is_conn,
            response_time_ms=response_ms,
            error_msg=msg_or_err if not is_conn else ""
        )
        await loading_msg.edit_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception(f"Error pada /status handler: {e}")
        await loading_msg.edit_text(
            format_error_message(),
            parse_mode=ParseMode.HTML
        )


@restricted
async def cek_putus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /cek_putus command."""
    logger.info(f"/cek_putus dipanggil oleh Chat ID: {update.effective_chat.id}")
    monitor: OLTMonitor = context.bot_data["monitor"]
    config: Config = context.bot_data["config"]

    loading_msg = await update.message.reply_text(
        format_loading_offline(),
        parse_mode=ParseMode.HTML
    )

    try:
        offline_onts = await monitor.get_offline_onts()
        messages = format_offline_onts_message(offline_onts, config.olt_name)

        if not messages:
            await loading_msg.edit_text(
                format_error_message("Gagal memformat hasil ONT putus."),
                parse_mode=ParseMode.HTML
            )
            return

        # Edit loading message with first chunk
        await loading_msg.edit_text(messages[0], parse_mode=ParseMode.HTML)

        # Send subsequent chunks if pagination needed
        for extra_msg in messages[1:]:
            await update.message.reply_text(extra_msg, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.exception(f"Error pada /cek_putus handler: {e}")
        await loading_msg.edit_text(
            format_error_message(),
            parse_mode=ParseMode.HTML
        )


@restricted
async def cek_redaman_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /cek_redaman command."""
    logger.info(f"/cek_redaman dipanggil oleh Chat ID: {update.effective_chat.id}")
    monitor: OLTMonitor = context.bot_data["monitor"]
    config: Config = context.bot_data["config"]

    loading_msg = await update.message.reply_text(
        format_loading_redaman(),
        parse_mode=ParseMode.HTML
    )

    try:
        high_attenuation_onts = await monitor.get_high_attenuation_onts()
        messages = format_high_attenuation_message(
            ont_list=high_attenuation_onts,
            olt_name=config.olt_name,
            threshold=config.olt_rx_power_threshold
        )

        if not messages:
            await loading_msg.edit_text(
                format_error_message("Gagal memformat hasil redaman."),
                parse_mode=ParseMode.HTML
            )
            return

        # Edit loading message with first chunk
        await loading_msg.edit_text(messages[0], parse_mode=ParseMode.HTML)

        # Send subsequent chunks if pagination needed
        for extra_msg in messages[1:]:
            await update.message.reply_text(extra_msg, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.exception(f"Error pada /cek_redaman handler: {e}")
        await loading_msg.edit_text(
            format_error_message(),
            parse_mode=ParseMode.HTML
        )
