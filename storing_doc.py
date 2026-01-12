from chromaDB import vector_store

def store_docs(all_splits):
    document_ids = vector_store.add_documents(documents=all_splits)
    return document_ids
