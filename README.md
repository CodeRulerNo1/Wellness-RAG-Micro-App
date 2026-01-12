# 🧘 Yoga Wellness RAG Assistant

A local, AI-powered assistant for yoga practice, designed to provide safe, context-aware answers using Retrieval-Augmented Generation (RAG).

## 🚀 Features

*   **RAG-Powered Q&A:** Answers questions based on your specific uploaded documents (PDF, TXT, DOCX).
*   **Safety First:** Built-in safety layer to detect and block queries related to medical conditions, pregnancy, or injuries, directing users to professional help.
*   **Knowledge Base Management:** Upload documents and refresh the vector database directly from the UI.
*   **Interaction Logging:** Logs all queries, answers, and safety triggers to MongoDB for audit and improvement.
*   **Source Citation:** Transparency by citing the exact document and page number used for the answer.
*   **User Feedback:** Simple thumbs up/down mechanism for response quality tracking.

## 🛠️ Architecture

The application follows a modular Micro-Service architecture:

1.  **Frontend:** Built with **Streamlit** for a responsive, interactive web UI.
2.  **LLM Layer:** Uses **Ollama (Llama 3.2)** for local inference, ensuring privacy and zero cost.
3.  **Vector Database:** **ChromaDB** stores document embeddings locally for fast retrieval.
4.  **Orchestration:** **LangChain** manages the RAG pipeline (Retrieval -> Context Injection -> Generation).
5.  **Data Persistence:** **MongoDB** stores chat logs, categorizations, and safety events.

### The RAG Pipeline
1.  **Ingest:** Documents are loaded (`load_documents.py`), split into chunks (`split_doc.py`), and embedded.
2.  **Store:** Embeddings are saved to `chroma_langchain_db`.
3.  **Retrieve:** User queries trigger a similarity search in ChromaDB.
4.  **Generate:** Relevant chunks are passed to Llama 3.2 via Ollama to generate a natural language response.

## 📦 Setup & Installation

### Prerequisites
*   Python 3.10+
*   [Ollama](https://ollama.com/) installed and running.
*   MongoDB installed and running locally on port 27017.

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/CodeRulerNo1/Wellness-RAG-Micro-App

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Setup Ollama
Ensure you have the model pulled:
```bash
ollama pull llama3.2
```

### 3. Run the Application
```bash
streamlit run app.py
```

## 🛡️ Design Choices

*   **Why Streamlit?** Chosen for rapid prototyping and its native support for data visualization and chat interfaces.
*   **Why Local RAG (Ollama + Chroma)?** To ensure user privacy regarding health/wellness data and to allow offline capability without API costs.
*   **Safety Implementation:** A deterministic keyword filtering approach is used *before* the LLM call. This is safer than relying on the LLM to self-censor, ensuring immediate blocking of high-risk queries (e.g., "pregnancy yoga").

## 📂 Project Structure
*   `app.py`: Main application entry point and UI logic.
*   `RAG_agent.py`: Handles context retrieval logic.
*   `chat_model.py`: Configures the connection to Ollama.
*   `load_documents.py` / `split_doc.py` / `storing_doc.py`: ETL pipeline for document processing.
*   `uploaded_documents/`: Directory for user-provided knowledge base files.
