from utils.web_search import get_apnews_articles

response = get_apnews_articles(max_articles=5)
print(response)
