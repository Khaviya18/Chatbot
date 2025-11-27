// Use relative path - works automatically on localhost, Render, and Railway
const API_URL = '';

// DOM Elements
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const uploadStatus = document.getElementById('uploadStatus');
const fileList = document.getElementById('fileList');
const reindexBtn = document.getElementById('reindexBtn');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');

// State
let hasIndex = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadFiles();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // File upload
    fileInput.addEventListener('change', handleFileUpload);

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        handleFiles(files);
    });

    // Reindex button
    reindexBtn.addEventListener('click', reindexFiles);

    // Chat input
    chatInput.addEventListener('input', () => {
        autoResize(chatInput);
        sendBtn.disabled = !chatInput.value.trim();
    });

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Send button
    sendBtn.addEventListener('click', sendMessage);
}

// Auto-resize textarea
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// File Upload
async function handleFileUpload(e) {
    const files = e.target.files;
    await handleFiles(files);
    fileInput.value = ''; // Reset input
}

async function handleFiles(files) {
    if (files.length === 0) return;

    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }

    try {
        showStatus('Uploading files...', 'info');
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(data.message, 'success');
            loadFiles();
        } else {
            showStatus(data.error || 'Upload failed', 'error');
        }
    } catch (error) {
        showStatus('Upload failed: ' + error.message, 'error');
    }
}

// Load Files
async function loadFiles() {
    try {
        const response = await fetch(`${API_URL}/files`);
        const data = await response.json();

        displayFiles(data.files);
        hasIndex = data.files.length > 0;
        updateChatState();
    } catch (error) {
        console.error('Failed to load files:', error);
    }
}

// Display Files
function displayFiles(files) {
    if (files.length === 0) {
        fileList.innerHTML = '<p class="empty-state">No files uploaded yet</p>';
        return;
    }

    fileList.innerHTML = files.map(file => `
        <div class="file-item">
            <span class="file-name" title="${file}">${file}</span>
            <button class="btn-delete" onclick="deleteFile('${file}')" title="Delete ${file}">
                ❌
            </button>
        </div>
    `).join('');
}

// Delete File
async function deleteFile(filename) {
    if (!confirm(`Delete ${filename}?`)) return;

    try {
        const response = await fetch(`${API_URL}/files/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(data.message, 'success');
            loadFiles();
        } else {
            showStatus(data.error || 'Delete failed', 'error');
        }
    } catch (error) {
        showStatus('Delete failed: ' + error.message, 'error');
    }
}

// Reindex
async function reindexFiles() {
    try {
        reindexBtn.disabled = true;
        reindexBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
                <polyline points="23 4 23 10 17 10"></polyline>
                <polyline points="1 20 1 14 7 14"></polyline>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
            Indexing...
        `;

        const response = await fetch(`${API_URL}/reindex`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(`✅ Indexed ${data.file_count} file(s), ${data.document_count} document(s)`, 'success');
            hasIndex = data.file_count > 0;
            updateChatState();
        } else {
            showStatus(data.error || 'Reindex failed', 'error');
        }
    } catch (error) {
        showStatus('Reindex failed: ' + error.message, 'error');
    } finally {
        reindexBtn.disabled = false;
        reindexBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"></polyline>
                <polyline points="1 20 1 14 7 14"></polyline>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
            Reindex
        `;
    }
}

// Chat Functions
function updateChatState() {
    if (hasIndex) {
        chatInput.disabled = false;
        chatInput.placeholder = 'Ask something from your documents...';
    } else {
        chatInput.disabled = true;
        chatInput.placeholder = 'Upload documents and reindex to start chatting...';
        sendBtn.disabled = true;
    }
}

async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;

    // Add user message
    addMessage('user', query);
    chatInput.value = '';
    autoResize(chatInput);
    sendBtn.disabled = true;

    // Show typing indicator
    const typingId = addTypingIndicator();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator(typingId);

        if (response.ok) {
            addMessage('assistant', data.response);
        } else {
            addMessage('assistant', `Error: ${data.error}`);
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessage('assistant', `Error: ${error.message}`);
    }
}

function addMessage(role, content) {
    // Remove welcome message if it exists
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = role === 'user' ? '👤' : '🤖';

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <p>${escapeHtml(content)}</p>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.id = 'typing-indicator';

    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return 'typing-indicator';
}

function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) {
        indicator.remove();
    }
}

// Utility Functions
function showStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = `status-message ${type}`;

    setTimeout(() => {
        uploadStatus.className = 'status-message';
    }, 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add CSS for spin animation
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
