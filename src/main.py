# Process emails every 5 minutes
import random
from process_email import process_email
from local_llm import LocalLLM
import time


if __name__ == "__main__":
    while True:
        # Check and process emails
        process_email()
        time.sleep(300)  # Sleep for 5 minutes

        # Randomly browse Moltbook once in a while
        if random.random() < 0.1:  # 10% chance every 5 minutes
            print("🔍 Randomly browsing Moltbook...")
            llm = LocalLLM()
            llm.set_tools_enabled(True)
            response = llm.prompt("Browse and interact with Moltbook for a while using the available tool calls for Moltbook. Take your time. You have up to 20 iterations/tool calls before this session finishes.", max_tokens=300, temperature=0.5)
            print(f"📖 Moltbook summary: {response}")
