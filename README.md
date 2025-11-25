# Local RAG Chatbot

This is a local chatbot that answers questions based on your PDF documents.

## Prerequisites

1.  **Ollama**: You must have [Ollama](https://ollama.com/) installed and running.
2.  **Model**: Pull the model you want to use (default is `llama3.2`).
    ```bash
    ollama pull llama3.2
    ```

## Setup

The dependencies are installed in a virtual environment (`venv`).

## Usage

1.  **Add Documents**: Place your PDF files in the `data/` directory.
2.  **Run the App**:
    ```bash
    ./run.sh
    ```
3.  **Chat**: Open the URL shown in the terminal (usually `http://localhost:8501`).

## How to Restart (e.g., after reboot)

1.  Open your terminal.
2.  Start Ollama:
    ```bash
    ollama serve
    ```
3.  Open a **new** terminal tab (Cmd+T).
4.  Navigate to the project folder:
    ```bash
    cd /Users/khaviyasrre/Rag
    ```
5.  Run the app:
    ```bash
    ./run.sh
    ```

## Notes

- The first time you run it, it will download the embedding model (small, ~100MB).
- If you add new files, click the "Refresh/Re-index" button in the sidebar.
- The chatbot is configured to **only** answer from the documents.
- Uses local file storage for the index (in `storage/` folder).
