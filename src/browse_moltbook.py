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

    # Step 1: Find a random post
    response = moltbook_client.get_personalized_feed()
    length = len(response['posts'])
    if length == 0:
        print("No posts found in feed.")
        return
    
    random_post = response['posts'][random.randint(0, length - 1)]
    post_id = random_post['id']
    print(f"Found post with ID: {post_id}")
    post_details = moltbook_client.get_single_post(post_id)
    print(f"Post title: {post_details['post']['title']}")

    # Step 2: Generate a comment
    comment_content = llm.prompt(f"Write an interesting and relevant comment to this post: ```{post_details['post']['content']}```", max_tokens=200, temperature=0.7)
    print(f"Generated comment: {comment_content}")
    
    # Step 3: Post the comment
    moltbook_client.add_comment(post_id, comment_content)
    print(f"Added comment to post ID {post_id}: {comment_content}")

if __name__ == "__main__":
    browse_moltbook()
