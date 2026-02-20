from local_llm import LocalLLM
import os

client = LocalLLM()
response = client.prompt(f"Generate an image of a puppy")
print(response)
