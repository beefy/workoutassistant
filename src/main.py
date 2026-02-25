from tasks import heartbeat, use_moltbook, respond_to_email, newsletter, trade_crypto, discord_bot
import threading
import time
from utils.tracking_api import login, status_update
import os
from clients.gmail import GmailClient


def auto_restart_wrapper(target_func, name):
    """Wrapper to automatically restart threads that encounter exceptions"""
    while True:
        try:
            print(f"🔄 Starting {name} thread...")
            target_func()
        except Exception as e:
            print(f"❌ {name} thread crashed: {e}")
            print(f"🔄 Restarting {name} thread in 5 seconds...")

            print(f"⚠️ An error occurred: {e}")
            admin_email = os.getenv("ADMIN_EMAIL")
            client = GmailClient()
            client.send_email_with_attachment(admin_email, f"Bob encountered an Exception in {name} thread", "Please see the attached file.", file_path="/home/bob/Code/workoutassistant/output.log")
            tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
            if tracking_token:
                status_update(tracking_token, "Error!")

            time.sleep(5)


if __name__ == "__main__":
    # start threads with auto-restart capability
    threading.Thread(target=auto_restart_wrapper, args=(heartbeat.main, "heartbeat"), daemon=True).start()
    threading.Thread(target=auto_restart_wrapper, args=(use_moltbook.main, "moltbook"), daemon=True).start()
    threading.Thread(target=auto_restart_wrapper, args=(respond_to_email.main, "email"), daemon=True).start()
    threading.Thread(target=auto_restart_wrapper, args=(newsletter.main, "newsletter"), daemon=True).start()
    threading.Thread(target=auto_restart_wrapper, args=(trade_crypto.main, "crypto"), daemon=True).start()
    threading.Thread(target=auto_restart_wrapper, args=(discord_bot.main, "discord_bot"), daemon=True).start()
    
    # keep main thread alive - wait for keyboard interrupt
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        exit(0)
