from utils.browse_moltbook import create_a_text_post
from llm.local_llm import LocalLLM
from clients.moltbook import MoltbookClient

llm = LocalLLM()
moltbook_client = MoltbookClient()
create_a_text_post(moltbook_client, llm)
