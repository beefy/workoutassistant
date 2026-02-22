from tasks import heartbeat, use_moltbook, respond_to_email
import threading

if __name__ == "__main__":
    # start threads
    threading.Thread(target=heartbeat.main, daemon=True).start()
    threading.Thread(target=use_moltbook.main, daemon=True).start()
    threading.Thread(target=respond_to_email.main, daemon=True).start()
    
    # keep main thread alive - wait for keyboard interrupt
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        exit(0)
