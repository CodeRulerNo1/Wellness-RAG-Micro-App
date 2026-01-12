import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

def load_docs(directory_path="uploaded_documents"):
    """
    Loads PDF, DOCX, and TXT files from the specified directory.
    """
    documents = []
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        return documents

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())
        elif filename.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
            documents.extend(loader.load())
        elif filename.endswith(".txt"):
            loader = TextLoader(file_path)
            documents.extend(loader.load())
    
    return documents

if __name__ == "__main__":
    docs = load_docs()
    print(f"Loaded {len(docs)} documents.")
    if docs:
        print(f"First doc content preview: {docs[0].page_content[:500]}")