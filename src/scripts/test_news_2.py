from utils.web_search import get_apnews_article_titles

response = get_apnews_article_titles(max_articles=5)
print(f"found {len(response)} articles")
# Expected output:
# Kansas City airport reopens hours after an evacuation as a potential threat was investigated
# Debris sent flying as suspected tornado strikes southwest Michigan
for article in response:
    print(article)
