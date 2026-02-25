from utils.web_search import get_apnews_articles
from llm.priority_queue import submit_llm_request
from clients.gmail import GmailClient
import os
import datetime


def summarize_news():
    response = get_apnews_articles(max_articles=5)
    print(f"found {len(response)} articles")

    summaries = []
    for article in response:
        print(f"Summarizing: {article['title']}")
        prompt = f"Summarize the following news article in a concise way:\n\n{article['content']}"

        llm_result = submit_llm_request(
            prompt=prompt,
            max_tokens=500,
            priority=3,  # Low priority for news summarization
            task="Summarize news article"
        )
        response = llm_result.get('response', '')

        print(f"Summary:\n{response}\n")
        summaries.append(response)

    prompt = "Summarize the following news summaries into a single summary of the current news:\n\n" + "\n\n".join(summaries)

    response = submit_llm_request(
        prompt=prompt,
        max_tokens=1250,
        priority=3,  # Low priority for news summarization
        task="Summarize news"
    )

    print(f"News summary:\n{response}")
    return response


def email_news_summary():
    # TODO: store email list in database and use BCC
    summary = summarize_news()
    gmail = GmailClient()
    admin_email = os.getenv("ADMIN_EMAIL")
    today = datetime.datetime.now().strftime("%m/%d/%Y")
    subject = f"Daily News Summary for {today}"
    gmail.send_email(admin_email, subject, summary)
