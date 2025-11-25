import streamlit as st
import os
import shutil
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    load_index_from_storage
)
from llama_index.llms.ollama import Ollama
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import google.generativeai as genai

# --- Configuration ---
DATA_DIR = "./data"
PERSIST_DIR = "./storage"
OLLAMA_MODEL = "llama3.2:1b"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

st.set_page_config(page_title="Local RAG Chatbot", layout="wide")
st.title("🤖 Document Chatbot")

# ----------------------- SIDEBAR SETTINGS ------------------------------------ #
with st.sidebar:
    st.header("⚙️ Model Selection")
    
    # Model choice
    model_choice = st.radio(
        "Choose your LLM:",
        ["🏠 Local (Ollama)", "🌐 Gemini (Cloud)"],
        key="model_choice"
    )
    
    # Show relevant instructions based on choice
    if model_choice == "🏠 Local (Ollama)":
        # Check if Ollama is running
        import subprocess
        try:
            result = subprocess.run(["pgrep", "-x", "ollama"], capture_output=True)
            if result.returncode == 0:
                st.success("✅ Ollama is running")
            else:
                st.warning("⚠️ Ollama is not running")
                st.info("Run `./start_ollama.sh` in terminal to start Ollama")
        except:
            st.error("❌ Ollama not found")
            st.info("Install with: `brew install ollama`")
    
    # API Key input for Gemini
    if model_choice == "🌐 Gemini (Cloud)":
        api_key = st.text_input(
            "Enter Gemini API Key:",
            type="password",
            help="Get your API key from https://aistudio.google.com/apikey"
        )
        if api_key:
            st.session_state["gemini_api_key"] = api_key
            st.success("✅ API Key saved!")
        else:
            st.warning("⚠️ Please enter your Gemini API key to continue.")
    
    st.divider()
    st.subheader("📊 Current Settings")
    
    if model_choice == "🏠 Local (Ollama)":
        st.info(f"**LLM:** Ollama ({OLLAMA_MODEL})")
    else:
        st.info(f"**LLM:** Gemini (gemini-1.5-flash)")
    
    st.info(f"**Embeddings:** {EMBED_MODEL}")
    
    st.divider()

    if st.button("🔄 Refresh / Re-index Knowledge Base"):
        # Clear cached index
        if "index" in st.session_state:
            del st.session_state["index"]

        # Delete old storage
        if os.path.exists(PERSIST_DIR):
            shutil.rmtree(PERSIST_DIR)

        # Set flag to show indexing is in progress
        st.session_state["indexing"] = True
        st.rerun()

# ---------------------- FRONTEND FILE UPLOAD -------------------------------- #
st.subheader("📂 Upload Documents")

uploaded_files = st.file_uploader(
    "Upload PDFs or text files",
    accept_multiple_files=True,
    type=["pdf", "txt", "md"]
)

if uploaded_files:
    os.makedirs(DATA_DIR, exist_ok=True)

    for file in uploaded_files:
        file_path = os.path.join(DATA_DIR, file.name)
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())

    st.success("Files uploaded successfully!")
    st.info("Click **Re-index Knowledge Base** on the left to update the chatbot.")


# ---------------------- LlamaIndex Settings ---------------------------------- #
@st.cache_resource
def get_settings(model_type, _api_key=None):
    """Initialize LLM and embeddings based on user choice"""
    embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)
    
    if model_type == "🏠 Local (Ollama)":
        llm = Ollama(model=OLLAMA_MODEL, request_timeout=300.0)
    else:  # Gemini
        if not _api_key:
            st.error("Please provide a Gemini API key in the sidebar.")
            st.stop()
        # Configure the genai library
        genai.configure(api_key=_api_key)
        # Use Gemini with the correct model name for free tier
        llm = Gemini(model_name="models/gemini-pro", api_key=_api_key)

    Settings.llm = llm
    Settings.embed_model = embed_model
    return llm, embed_model

llm, embed_model = get_settings(
    model_choice, 
    st.session_state.get("gemini_api_key")
)


# ------------------------- Load or Create Index ------------------------------ #
@st.cache_resource(show_spinner=False)
def load_index():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        return None

    files = os.listdir(DATA_DIR)
    if not files:
        return None

    # Use existing index if available
    if os.path.exists(PERSIST_DIR):
        try:
            with st.spinner("📚 Loading existing index..."):
                storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
                index = load_index_from_storage(storage_context)
                st.success("✅ Index loaded successfully!")
                return index
        except:
            pass

    # Fresh indexing with progress bar
    st.info(f"📄 Found {len(files)} file(s) to index...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Load documents
    status_text.text("Step 1/3: Reading documents...")
    progress_bar.progress(33)
    documents = SimpleDirectoryReader(DATA_DIR).load_data()
    
    # Step 2: Create index
    status_text.text(f"Step 2/3: Creating embeddings for {len(documents)} document(s)...")
    progress_bar.progress(66)
    index = VectorStoreIndex.from_documents(documents)
    
    # Step 3: Persist
    status_text.text("Step 3/3: Saving index...")
    progress_bar.progress(100)
    index.storage_context.persist(persist_dir=PERSIST_DIR)
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    st.success("✅ Indexing complete! You can now chat with your documents.")
    
    return index


# Initialize Index
if "index" not in st.session_state:
    # Check if we're in indexing mode
    if st.session_state.get("indexing", False):
        # Show progress manually
        if os.path.exists(DATA_DIR) and os.listdir(DATA_DIR):
            files = os.listdir(DATA_DIR)
            st.info(f"📄 Found {len(files)} file(s) to index...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Load documents
            status_text.text("Step 1/3: Reading documents...")
            progress_bar.progress(33)
            documents = SimpleDirectoryReader(DATA_DIR).load_data()
            
            # Step 2: Create index
            status_text.text(f"Step 2/3: Creating embeddings for {len(documents)} document(s)...")
            progress_bar.progress(66)
            index = VectorStoreIndex.from_documents(documents)
            
            # Step 3: Persist
            status_text.text("Step 3/3: Saving index...")
            progress_bar.progress(100)
            index.storage_context.persist(persist_dir=PERSIST_DIR)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            st.success("✅ Indexing complete! You can now chat with your documents.")
            
            st.session_state["index"] = index
            st.session_state["indexing"] = False
        else:
            st.session_state["indexing"] = False
    else:
        st.session_state["index"] = load_index()

index = st.session_state["index"]

# ----------------------------- Chat Interface -------------------------------- #
st.subheader("💬 Chat with Your Documents")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input from user
if index is None:
    st.chat_input("Upload documents first to start chatting...", disabled=True)
    st.info("👆 Upload some documents and click 'Re-index' to start chatting!")
else:
    if prompt := st.chat_input("Ask something from your documents..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                query_engine = index.as_query_engine(
                    streaming=True,
                    similarity_top_k=1,
                    system_prompt=(
                        "You answer strictly using the provided context. "
                        "If answer is not in documents, reply: "
                        "'I cannot answer this based on the provided documents.'"
                    )
                )

                try:
                    response = query_engine.query(prompt)
                    placeholder = st.empty()

                    full_response = ""
                    for token in response.response_gen:
                        full_response += token
                        placeholder.markdown(full_response + "▌")

                    placeholder.markdown(full_response)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response
                    })

                except Exception as e:
                    st.error(f"Error: {e}")


