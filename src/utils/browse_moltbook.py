from llm.priority_queue import submit_llm_request
from clients.moltbook import MoltbookClient
from utils.tracking_api import status_update, login
import os
import random

def vote_on_a_post(moltbook_client):
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

    # Step 2: Decide whether to upvote or downvote
    content = post_details['post'].get('content', '')
    if not content:
        content = post_details['post'].get('url', '')
    if not content:
        print("No content or URL found for the post to evaluate.")
        return

    llm_result = submit_llm_request(
        prompt=f"Should you upvote or downvote this post based on its content? Reply with only 'upvote' or 'downvote'. ```{post_details['post']['content']}```",
        priority=2,  # Lower priority for moltbook
        max_tokens=20,
        temperature=0.7
    )
    vote_decision = llm_result.get('response', '')
    print(f"LLM vote decision: {vote_decision}")

    # Step 3: Cast the vote
    if "upvote" in vote_decision.lower():
        moltbook_client.upvote_post(post_id)
        print(f"Upvoted post ID {post_id}")
        tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
        if tracking_token:
            status_update(tracking_token, f"Upvoted a post on Moltbook: {post_id}")

    elif "downvote" in vote_decision.lower():
        moltbook_client.downvote_post(post_id)
        print(f"Downvoted post ID {post_id}")
        tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
        if tracking_token:
            status_update(tracking_token, f"Downvoted a post on Moltbook: {post_id}")

    else:
        print(f"No vote cast on post ID {post_id}")


def comment_on_a_post(moltbook_client):
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
    content = post_details['post'].get('content', '')
    if not content:
        content = post_details['post'].get('url', '')
    if not content:
        print("No content or URL found for the post to evaluate.")
        return

    llm_result = submit_llm_request(
        prompt=f"Write an interesting and relevant comment to this post: ```{post_details['post']['content']}```",
        priority=2,  # Lower priority for moltbook
        max_tokens=200,
        temperature=0.7
    )
    comment_content = llm_result.get('response', '')
    print(f"Generated comment: {comment_content}")
    
    # Step 3: Post the comment
    moltbook_client.add_comment(post_id, comment_content)
    print(f"Added comment to post ID {post_id}: {comment_content}")
    tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
    if tracking_token:
        status_update(tracking_token, f"Commented on a post on Moltbook: {post_id}")


def create_a_text_post(moltbook_client):
    # Step 1: find a random submolt to post it in
    submolts_response = moltbook_client.list_submolts()
    submolts = submolts_response['submolts']
    submolt_names = [submolt['name'] for submolt in submolts]
    chosen_submolt = random.choice(submolt_names)
    print(f"Chosen submolt: {chosen_submolt}")

    llm_result = submit_llm_request(
        prompt=f"Generate an interesting post title for Moltbook about the topic: {chosen_submolt}.",
        priority=2,  # Lower priority for moltbook
        max_tokens=30,
        temperature=0.7
    )
    title = llm_result.get('response', '')
    print(f"Generated post title: {title}")

    # Clean title to remove "Dear User" and "Sincerely, Bob the Raspberry Pi" if they are included
    title = title.replace("Dear User,", "").replace("Sincerely, Bob the Raspberry Pi", "").strip()
    if not title:
        return

    llm_result = submit_llm_request(
        prompt=f"Write an engaging post to go with this title: {title}",
        priority=2,  # Lower priority for moltbook
        max_tokens=1000,
        temperature=0.7
    )
    content = llm_result.get('response', '')
    print(f"Generated post content: {content}")
    
    if not content:
        return

    # Step 2: Create the post
    response = moltbook_client.create_post(chosen_submolt, title, content)
    print(f"Created post with ID: {response['post']['id']}")
    tracking_token = login(os.getenv("TRACKING_API_USERNAME"), os.getenv("TRACKING_API_PASSWORD"))
    if tracking_token:
        status_update(tracking_token, f"Created a post on Moltbook: {response['post']['id']}")


def browse_moltbook():
    moltbook_client = MoltbookClient()
    
    print("🔍 Browsing Moltbook...")
    # Randomly decide what to do
    if random.random() < 0.7:  # 70% chance to comment on a post
        comment_on_a_post(moltbook_client)
    elif random.random() < 0.9:  # 20% chance to upvote/downvote
        vote_on_a_post(moltbook_client)
    else:
        # 10% chance to create a new post
        create_a_text_post(moltbook_client)


if __name__ == "__main__":
    browse_moltbook()
