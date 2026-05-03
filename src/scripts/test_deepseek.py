from llm import deepseek

client = deepseek.DeepSeekLLM()
response = client.prompt("What is the capital of France?")
print(response)
