# Document-Based Chatbot

A Retrieval‑Augmented Generation (RAG) chatbot that answers questions **only** from the documents you upload.

- **Gemini (Cloud)** – fast, no local resources needed, requires a free Google AI API key.

---

## Quick Start (Beginner Friendly)

1. **Clone the repository**
   ```bash
   git clone https://github.com/Khaviya18/Chatbot.git
   cd Chatbot
   ```
2. **Set up your API Key**
   - Create a `.env` file in the project root:
     ```bash
     touch .env
     ```
   - Open the `.env` file and add your Google Gemini API key:
     ```env
     GEMINI_API_KEY=your_api_key_here
     ```
   - You can get a free key from [Google AI Studio](https://aistudio.google.com/apikey).
   - ⚠️ **If you see a 403 error about a leaked API key**, see [SECURITY.md](SECURITY.md) for instructions on getting a new key.

3. **Run the setup script** – it creates a virtual environment, installs all Python dependencies, and launches the app.
   ```bash
   ./run.sh
   ```
4. Your default browser will open at `http://localhost:8501`.

---

## Model Options

### Gemini (Cloud) – Recommended for Speed
- **Pros:** Very fast responses, no local compute required.
- **Cons:** Requires an internet connection and a Google AI API key.
- **Setup:**
  1. Obtain a free API key from the [Google AI Studio](https://aistudio.google.com/apikey).
  2. Add it to your `.env` file as shown in the Quick Start.
  3. The app will automatically load the key from the backend.

---

## How to Use the App

1. **Upload Documents** – Drag and drop PDF, TXT, or MD files into the upload area.
2. **Re‑index** – Click the **"Refresh / Re‑index Knowledge Base"** button in the sidebar. A progress bar will show the indexing steps.
3. **Chat** – Once indexing finishes, type a question in the chat box and press **Enter**. The bot will answer using only the content of your uploaded files.
4. **View Full Content** – Type **"what is the content"** in the chat to see the full text of all uploaded documents.

> You can re‑index any time you add or remove documents.

---

## Scripts Overview

| Script | Purpose |
|--------|---------|
| `./run.sh` | Detects a compatible Python version, creates/activates a virtual environment, installs all Python packages from `requirements.txt`, and launches the Streamlit app. |

---

## Privacy and Clean‑up

- Uploaded files are stored in a temporary `./data` folder and are automatically deleted when you stop the app (Ctrl +C).
- The chatbot never accesses external knowledge; it answers solely from your documents.

---

## Requirements

- **Python 3.9 – 3.12** (the script auto‑detects a suitable version).
- **For Gemini:** A free Google AI API key.
- An internet connection is required for the first run to download the embedding model (approximately 100 MB).

---

You now have a functional, privacy‑focused chatbot. If you encounter any issues, the console output from `run.sh` provides helpful hints.

Happy chatting!
