from local_llm import LocalLLM
import os

client = LocalLLM()
test_email = os.getenv("TEST_EMAIL")
response = client.prompt(f"Get the current system info and email it to {test_email}")
print(response)
