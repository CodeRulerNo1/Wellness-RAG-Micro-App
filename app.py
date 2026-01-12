import streamlit as st
import os
import shutil
import datetime
import pymongo
from load_documents import load_docs
from split_doc import split_docs
from storing_doc import store_docs
from RAG_agent import retrieve_context
from chromaDB import vector_store
from langchain_core.messages import HumanMessage, AIMessage
from chat_model import model

# Page Configuration
st.set_page_config(page_title="Yoga Wellness Assistant", layout="wide")

# MongoDB Connection
try:
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["yoga_wellness_db"]
    collection = db["queries"]
    mongo_available = True
except Exception as e:
    mongo_available = False
    print(f"MongoDB Connection Failed: {e}")

# Title and Description
st.title("🧘 Ask Me Anything About Yoga")
st.markdown("Your personal AI assistant for yoga poses, benefits, and safe practices.")

# Safety Logic
UNSAFE_KEYWORDS = [
    "pregnant", "pregnancy", "trimester", 
    "hernia", "glaucoma", "blood pressure", 
    "surgery", "operation", "injury", "pain",
    "medical", "doctor", "disease"
]

def check_safety(query):
    """
    Checks if the query contains unsafe keywords.
    Returns (is_unsafe, reason)
    """
    query_lower = query.lower()
    for keyword in UNSAFE_KEYWORDS:
        if keyword in query_lower:
            return True, keyword
    return False, None

def log_to_mongo(query, answer, sources, is_unsafe, category):
    """Logs the interaction to MongoDB."""
    if not mongo_available:
        return
    
    log_entry = {
        "query": query,
        "answer": answer,
        "sources": sources,
        "is_unsafe": is_unsafe,
        "category": category,
        "timestamp": datetime.datetime.now()
    }
    try:
        collection.insert_one(log_entry)
    except Exception as e:
        print(f"Failed to log to MongoDB: {e}")

def process_documents():
    """
    Clears the vector store and re-processes all documents in the 'uploaded_documents' folder.
    """
    with st.spinner("Updating Yoga Knowledge Base..."):
        try:
            # 1. Clear old vector store safe way
            try:
                existing_data = vector_store.get()
                if existing_data and "ids" in existing_data and existing_data["ids"]:
                    vector_store.delete(existing_data["ids"])
            except Exception as e:
                st.warning(f"Could not clear existing data (might be empty): {e}")

            # 2. Load
            docs = load_docs()
            
            if docs:
                # 3. Split
                splits = split_docs(docs)
                
                # 4. Store
                ids = store_docs(splits)
                st.toast(f"Knowledge Base Updated! ({len(ids)} chunks)")
            else:
                st.toast("Knowledge Base Cleared (No documents).")
                
        except Exception as e:
            st.error(f"Error processing documents: {e}")

# Sidebar for Document Management
with st.sidebar:
    st.header("Admin Panel")
    st.markdown("### Knowledge Base Management")
    
    if st.button("Refresh Knowledge Base"):
        process_documents()

    if st.checkbox("Show Upload Options"):
        uploaded_files = st.file_uploader(
            "Upload Yoga Articles (TXT/PDF)", 
            type=["pdf", "docx", "txt"], 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            upload_dir = "uploaded_documents"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            for uploaded_file in uploaded_files:
                file_path = os.path.join(upload_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            
            st.success("Files uploaded. Click 'Refresh Knowledge Base' to apply.")

    st.markdown("### Current Files")
    if os.path.exists("uploaded_documents"):
        files = os.listdir("uploaded_documents")
        if files:
            for f in files:
                st.text(f"📄 {f}")
        else:
            st.text("No documents found.")
    else:
        st.text("No documents folder.")

    st.divider()
    if mongo_available:
        st.success("✅ MongoDB Connected")
    else:
        st.error("❌ MongoDB Not Connected")

# Chat Interface
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            if "⚠️ **SAFETY WARNING**" in message.content:
                st.error(message.content) # Render unsafe messages as error blocks
            else:
                st.markdown(message.content)

# User Input
if prompt := st.chat_input("Ask about a pose, breathing technique, or benefit..."):
    # Add user message to state
    st.session_state.messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # 1. Safety Check
        is_unsafe, unsafe_reason = check_safety(prompt)
        
        if is_unsafe:
            warning_msg = (
                f"### ⚠️ **SAFETY WARNING**\n\n"
                f"Your query mentions **'{unsafe_reason}'**, which indicates a potential health risk.\n\n"
                f"**Advisory:**\n"
                f"- Please consult a doctor or certified yoga therapist before attempting new poses.\n"
                f"- Yoga can be beneficial, but certain conditions require personalized modifications that an AI cannot safely prescribe.\n"
                f"- Consider gentle breathing exercises (Pranayama) or meditation instead of physical asanas."
            )
            message_placeholder.error(warning_msg)
            st.session_state.messages.append(AIMessage(content=warning_msg))
            log_to_mongo(prompt, warning_msg, [], True, "Safety Blocked")
        
        else:
            with st.spinner("Searching Yoga Knowledge Base..."):
                try:
                    # 2. Intelligent Categorization
                    category_prompt = f"""Categorize this yoga query into ONE:
                    - Asana (Poses)
                    - Pranayama (Breathing)
                    - Philosophy
                    - Benefits/Contraindications
                    - General
                    
                    Query: {prompt}
                    Category:"""
                    
                    try:
                        cat_response = model.invoke([HumanMessage(content=category_prompt)])
                        category = cat_response.content.strip().split('\n')[0].replace("- ", "")
                    except:
                        category = "General"
                    
                    # 3. Retrieve Context
                    result = retrieve_context.func(prompt)
                    
                    context_str = ""
                    sources_list = []
                    
                    if isinstance(result, tuple):
                        _, raw_docs = result
                        # Extract clean source names
                        for doc in raw_docs:
                            src_meta = doc.metadata
                            src_name = os.path.basename(src_meta.get('source', 'Unknown'))
                            page = src_meta.get('page', 'N/A')
                            sources_list.append({"name": src_name, "page": page})
                        
                        context_elements = []
                        for i, doc in enumerate(raw_docs):
                            context_elements.append(f"[Source {i+1}]: {doc.page_content}")
                        
                        context_str = "\n\n".join(context_elements)
                    else:
                        context_str = str(result)

                    system_prompt = f"""You are a Yoga Wellness Assistant. Answer the user's question based ONLY on the provided Context. 
                    
                    Context:
                    {context_str}
                    
                    Instructions:
                    1. Be encouraging and calm.
                    2. If the answer is not in the context, say "I cannot find specific advice on this in my current library."
                    3. ALWAYS mention: "Listen to your body and stop if you feel pain."
                    4. Cite sources using [Source X] format.
                    """
                    
                    messages = [
                        HumanMessage(content=system_prompt),
                        HumanMessage(content=prompt)
                    ]
                    
                    # 4. Streaming Response
                    answer_content = ""
                    header_text = f"**Topic:** {category}\n\n"
                    
                    for chunk in model.stream(messages):
                        answer_content += chunk.content
                        message_placeholder.markdown(header_text + answer_content + "▌")
                    
                    # Formatting Sources
                    source_text = ""
                    if sources_list:
                        source_text += "\n\n---\n**Sources Used:**\n"
                        unique_sources = {f"{s['name']} (Page {s['page']})" for s in sources_list}
                        for src in unique_sources:
                            source_text += f"- 📖 {src}\n"

                    final_output = header_text + answer_content + source_text
                    message_placeholder.markdown(final_output)
                    
                    # Add to state and log
                    st.session_state.messages.append(AIMessage(content=final_output))
                    log_to_mongo(prompt, final_output, list(unique_sources) if sources_list else [], False, category)

                    # Feedback Buttons
                    col1, col2, col3 = st.columns([0.05, 0.05, 0.9])
                    with col1:
                        if st.button("👍", key=f"like_{len(st.session_state.messages)}"):
                            st.toast("Thanks for the positive feedback!")
                    with col2:
                        if st.button("👎", key=f"dislike_{len(st.session_state.messages)}"):
                            st.toast("Thanks for the feedback. We'll work to improve!")
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")