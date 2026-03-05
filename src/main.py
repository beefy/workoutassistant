from tasks import heartbeat, use_moltbook, respond_to_email, newsletter, trade_crypto, discord_bot
import threading
import time
import signal
import sys
import traceback
from utils.tracking_api import login, status_update
import os
from clients.gmail import GmailClient
import logging
from utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global shutdown event
shutdown_event = threading.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"🛑 Received signal {signum}. Initiating graceful shutdown...")
    shutdown_event.set()


def auto_restart_wrapper(target_func, name):
    """Wrapper to automatically restart threads that encounter exceptions"""
    while not shutdown_event.is_set():
        try:
            logger.info(f"🔄 Starting {name} thread...")
            target_func()
        except Exception as e:
            if shutdown_event.is_set():
                logger.info(f"🛑 {name} thread stopped due to shutdown signal")
                break
            
            error_msg = str(e) or repr(e) or "Unknown error"
            exception_type = type(e).__name__
            logger.error(f"❌ {name} thread crashed: {exception_type}: {error_msg}")
            logger.error(f"📝 Full traceback:")
            logger.error(traceback.format_exc())
            logger.exception("Full traceback:")
            logger.info(f"🔄 Restarting {name} thread in 5 minutes...")

            logger.warning(f"⚠️ An error occurred: {e}")
            try:
                admin_email = os.getenv("ADMIN_EMAIL")
                if admin_email:
                    client = GmailClient()
                    log_path = os.getenv("LOG_PATH", "/app/logs/output.log")
                    agent_name = os.getenv("TRACKING_API_USERNAME", "unknown")
                    client.send_email_with_attachment(admin_email, f"{agent_name} encountered an Exception in {name} thread", "Please see the attached file.", file_path=log_path)
                
                tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
                if tracking_token:
                    status_update(tracking_token, "Error!")
            except Exception as notify_error:
                logger.error(f"⚠️ Failed to send error notification: {notify_error}")
                logger.exception("Full traceback:")

            # Wait for 5 minutes or until shutdown is requested
            for _ in range(300):  # 5 minutes in 1 second intervals
                if shutdown_event.is_set():
                    break
                time.sleep(1)


if __name__ == "__main__":
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("🚀 Starting WorkoutAssistant...")
    
    # Start threads with auto-restart capability
    threads = []
    agent_name = os.getenv("TRACKING_API_USERNAME", "unknown")

    token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
    status_update(token, "Starting threads")

    thread_configs = []
    if agent_name == "bob":
        logger.info("👋 Hello Bob! Starting your personalized assistant threads.")
        thread_configs = [
            (heartbeat.main, "heartbeat"),
            (use_moltbook.main, "moltbook"),
            (respond_to_email.main, "email"),
            # (trade_crypto.bob, "crypto"),
        ]
    elif agent_name == "bobby":
        logger.info("👋 Hello Bobby! Starting your personalized assistant threads.")
        thread_configs = [
            (heartbeat.main, "heartbeat"),
            (use_moltbook.main, "moltbook"),
            (respond_to_email.main, "email"),
            # (trade_crypto.bobby, "crypto"),
            (newsletter.main, "newsletter"),
            (discord_bot.main, "discord_bot")
        ]
    elif agent_name == "robert":
        logger.info("👋 Hello Robert! Starting your personalized assistant threads.")
        thread_configs = [
            (heartbeat.main, "heartbeat"),
            # (trade_crypto.robert, "crypto"),
        ]
    
    for func, name in thread_configs:
        thread = threading.Thread(target=auto_restart_wrapper, args=(func, name), daemon=True)
        thread.start()
        threads.append(thread)
    
    # Keep main thread alive and handle shutdown
    try:
        shutdown_event.wait()
    except KeyboardInterrupt:
        logger.info("🛑 Received KeyboardInterrupt")
        shutdown_event.set()
    
    logger.info("🛑 Shutting down WorkoutAssistant...")
    
    # Wait a moment for threads to finish gracefully
    time.sleep(2)
    
    logger.info("✅ WorkoutAssistant shutdown complete")
    sys.exit(0)
