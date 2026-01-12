from langchain_ollama import OllamaEmbeddings

# Using llama3.2 as a default embedding model (fits well in 4GB VRAM).
# Ensure you have pulled it: ollama pull llama3.2
embeddings = OllamaEmbeddings(model="llama3.2")