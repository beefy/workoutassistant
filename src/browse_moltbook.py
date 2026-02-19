from local_llm import LocalLLM
from moltbook import MoltbookClient
import random

def comment_on_a_post(moltbook_client, llm):
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

def create_a_text_post(moltbook_client, llm):
    # Step 1: find a random submolt to post it in
    submolts_response = moltbook_client.list_submolts()
    submolts = submolts_response['submolts']
    submolt_names = [submolt['name'] for submolt in submolts]
    chosen_submolt = random.choice(submolt_names)
    print(f"Chosen submolt: {chosen_submolt}")

    title = llm.prompt(f"Generate an interesting post title for Moltbook about the topic: {chosen_submolt}.", max_tokens=10, temperature=0.7)

    # Clean title to remove "Dear User" and "Sincerely, Bob the Raspberry Pi" if they are included
    title = title.replace("Dear User,", "").replace("Sincerely, Bob the Raspberry Pi", "").strip()

    print(f"Generated post title: {title}")
    content = llm.prompt(f"Write a short and engaging post to go with this title: {title}", max_tokens=200, temperature=0.7)
    print(f"Generated post content: {content}")

    # Step 2: Create the post
    response = moltbook_client.create_post(chosen_submolt, title, content)
    print(f"Created post with ID: {response['post']['id']}")

def browse_moltbook():
    llm = LocalLLM()
    moltbook_client = MoltbookClient()

    if llm.model is None:
        print("❌ Model failed to load")
        return
    
    print("🔍 Browsing Moltbook...")
    # Randomly decide to comment on a post or create a new post
    if random.random() < 0.9:  # 90% chance to comment, 10% chance to create a new post
        comment_on_a_post(moltbook_client, llm)
    else:
        create_a_text_post(moltbook_client, llm)


if __name__ == "__main__":
    browse_moltbook()
