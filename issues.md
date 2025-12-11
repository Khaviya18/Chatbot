# Chatbot Issues & Fixes

## Issue 1: Make RAG-Only (Remove General Conversation Mode)
**Problem**: The chatbot currently supports both general conversation and document Q&A. User wants it to ONLY answer from uploaded documents.

### Sub-tasks:
- [x] Remove user memory system integration from chat endpoint
- [x] Remove conversation history persistence
- [x] Modify chat prompt to be strictly document-focused
- [x] Update UI to indicate documents are required
- [x] Add validation to prevent chat without documents
- [x] Update error messages for no-document scenarios

---

## Issue 2: Clear All Data on Website Close
**Problem**: When the website is closed, all conversation history and documents should be cleared from memory/storage.

### Sub-tasks:
- [x] Implement session-based storage instead of persistent storage
- [x] Clear conversation history on tab/window close event
- [x] Clear uploaded documents from storage on close
- [x] Add beforeunload event listener to handle cleanup
- [x] Ensure backend doesn't persist data between sessions
- [x] Test that refresh maintains data but close doesn't

---

## Issue 3: Fix File Deletion from Knowledge Base
**Problem**: When a file is deleted and refresh is clicked, the chatbot still has information from that document in its knowledge base.

### Sub-tasks:
- [x] Modify file deletion endpoint to immediately remove from active context
- [x] Clear document text cache when file is deleted
- [x] Update reindex logic to rebuild knowledge base from remaining files
- [x] Ensure chat endpoint doesn't use deleted files
- [x] Add validation to check file existence before processing
- [x] Test that deleted files are completely inaccessible

---

## Issue 4: Remove All Local Model Traces
**Problem**: The app still has traces of local model configuration (Ollama, etc.). User wants to use only the API-based model (Gemini).

### Sub-tasks:
- [x] Remove all Ollama-related imports and references
- [x] Remove local model configuration variables
- [x] Clean up any remaining local model code in app.py
- [x] Remove model selection UI from frontend
- [x] Update documentation to reflect API-only approach
- [x] Remove any local model startup scripts

---

## Issue 5: Improve RAG to NotebookLM-like Experience
**Problem**: Current RAG implementation is basic and doesn't feel natural like Google NotebookLM. Need better UX, citations, and conversational abilities.

### Sub-tasks:
- [x] Implement conversational memory within session for follow-up questions
- [x] Add streaming responses with typing indicators
- [x] Implement markdown support for better formatting
- [x] Add dark/light mode toggle
- [x] Create responsive mobile-friendly design
- [x] Add question suggestions based on document content
- [x] Create document preview panel with highlighting
- [ ] Document summarization feature (skipped - not essential for best answers)
- [ ] Hybrid search implementation (skipped - current retrieval is sufficient)

---

## Implementation Notes:
- Focus on Flask app (`app_flask.py`) as main implementation
- Update frontend (`web/`) to reflect RAG-only nature
- Remove or disable memory-related functions
- Ensure proper cleanup on session end
- Test all scenarios thoroughly
