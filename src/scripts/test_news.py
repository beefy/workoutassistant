from utils.web_search import get_apnews_articles
from llm.priority_queue import submit_llm_request


response = get_apnews_articles(max_articles=5)
print(f"found {len(response)} articles")

summaries = []
for article in response:
    print(f"Summarizing: {article['title']}")
    prompt = f"Summarize the following news article in a concise way:\n\n{article['content']}"

    llm_result = submit_llm_request(
        prompt=prompt,
        max_tokens=500,
        priority=2,  # Low priority for news summarization
        task="Summarize news article"
    )
    response = llm_result.get('response', '')

    print(f"Summary:\n{response}\n")
    summaries.append(response)

prompt = "Summarize the following news summaries into a single concise summary of the current news:\n\n" + "\n\n".join(summaries)

llm_result = submit_llm_request(
    prompt=prompt,
    max_tokens=1000,
    priority=2,  # Low priority for news summarization
    task="Summarize news"
)
response = llm_result.get('response', '')

print(f"News summary:\n{response}")
