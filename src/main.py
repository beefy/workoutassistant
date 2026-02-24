from tasks import heartbeat, use_moltbook, respond_to_email, newsletter, trade_crypto
import threading
import time
import signal
import sys
from utils.tracking_api import login, status_update
import os
from clients.gmail import GmailClient

# Global shutdown event
shutdown_event = threading.Event()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"🛑 Received signal {signum}. Initiating graceful shutdown...")
    shutdown_event.set()

def auto_restart_wrapper(target_func, name):
    """Wrapper to automatically restart threads that encounter exceptions"""
    while not shutdown_event.is_set():
        try:
            print(f"🔄 Starting {name} thread...")
            target_func()
        except Exception as e:
            if shutdown_event.is_set():
                print(f"🛑 {name} thread stopped due to shutdown signal")
                break
                
            print(f"❌ {name} thread crashed: {e}")
            print(f"🔄 Restarting {name} thread in 5 seconds...")

            print(f"⚠️ An error occurred: {e}")
            try:
                admin_email = os.getenv("ADMIN_EMAIL")
                if admin_email:
                    client = GmailClient()
                    log_path = os.getenv("LOG_PATH", "/app/logs/output.log")
                    client.send_email_with_attachment(admin_email, f"WorkoutAssistant encountered an Exception in {name} thread", "Please see the attached file.", file_path=log_path)
                
                tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
                if tracking_token:
                    status_update(tracking_token, "Error!")
            except Exception as notify_error:
                print(f"⚠️ Failed to send error notification: {notify_error}")

            # Wait for 5 seconds or until shutdown is requested
            for _ in range(50):  # 5 seconds in 0.1 second intervals
                if shutdown_event.is_set():
                    break
                time.sleep(0.1)

if __name__ == "__main__":
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 Starting WorkoutAssistant...")
    
    # Start threads with auto-restart capability
    threads = []
    thread_configs = [
        (heartbeat.main, "heartbeat"),
        (use_moltbook.main, "moltbook"),
        (respond_to_email.main, "email"),
        (newsletter.main, "newsletter"),
        (trade_crypto.main, "crypto")
    ]
    
    for func, name in thread_configs:
        thread = threading.Thread(target=auto_restart_wrapper, args=(func, name), daemon=True)
        thread.start()
        threads.append(thread)
    
    # Keep main thread alive and handle shutdown
    try:
        shutdown_event.wait()
    except KeyboardInterrupt:
        print("🛑 Received KeyboardInterrupt")
        shutdown_event.set()
    
    print("🛑 Shutting down WorkoutAssistant...")
    
    # Wait a moment for threads to finish gracefully
    time.sleep(2)
    
    print("✅ WorkoutAssistant shutdown complete")
    sys.exit(0)
