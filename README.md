# Document-Based Chatbot

A Retrieval‑Augmented Generation (RAG) chatbot that answers questions **only** from the documents you upload. You can choose between two options:

- **Gemini (Cloud)** – fast, no local resources needed, requires a free Google AI API key.
- **Local (Ollama)** – fully private, runs on your machine, no API key required.

---

## Quick Start (Beginner Friendly)

1. **Clone the repository**
   ```bash
   git clone https://github.com/Khaviya18/Chatbot.git
   cd Chatbot
   ```
2. **Run the setup script** – it creates a virtual environment, installs all Python dependencies, and launches the app.
   ```bash
   ./run.sh
   ```
3. Your default browser will open at `http://localhost:8501`.

---

## Model Options

### Gemini (Cloud) – Recommended for Speed
- **Pros:** Very fast responses, no local compute required.
- **Cons:** Requires an internet connection and a Google AI API key.
- **Setup:**
  1. Obtain a free API key from the [Google AI Studio](https://aistudio.google.com/apikey).
  2. In the app sidebar select **"Gemini (Cloud)"**.
  3. Paste your API key into the provided field.

### Local (Ollama) – Recommended for Privacy
- **Pros:** 100 % private, works offline, no API key needed.
- **Cons:** Uses your machine’s CPU/GPU and may be slower.
- **Setup:**
  1. Install Ollama (macOS): `brew install ollama`.
  2. Start Ollama and download the model (about 1.3 GB):
     ```bash
     ./start_ollama.sh
     ```
  3. In the app sidebar select **"Local (Ollama)"**.

---

## How to Use the App

1. **Upload Documents** – Drag and drop PDF, TXT, or MD files into the upload area.
2. **Re‑index** – Click the **"Refresh / Re‑index Knowledge Base"** button in the sidebar. A progress bar will show the indexing steps.
3. **Chat** – Once indexing finishes, type a question in the chat box and press **Enter**. The bot will answer using only the content of your uploaded files.

> You can re‑index any time you add or remove documents.

---

## Scripts Overview

| Script | Purpose |
|--------|---------|
| `./run.sh` | Detects a compatible Python version, creates/activates a virtual environment, installs all Python packages from `requirements.txt`, and launches the Streamlit app. |
| `./start_ollama.sh` | Starts the Ollama service and pulls the `llama3.2:1b` model. **Only needed** when you choose the Local Ollama option. |

---

## Privacy and Clean‑up

- Uploaded files are stored in a temporary `./data` folder and are automatically deleted when you stop the app (Ctrl +C).
- The chatbot never accesses external knowledge; it answers solely from your documents.

---

## Requirements

- **Python 3.9 – 3.12** (the script auto‑detects a suitable version).
- **For the Local model:** Ollama installed (`brew install ollama`).
- **For Gemini:** A free Google AI API key.
- An internet connection is required for the first run to download the embedding model (approximately 100 MB).

---

You now have a functional, privacy‑focused chatbot. If you encounter any issues, the console output from `run.sh` provides helpful hints.

Happy chatting!
