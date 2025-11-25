# Document Chatbot

A RAG (Retrieval-Augmented Generation) chatbot that answers questions based on your uploaded documents. Choose between local (private) or cloud-based (fast) AI models.

## 🚀 Quick Start

```bash
git clone https://github.com/Khaviya18/Chatbot.git
cd Chatbot
./run.sh
```

The app will open in your browser. Choose your preferred model in the sidebar!

## 🤖 Model Options

### Option 1: Gemini (Cloud) - Recommended for Speed
- **Pros**: Fast responses, no local resources needed
- **Cons**: Requires internet and API key
- **Setup**: 
  1. Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey)
  2. Select "Gemini (Cloud)" in the app sidebar
  3. Paste your API key

### Option 2: Local (Ollama) - Recommended for Privacy
- **Pros**: 100% private, works offline, no API key needed
- **Cons**: Slower, uses laptop resources
- **Setup**:
  1. Install Ollama: `brew install ollama`
  2. Run: `./start_ollama.sh` (downloads model ~1.3GB)
  3. Select "Local (Ollama)" in the app sidebar

## 📖 How to Use

1. **Upload Documents**: Drag and drop PDF/TXT/MD files in the app
2. **Click "Re-index"**: Wait for indexing to complete (shows progress bar)
3. **Start Chatting**: Ask questions about your documents!

## 🛠️ Scripts

- **`./run.sh`** - Start the chatbot application
- **`./start_ollama.sh`** - Start Ollama service and download model (only if using local model)

## 📝 Notes

- Documents are **automatically deleted** when you close the app (for privacy)
- The chatbot **only answers from your documents** - it won't use external knowledge
- Supports PDF, TXT, and MD files
- First-time setup downloads embedding model (~100MB)

## 🔧 Requirements

- Python 3.9-3.12 (auto-detected by `run.sh`)
- For local model: Ollama + llama3.2:1b model
- For Gemini: API key (free tier available)
