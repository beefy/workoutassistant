import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class MoltbookClient:
    def __init__(self):
        self.api_key = os.getenv("MOLTBOOK_API_KEY")
        if not self.api_key:
            raise ValueError("MOLTBOOK_API_KEY environment variable is required")

        self.base_url = "https://www.moltbook.com/api/v1"
    
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def create_post(self, submolt, title, content):
        # curl -X POST https://www.moltbook.com/api/v1/posts \
        #     -H "Authorization: Bearer YOUR_API_KEY" \
        #     -H "Content-Type: application/json" \
        #     -d '{"submolt": "general", "title": "Hello Moltbook!", "content": "My first post!"}'
        data = {
            "submolt_name": submolt,
            "title": title,
            "content": content
        }
        response = requests.post(
            f"{self.base_url}/posts",
            headers=self._get_headers(),
            json=data
        )
        
        if not response.ok:
            print(f"❌ API Error {response.status_code}: {response.reason}")
            try:
                error_details = response.json()
                print(f"Error details: {error_details}")
            except:
                print(f"Raw error response: {response.text}")
        
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def create_link_post(self, submolt, title, url):
        # curl -X POST https://www.moltbook.com/api/v1/posts \
        #     -H "Authorization: Bearer YOUR_API_KEY" \
        #     -H "Content-Type: application/json" \
        #     -d '{"submolt": "general", "title": "Interesting article", "url": "https://example.com"}'
        data = {
            "submolt": submolt,
            "title": title,
            "url": url
        }
        response = requests.post(
            f"{self.base_url}/posts",
            headers=self._get_headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def get_feed(self):
        # curl "https://www.moltbook.com/api/v1/posts?sort=hot&limit=25" \
        #     -H "Authorization: Bearer YOUR_API_KEY"
        response = requests.get(
            f"{self.base_url}/posts?sort=hot&limit=5",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def get_posts_from_submolt(self, submolt):
        # curl "https://www.moltbook.com/api/v1/posts?submolt=general&sort=new" \
        #     -H "Authorization: Bearer YOUR_API_KEY"
        response = requests.get(
            f"{self.base_url}/posts?submolt={submolt}&sort=new",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def get_single_post(self, post_id):
        # url https://www.moltbook.com/api/v1/posts/POST_ID \
        #     -H "Authorization: Bearer YOUR_API_KEY"
        response = requests.get(
            f"{self.base_url}/posts/{post_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def add_comment(self, post_id, content):
        # curl -X POST https://www.moltbook.com/api/v1/posts/POST_ID/comments \
        # -H "Authorization: Bearer YOUR_API_KEY" \
        # -H "Content-Type: application/json" \
        # -d '{"content": "Great insight!"}'
        data = {"content": content}
        response = requests.post(
            f"{self.base_url}/posts/{post_id}/comments",
            headers=self._get_headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def reply_to_comment(self, post_id, parent_comment_id, content):
        # curl -X POST https://www.moltbook.com/api/v1/posts/POST_ID/comments \
        #     -H "Authorization: Bearer YOUR_API_KEY" \
        #     -H "Content-Type: application/json" \
        #     -d '{"content": "I agree!", "parent_id": "COMMENT_ID"}'
        data = {
            "content": content,
            "parent_id": parent_comment_id
        }
        response = requests.post(
            f"{self.base_url}/posts/{post_id}/comments",
            headers=self._get_headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def get_comments(self, post_id):
        # curl "https://www.moltbook.com/api/v1/posts/POST_ID/comments?sort=top" \
        # -H "Authorization: Bearer YOUR_API_KEY"
        response = requests.get(
            f"{self.base_url}/posts/{post_id}/comments?sort=top",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def upvote_post(self, post_id):
        # curl -X POST https://www.moltbook.com/api/v1/posts/POST_ID/upvote \
        #     -H "Authorization: Bearer YOUR_API_KEY"
        response = requests.post(
            f"{self.base_url}/posts/{post_id}/upvote",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def downvote_post(self, post_id):
        # curl -X POST https://www.moltbook.com/api/v1/posts/POST_ID/downvote \
        #   -H "Authorization: Bearer YOUR_API_KEY"
        response = requests.post(
            f"{self.base_url}/posts/{post_id}/downvote",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def upvote_comment(self, comment_id):
        # curl -X POST https://www.moltbook.com/api/v1/comments/COMMENT_ID/upvote \
        #     -H "Authorization: Bearer YOUR_API_KEY"
        response = requests.post(
            f"{self.base_url}/comments/{comment_id}/upvote",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def list_submolts(self):
        # curl https://www.moltbook.com/api/v1/submolts \
        # -H "Authorization: Bearer YOUR_API_KEY"
        response = requests.get(
            f"{self.base_url}/submolts",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def subscribe_to_submolt(self, submolt):
        # curl -X POST https://www.moltbook.com/api/v1/submolts/SUBMOLT_NAME/subscribe \
        #     -H "Authorization
        response = requests.post(
            f"{self.base_url}/submolts/{submolt}/subscribe",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def unsubscribe_from_submolt(self, submolt):
        # curl -X DELETE https://www.moltbook.com/api/v1/submolts/SUBMOLT_NAME/subscribe \
        # -H "Authorization: Bearer YOUR_API_KEY"
        response = requests.delete(
            f"{self.base_url}/submolts/{submolt}/subscribe",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def follow_user(self, username):
        # curl -X POST https://www.moltbook.com/api/v1/agents/MOLTY_NAME/follow \
        # -H "Authorization: Bearer YOUR_API_KEY"
        response = requests.post(
            f"{self.base_url}/agents/{username}/follow",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def unfollow_user(self, username):
        # curl -X DELETE https://www.moltbook.com/api/v1/agents/MOLTY_NAME/follow \
        # -H "Authorization: Bearer YOUR_API_KEY"
        response = requests.delete(
            f"{self.base_url}/agents/{username}/follow",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def get_personalized_feed(self):
        # curl "https://www.moltbook.com/api/v1/feed?sort=hot&limit=25" \
        #   -H "Authorization: Bearer YOUR_API_KEY"
        response = requests.get(
            f"{self.base_url}/feed?sort=new&limit=15",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError))
    )
    def search_posts_and_comments(self, query):
        # curl "https://www.moltbook.com/api/v1/search?q=how+do+agents+handle+memory&limit=20" \
        #   -H "Authorization: Bearer YOUR_API_KEY"
        import urllib.parse
        encoded_query = urllib.parse.quote_plus(query)
        response = requests.get(
            f"{self.base_url}/search?q={encoded_query}&limit=5",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
