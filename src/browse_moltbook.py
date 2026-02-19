from local_llm import LocalLLM
from moltbook import MoltbookClient
import random

def browse_moltbook():
    llm = LocalLLM()
    moltbook_client = MoltbookClient()

    if llm.model is None:
        print("❌ Model failed to load")
        return
    
    print("🔍 Browsing Moltbook...")

    # Step 1: Find a random post and get the post ID
    response = moltbook_client.get_personalized_feed()
    length = len(response['posts'])
    if length == 0:
        print("No posts found in feed.")
        return
    
    random_post = response['posts'][random.randint(0, length - 1)]
    post_id = random_post['id']
    print(f"Found post with ID: {post_id}")

    # Step 2: Get the post details
    post_details = moltbook_client.get_single_post(post_id)
    print(f"Post details: {post_details}")


if __name__ == "__main__":
    browse_moltbook()
