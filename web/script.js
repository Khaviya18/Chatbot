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
const themeToggle = document.getElementById('themeToggle');
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');

// State
let hasIndex = false;
let isInitialized = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadFiles();
    setupEventListeners();
    updateChatState();
    initializeTheme();
    isInitialized = true;
});

// Theme Management
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Sidebar Management
function toggleSidebar() {
    sidebar.classList.toggle('collapsed');
    localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
}

// Event Listeners
function setupEventListeners() {
    // Theme toggle
    themeToggle.addEventListener('click', toggleTheme);

    // Sidebar toggle
    sidebarToggle.addEventListener('click', toggleSidebar);

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
        // Enable/disable send button based on input
        sendBtn.disabled = !chatInput.value.trim();
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

    // Attach file button
    const attachBtn = document.getElementById('attachBtn');
    if (attachBtn) {
        attachBtn.addEventListener('click', () => {
            fileInput.click();
        });
    }
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

        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Non-JSON response:', text.substring(0, 200));
            showStatus('Upload failed: Server returned invalid response', 'error');
            return;
        }

        const data = await response.json();

        if (response.ok) {
            showStatus(data.message, 'success');
            loadFiles();
        } else {
            showStatus(data.error || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showStatus('Upload failed: ' + error.message, 'error');
    }
}

// Load Files
async function loadFiles() {
    try {
        const response = await fetch(`${API_URL}/files`);

        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Non-JSON response when loading files:', text.substring(0, 200));
            // Don't block chat if file loading fails
            hasIndex = false;
            if (isInitialized) {
                updateChatState();
            }
            return;
        }

        const data = await response.json();

        displayFiles(data.files);
        hasIndex = data.files.length > 0;
        if (isInitialized) {
            updateChatState();
        }
    } catch (error) {
        console.error('Failed to load files:', error);
        // Don't block chat if file loading fails
        hasIndex = false;
        if (isInitialized) {
            updateChatState();
        }
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

        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Non-JSON response:', text.substring(0, 200));
            showStatus('Delete failed: Server returned invalid response', 'error');
            return;
        }

        const data = await response.json();

        if (response.ok) {
            showStatus(data.message, 'success');
            loadFiles();
        } else {
            showStatus(data.error || 'Delete failed', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
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
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Non-JSON response:', text.substring(0, 200));
            showStatus('Reindex failed: Server returned invalid response. Please check the console.', 'error');
            return;
        }

        const data = await response.json();

        if (response.ok) {
            showStatus(`✅ Indexed ${data.file_count} file(s), ${data.document_count} document(s)`, 'success');
            hasIndex = data.file_count > 0;
            updateChatState();
        } else {
            showStatus(data.error || 'Reindex failed', 'error');
        }
    } catch (error) {
        console.error('Reindex error:', error);
        if (error.message.includes('JSON')) {
            showStatus('Reindex failed: Invalid server response. Please refresh the page and try again.', 'error');
        } else {
            showStatus('Reindex failed: ' + error.message, 'error');
        }
    } finally {
        reindexBtn.disabled = false;
        reindexBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"></polyline>
                <polyline points="1 20 1 14 7 14"></polyline>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
            Refresh
        `;
    }
}

// Chat Functions
function updateChatState() {
    // Always enable chat - files are optional
    chatInput.disabled = false;
    if (hasIndex) {
        chatInput.placeholder = 'Type a message or ask about your documents...';
    } else {
        chatInput.placeholder = 'Type a message...';
    }
    // Enable send button if there's text
    sendBtn.disabled = !chatInput.value.trim();
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

        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Non-JSON response:', text.substring(0, 200));
            removeTypingIndicator(typingId);
            addMessage('assistant', 'Error: Server returned invalid response. Please try again.');
            return;
        }

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator(typingId);

        if (response.ok) {
            addMessage('assistant', data.response);
        } else {
            addMessage('assistant', `Error: ${data.error || 'Unknown error occurred'}`);
        }
    } catch (error) {
        console.error('Chat error:', error);
        removeTypingIndicator(typingId);
        if (error.message.includes('JSON')) {
            addMessage('assistant', 'Error: Invalid server response. Please refresh the page and try again.');
        } else {
            addMessage('assistant', `Error: ${error.message}`);
        }
    } finally {
        // Re-enable send button
        sendBtn.disabled = !chatInput.value.trim();
    }
}

function formatMessageContent(content) {
    // Escape HTML first
    let formatted = escapeHtml(content);

    // Convert code blocks with language identifier (```lang\ncode```)
    formatted = formatted.replace(/```(\w+)?\n?([\s\S]*?)```/g, (match, lang, code) => {
        const language = lang || 'plaintext';
        return `<pre><code class="language-${language}">${code.trim()}</code></pre>`;
    });

    // Convert **bold** to <strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Convert *italic* to <em>
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Convert inline code
    formatted = formatted.replace(/`([^`]+)`/g, '<code class="language-none">$1</code>');

    // Convert newlines to <br>
    formatted = formatted.replace(/\n/g, '<br>');

    return formatted;
}

function addMessage(role, content) {
    // Remove welcome message if it exists
    const welcomeMsg = chatMessages.querySelector('.flex.gap-4');
    if (welcomeMsg && welcomeMsg.innerText.includes("RAG-powered assistant")) {
        welcomeMsg.remove();
    }

    const messageDiv = document.createElement('div');
    const isUser = role === 'user';

    // Container classes
    messageDiv.className = `flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`;

    // Avatar
    const avatar = isUser
        ? `<div class="flex-shrink-0 w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center">
             <i data-lucide="user" class="w-5 h-5 text-white"></i>
           </div>`
        : `<div class="flex-shrink-0 w-10 h-10 rounded-full bg-accent flex items-center justify-center">
             <i data-lucide="bot" class="w-5 h-5 text-foreground"></i>
           </div>`;

    // Content Bubble
    // User: blue bg, white text
    // AI: accent bg, foreground text, border
    const bubbleClass = isUser
        ? 'bg-blue-600 text-white'
        : 'bg-accent border border-border text-foreground';

    // Format content
    const formattedContent = formatMessageContent(content);

    messageDiv.innerHTML = `
        ${avatar}
        <div class="flex-1 ${isUser ? 'flex justify-end' : ''}">
            <div class="inline-block max-w-2xl rounded-2xl px-5 py-3 ${bubbleClass}">
                <div class="whitespace-pre-wrap">${formattedContent}</div>
            </div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Initialize new icons
    lucide.createIcons();

    // Highlight code blocks with Prism
    if (typeof Prism !== 'undefined') {
        Prism.highlightAll();
    }
}

function addTypingIndicator() {
    // Remove welcome message if it exists
    const welcomeMsg = chatMessages.querySelector('.flex.gap-4');
    if (welcomeMsg && welcomeMsg.innerText.includes("RAG-powered assistant")) {
        welcomeMsg.remove();
    }

    const id = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = id;
    typingDiv.className = 'flex gap-4';

    typingDiv.innerHTML = `
        <div class="flex-shrink-0 w-10 h-10 rounded-full bg-accent flex items-center justify-center">
             <i data-lucide="bot" class="w-5 h-5 text-foreground"></i>
        </div>
        <div class="flex-1">
            <div class="inline-block rounded-2xl px-5 py-3 bg-accent border border-border">
                <div class="flex gap-1 h-5 items-center">
                    <div class="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style="animation-delay: 0ms"></div>
                    <div class="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style="animation-delay: 150ms"></div>
                    <div class="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style="animation-delay: 300ms"></div>
                </div>
            </div>
        </div>
    `;

    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Initialize new icons
    lucide.createIcons();

    return id;
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

// Session Cleanup on Tab Close
window.addEventListener('beforeunload', () => {
    // Use sendBeacon for reliable background request on unload
    // This calls /clear-session to delete local files
    navigator.sendBeacon('/clear-session');
});

// Also try to clear on page hide (mobile/modern browsers)
window.addEventListener('pagehide', () => {
    navigator.sendBeacon('/clear-session');
});
