from utils.web_search import get_apnews_articles
from utils.process_email import submit_llm_request


response = get_apnews_articles(max_articles=5)
print(f"found {len(response)} articles")

prompt = f"Summarize the following news articles in a concise way:\n\n{response}\n\nProvide a summary that captures the main points and key details of the news articles."

response = submit_llm_request(
    prompt=prompt,
    max_tokens=500,
    priority=2,  # Low priority for news summarization
)

print(f"News summary:\n{response}")
