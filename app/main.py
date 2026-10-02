import sys
from telegram.ext import ApplicationBuilder, CommandHandler

from app.config import Config
from app.logger import setup_logger
from app.snmp.client import SNMPClient
from app.olt.monitor import OLTMonitor
from app.bot.handlers import (
    start_command,
    help_command,
    cek_putus_command,
    cek_redaman_command,
    status_command,
)


def main():
    """Main application entry point."""
    # 1. Load Configuration
    try:
        config = Config.load()
    except Exception as e:
        print(f"Error Konfigurasi: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Setup Logging
    logger = setup_logger(log_level=config.log_level, log_file=config.log_file)
    logger.info("Starting OLT Telegram Monitor v1.0.0...")
    logger.info(f"Target OLT: {config.olt_name} ({config.olt_host}:{config.olt_port})")

    # 3. Instantiate SNMP Client & OLT Monitor
    snmp_client = SNMPClient(config)
    monitor = OLTMonitor(config, snmp_client)

    # 4. Build Telegram Bot Application
    try:
        application = ApplicationBuilder().token(config.telegram_bot_token).build()
    except Exception as e:
        logger.error(f"Gagal menginisialisasi Telegram Bot Application: {e}")
        sys.exit(1)

    # Store shared objects in bot_data
    application.bot_data["config"] = config
    application.bot_data["monitor"] = monitor

    # 5. Register Command Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cek_putus", cek_putus_command))
    application.add_handler(CommandHandler("cek_redaman", cek_redaman_command))
    application.add_handler(CommandHandler("status", status_command))

    logger.info("Bot Telegram siap & polling dimulai...")

    # 6. Start Polling
    application.run_polling()


if __name__ == "__main__":
    main()
