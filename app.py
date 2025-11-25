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
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# --- Configuration ---
DATA_DIR = "./data"
PERSIST_DIR = "./storage"
LLM_MODEL = "llama3.2:1b"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

st.set_page_config(page_title="Local RAG Chatbot", layout="wide")
st.title("🤖 Local Document Chatbot")

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


# ----------------------- SIDEBAR SETTINGS ------------------------------------ #
with st.sidebar:
    st.header("Settings")
    st.info(f"LLM: **{LLM_MODEL}**")
    st.info(f"Embeddings: **{EMBED_MODEL}**")

    if st.button("🔄 Refresh / Re-index Knowledge Base"):
        # Clear cached index
        if "index" in st.session_state:
            del st.session_state["index"]

        # Delete old storage
        if os.path.exists(PERSIST_DIR):
            shutil.rmtree(PERSIST_DIR)

        st.rerun()


# ---------------------- LlamaIndex Settings ---------------------------------- #
@st.cache_resource
def get_settings():
    llm = Ollama(model=LLM_MODEL, request_timeout=300.0)
    embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)

    Settings.llm = llm
    Settings.embed_model = embed_model
    return llm, embed_model


llm, embed_model = get_settings()


# ------------------------- Load or Create Index ------------------------------ #
@st.cache_resource(show_spinner=False)
def load_index():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        return None

    files = os.listdir(DATA_DIR)
    if not files:
        return None

    with st.spinner("📚 Loading & indexing documents... Please wait..."):
        # Use existing index if available
        if os.path.exists(PERSIST_DIR):
            try:
                storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
                index = load_index_from_storage(storage_context)
                return index
            except:
                pass

        # Fresh indexing
        documents = SimpleDirectoryReader(DATA_DIR).load_data()
        index = VectorStoreIndex.from_documents(documents)

        # Persist
        index.storage_context.persist(persist_dir=PERSIST_DIR)
        return index


# Initialize Index
if "index" not in st.session_state:
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


