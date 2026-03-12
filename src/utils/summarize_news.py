from utils.web_search import get_apnews_articles
from llm.priority_queue import submit_llm_request
from clients.gmail import GmailClient
from utils.logging_config import setup_logging
import os
import datetime
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def summarize_news():
    response = get_apnews_articles(max_articles=5)
    logger.info(f"found {len(response)} articles")

    summaries = []
    for article in response:
        logger.info(f"Summarizing: {article['title']}")
        prompt = f"Summarize the following news article in a concise way:\n\n{article['content']}"

        llm_result = submit_llm_request(
            prompt=prompt,
            max_tokens=500,
            priority=3,  # Low priority for news summarization
            task="Summarize news article"
        )
        response = llm_result.get('response', '')

        logger.info(f"Summary:\n{response}\n")
        summaries.append(response)

    prompt = "Summarize the following news summaries into a single summary of the current news:\n\n" + "\n\n".join(summaries)

    response = submit_llm_request(
        prompt=prompt,
        max_tokens=1250,
        priority=3,  # Low priority for news summarization
        task="Summarize news"
    )

    logger.info(f"News summary:\n{response}")
    return response


def email_news_summary():
    # TODO: store email list in database and use BCC
    try:
        summary = summarize_news()
        summary = summary.get('response') if isinstance(summary, dict) else summary
        
        # Validate that we have content to send
        if not summary or not summary.strip():
            logger.error("❌ Newsletter email not sent: Summary is empty")
            raise Exception("Newsletter summary is empty")
            
        gmail = GmailClient()
        admin_email = os.getenv("ADMIN_EMAIL")
        
        if not admin_email:
            logger.error("❌ Newsletter email not sent: ADMIN_EMAIL environment variable not set")
            raise Exception("ADMIN_EMAIL environment variable not set")
            
        today = datetime.datetime.now().strftime("%m/%d/%Y")
        subject = f"Daily News Summary for {today}"
        
        # Check return value and log result
        email_sent = gmail.send_email(admin_email, subject, summary)
        
        if email_sent:
            logger.info(f"✅ Newsletter email sent successfully to {admin_email}")
            return True
        else:
            logger.error(f"❌ Newsletter email failed to send to {admin_email}")
            raise Exception(f"Failed to send newsletter email to {admin_email}")
            
    except Exception as e:
        logger.error(f"❌ Newsletter email failed with exception: {e}")
        logger.exception("Full traceback:")
        # Re-raise to trigger thread failure and error notification
        raise
