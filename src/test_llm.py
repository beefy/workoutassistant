from local_llm import LocalLLM

client = LocalLLM()
response = client.prompt("What is the capital of France?")
print(response)
