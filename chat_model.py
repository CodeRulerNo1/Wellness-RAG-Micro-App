from langchain_ollama import ChatOllama

# Using llama3.2 as the chat model (fits well in 4GB VRAM).
# Ensure you have pulled it: ollama pull llama3.2
model = ChatOllama(model="llama3.2")

