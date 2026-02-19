from src.browse_moltbook import create_a_text_post
from local_llm import LocalLLM
from moltbook import MoltbookClient

llm = LocalLLM()
moltbook_client = MoltbookClient()
create_a_text_post(moltbook_client, llm)
