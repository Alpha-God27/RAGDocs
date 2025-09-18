/**
 * RAGDocs Frontend Application
 * Handles UI interactions, API calls, and state management
 */

class RAGDocsApp {
    constructor() {
        this.apiKey = localStorage.getItem('openrouter_api_key') || '';
        this.documents = [];
        this.selectedDocumentId = null;
        this.isProcessing = false;
        
        this.initializeElements();
        this.initializeEventListeners();
        this.checkInitialState();
    }
    
    initializeElements() {
        // API Key elements
        this.apiKeyStatus = document.getElementById('apiKeyStatus');
        this.configureApiBtn = document.getElementById('configureApiBtn');
        this.welcomeConfigureBtn = document.getElementById('welcomeConfigureBtn');
        this.apiKeyModal = document.getElementById('apiKeyModal');
        this.apiKeyInput = document.getElementById('apiKeyInput');
        this.saveApiKeyBtn = document.getElementById('saveApiKeyBtn');
        this.cancelApiKeyBtn = document.getElementById('cancelApiKeyBtn');
        this.apiKeyError = document.getElementById('apiKeyError');
        
        // Document elements
        this.addDocumentBtn = document.getElementById('addDocumentBtn');
        this.welcomeAddDocBtn = document.getElementById('welcomeAddDocBtn');
        this.addDocumentModal = document.getElementById('addDocumentModal');
        this.documentLabelInput = document.getElementById('documentLabelInput');
        this.documentUrlInput = document.getElementById('documentUrlInput');
        this.enableCrawlingInput = document.getElementById('enableCrawlingInput');
        this.maxPagesInput = document.getElementById('maxPagesInput');
        this.crawlingOptions = document.getElementById('crawlingOptions');
        this.saveDocumentBtn = document.getElementById('saveDocumentBtn');
        this.cancelAddDocBtn = document.getElementById('cancelAddDocBtn');
        this.addDocumentError = document.getElementById('addDocumentError');
        this.addDocumentProgress = document.getElementById('addDocumentProgress');
        this.documentsList = document.getElementById('documentsList');
        this.documentsCount = document.getElementById('documentsCount');
        this.clearAllBtn = document.getElementById('clearAllBtn');
        
        // Chat elements
        this.welcomeScreen = document.getElementById('welcomeScreen');
        this.messagesArea = document.getElementById('messagesArea');
        this.messagesContainer = document.getElementById('messagesContainer');
        this.chatForm = document.getElementById('chatForm');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
    }
    
    initializeEventListeners() {
        // API Key events
        this.configureApiBtn.addEventListener('click', () => this.showApiKeyModal());
        this.welcomeConfigureBtn.addEventListener('click', () => this.showApiKeyModal());
        this.saveApiKeyBtn.addEventListener('click', () => this.saveApiKey());
        this.cancelApiKeyBtn.addEventListener('click', () => this.hideApiKeyModal());
        
        // Document events
        this.addDocumentBtn.addEventListener('click', () => this.showAddDocumentModal());
        this.welcomeAddDocBtn.addEventListener('click', () => this.showAddDocumentModal());
        this.saveDocumentBtn.addEventListener('click', () => this.addDocument());
        this.cancelAddDocBtn.addEventListener('click', () => this.hideAddDocumentModal());
        this.clearAllBtn.addEventListener('click', () => this.clearAllDocuments());
        
        // Crawling options toggle
        this.enableCrawlingInput.addEventListener('change', () => this.toggleCrawlingOptions());
        
        // Chat events
        this.chatForm.addEventListener('submit', (e) => this.handleChatSubmit(e));
        
        // Close modals on outside click
        this.apiKeyModal.addEventListener('click', (e) => {
            if (e.target === this.apiKeyModal) this.hideApiKeyModal();
        });
        this.addDocumentModal.addEventListener('click', (e) => {
            if (e.target === this.addDocumentModal) this.hideAddDocumentModal();
        });
    }
    
    async checkInitialState() {
        this.updateApiKeyStatus();
        await this.loadDocuments();
        this.updateUI();
    }
    
    updateApiKeyStatus() {
        const hasApiKey = this.apiKey && this.apiKey.length > 0;
        
        if (hasApiKey) {
            this.apiKeyStatus.innerHTML = `
                <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                <span class="text-slate-600">API key configured</span>
                <button id="configureApiBtn" class="ml-auto text-blue-600 hover:text-blue-700 text-xs font-medium">
                    Change
                </button>
            `;
        } else {
            this.apiKeyStatus.innerHTML = `
                <div class="w-2 h-2 bg-red-500 rounded-full"></div>
                <span class="text-slate-600">API key not configured</span>
                <button id="configureApiBtn" class="ml-auto text-blue-600 hover:text-blue-700 text-xs font-medium">
                    Configure
                </button>
            `;
        }
        
        // Reattach event listener
        this.configureApiBtn = document.getElementById('configureApiBtn');
        this.configureApiBtn.addEventListener('click', () => this.showApiKeyModal());
    }
    
    updateUI() {
        const hasApiKey = this.apiKey && this.apiKey.length > 0;
        const hasDocuments = this.documents.length > 0;
        
        // Enable/disable chat input
        this.messageInput.disabled = !hasApiKey || !hasDocuments;
        this.sendButton.disabled = !hasApiKey || !hasDocuments;
        
        // Update placeholder text
        if (!hasApiKey) {
            this.messageInput.placeholder = "Configure API key to start chatting...";
        } else if (!hasDocuments) {
            this.messageInput.placeholder = "Add documents to start chatting...";
        } else {
            this.messageInput.placeholder = "Ask a question about your documents...";
        }
        
        // Show/hide welcome screen
        if (hasApiKey && hasDocuments && this.messagesArea.children.length === 0) {
            this.welcomeScreen.classList.add('hidden');
            this.messagesArea.classList.remove('hidden');
        } else if (!hasApiKey || !hasDocuments) {
            this.welcomeScreen.classList.remove('hidden');
            this.messagesArea.classList.add('hidden');
        }
        
        // Update documents count
        this.documentsCount.textContent = this.documents.length;
    }
    
    showApiKeyModal() {
        this.apiKeyInput.value = this.apiKey;
        this.apiKeyError.classList.add('hidden');
        this.apiKeyModal.classList.remove('hidden');
        this.apiKeyModal.classList.add('flex');
        this.apiKeyInput.focus();
    }
    
    hideApiKeyModal() {
        this.apiKeyModal.classList.add('hidden');
        this.apiKeyModal.classList.remove('flex');
    }
    
    async saveApiKey() {
        const apiKey = this.apiKeyInput.value.trim();
        
        if (!apiKey) {
            this.showApiKeyError('Please enter an API key');
            return;
        }
        
        // Show loading state
        this.saveApiKeyBtn.disabled = true;
        this.saveApiKeyBtn.textContent = 'Validating...';
        
        try {
            const response = await fetch('/api/validate-key', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.valid) {
                this.apiKey = apiKey;
                localStorage.setItem('openrouter_api_key', apiKey);
                this.updateApiKeyStatus();
                this.updateUI();
                this.hideApiKeyModal();
                this.showSuccess('API key validated and saved successfully!');
            } else {
                this.showApiKeyError(data.message || 'Invalid API key');
            }
        } catch (error) {
            this.showApiKeyError('Failed to validate API key. Please check your connection.');
        } finally {
            this.saveApiKeyBtn.disabled = false;
            this.saveApiKeyBtn.textContent = 'Save & Validate';
        }
    }
    
    showApiKeyError(message) {
        this.apiKeyError.textContent = message;
        this.apiKeyError.classList.remove('hidden');
    }
    
    showAddDocumentModal() {
        if (!this.apiKey) {
            this.showApiKeyModal();
            return;
        }
        
        this.documentLabelInput.value = '';
        this.documentUrlInput.value = '';
        this.enableCrawlingInput.checked = true;
        this.maxPagesInput.value = '10';
        this.toggleCrawlingOptions();
        this.addDocumentError.classList.add('hidden');
        this.addDocumentProgress.classList.add('hidden');
        this.addDocumentModal.classList.remove('hidden');
        this.addDocumentModal.classList.add('flex');
        this.documentLabelInput.focus();
    }
    
    toggleCrawlingOptions() {
        if (this.enableCrawlingInput.checked) {
            this.crawlingOptions.classList.remove('hidden');
        } else {
            this.crawlingOptions.classList.add('hidden');
        }
    }
    
    hideAddDocumentModal() {
        this.addDocumentModal.classList.add('hidden');
        this.addDocumentModal.classList.remove('flex');
    }
    
    async addDocument() {
        const label = this.documentLabelInput.value.trim();
        const url = this.documentUrlInput.value.trim();
        const enableCrawling = this.enableCrawlingInput.checked;
        const maxPages = parseInt(this.maxPagesInput.value);
        
        if (!label || !url) {
            this.showAddDocumentError('Please enter both label and URL');
            return;
        }
        
        // Validate URL format
        try {
            new URL(url);
        } catch {
            this.showAddDocumentError('Please enter a valid URL');
            return;
        }
        
        // Show loading state
        this.saveDocumentBtn.disabled = true;
        this.addDocumentError.classList.add('hidden');
        this.addDocumentProgress.classList.remove('hidden');
        
        // Update progress message for crawling
        const progressElement = this.addDocumentProgress.querySelector('span');
        if (enableCrawling) {
            progressElement.textContent = 'Discovering and processing pages...';
        } else {
            progressElement.textContent = 'Processing document...';
        }
        
        try {
            const response = await fetch('/api/index-document', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    label, 
                    url, 
                    enable_crawling: enableCrawling,
                    max_pages: maxPages
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                await this.loadDocuments();
                this.hideAddDocumentModal();
                this.updateUI();
                
                // Show success message with details
                const pagesText = data.pages_crawled > 1 ? `${data.pages_crawled} pages` : '1 page';
                this.showSuccess(
                    `Document "${label}" added successfully! ` +
                    `Processed ${pagesText} and created ${data.chunks_count} text chunks.`
                );
            } else {
                this.showAddDocumentError(data.detail || 'Failed to add document');
            }
        } catch (error) {
            this.showAddDocumentError('Failed to add document. Please check your connection.');
        } finally {
            this.saveDocumentBtn.disabled = false;
            this.addDocumentProgress.classList.add('hidden');
        }
    }
    
    showAddDocumentError(message) {
        this.addDocumentError.textContent = message;
        this.addDocumentError.classList.remove('hidden');
    }
    
    async loadDocuments() {
        try {
            const response = await fetch('/api/documents');
            const data = await response.json();
            
            this.documents = data.documents || [];
            this.renderDocuments();
        } catch (error) {
            console.error('Failed to load documents:', error);
        }
    }
    
    renderDocuments() {
        if (this.documents.length === 0) {
            this.documentsList.innerHTML = `
                <div class="text-center text-slate-400 text-sm py-8">
                    <svg class="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p>No documents indexed</p>
                    <p class="text-xs mt-1">Add a URL to get started</p>
                </div>
            `;
            return;
        }
        
        this.documentsList.innerHTML = this.documents.map(doc => `
            <div class="document-item p-3 rounded-lg border border-slate-200 hover:border-slate-300 cursor-pointer ${this.selectedDocumentId === doc.document_id ? 'selected' : ''}" 
                 data-document-id="${doc.document_id}">
                <div class="flex items-start justify-between">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-1">
                            <svg class="w-4 h-4 text-slate-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.72"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.72-1.72"></path>
                            </svg>
                            <span class="font-medium text-sm truncate">${doc.label}</span>
                            ${(doc.pages_count && doc.pages_count > 1) ? `<span class="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">${doc.pages_count} pages</span>` : ''}
                        </div>
                        <div class="text-xs text-slate-500 truncate">${doc.url}</div>
                        <div class="text-xs text-slate-400 mt-1">${doc.chunks_count} chunks</div>
                    </div>
                    <button class="delete-doc-btn ml-2 p-1 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100" 
                            data-document-id="${doc.document_id}">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `).join('');
        
        // Add event listeners
        this.documentsList.querySelectorAll('.document-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.delete-doc-btn')) {
                    this.selectDocument(item.dataset.documentId);
                }
            });
        });
        
        this.documentsList.querySelectorAll('.delete-doc-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteDocument(btn.dataset.documentId);
            });
        });
        
        // Auto-select first document if none selected
        if (!this.selectedDocumentId && this.documents.length > 0) {
            this.selectDocument(this.documents[0].document_id);
        }
    }
    
    selectDocument(documentId) {
        this.selectedDocumentId = documentId;
        this.renderDocuments();
    }
    
    async deleteDocument(documentId) {
        if (!confirm('Are you sure you want to delete this document?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/documents/${documentId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                if (this.selectedDocumentId === documentId) {
                    this.selectedDocumentId = null;
                }
                await this.loadDocuments();
                this.updateUI();
                this.showSuccess('Document deleted successfully');
            } else {
                throw new Error('Failed to delete document');
            }
        } catch (error) {
            this.showError('Failed to delete document');
        }
    }
    
    async clearAllDocuments() {
        if (!confirm('Are you sure you want to delete all documents?')) {
            return;
        }
        
        try {
            // Delete each document individually
            for (const doc of this.documents) {
                await fetch(`/api/documents/${doc.document_id}`, {
                    method: 'DELETE'
                });
            }
            
            this.selectedDocumentId = null;
            await this.loadDocuments();
            this.updateUI();
            this.showSuccess('All documents deleted successfully');
        } catch (error) {
            this.showError('Failed to delete all documents');
        }
    }
    
    async handleChatSubmit(e) {
        e.preventDefault();
        
        const message = this.messageInput.value.trim();
        if (!message || this.isProcessing) return;
        
        this.isProcessing = true;
        this.messageInput.value = '';
        this.sendButton.disabled = true;
        
        // Add user message
        this.addMessage('user', message);
        
        // Add loading message
        const loadingId = this.addMessage('assistant', 'Thinking...', true);
        
        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: message,
                    document_id: this.selectedDocumentId
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.updateMessage(loadingId, data.answer);
                
                // Add sources if available
                if (data.sources && data.sources.length > 0) {
                    this.addSourcesMessage(data.sources);
                }
            } else {
                this.updateMessage(loadingId, `Error: ${data.detail || 'Failed to get response'}`);
            }
        } catch (error) {
            this.updateMessage(loadingId, 'Sorry, I encountered an error while processing your request.');
        } finally {
            this.isProcessing = false;
            this.sendButton.disabled = false;
        }
    }
    
    addMessage(role, content, isLoading = false) {
        const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        const messageDiv = document.createElement('div');
        messageDiv.id = messageId;
        messageDiv.className = `message p-4 rounded-lg ${role}-message ${isLoading ? 'loading-dots' : ''}`;
        messageDiv.textContent = content;
        
        this.messagesArea.appendChild(messageDiv);
        this.scrollToBottom();
        
        return messageId;
    }
    
    updateMessage(messageId, content) {
        const messageEl = document.getElementById(messageId);
        if (messageEl) {
            messageEl.textContent = content;
            messageEl.classList.remove('loading-dots');
        }
    }
    
    addSourcesMessage(sources) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'text-xs text-slate-500 mt-2 p-3 bg-slate-50 rounded border-l-4 border-blue-200';
        
        sourcesDiv.innerHTML = `
            <div class="font-medium mb-2">Sources:</div>
            ${sources.slice(0, 3).map(source => `
                <div class="mb-1">
                    <a href="${source.document_url}" target="_blank" class="text-blue-600 hover:underline">
                        ${source.document_title || 'Document'}
                    </a>
                    <span class="text-slate-400"> (score: ${source.similarity_score.toFixed(3)})</span>
                </div>
            `).join('')}
        `;
        
        this.messagesArea.appendChild(sourcesDiv);
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        // Simple notification - you could replace this with a more sophisticated toast system
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg text-white ${
            type === 'success' ? 'bg-green-600' : 
            type === 'error' ? 'bg-red-600' : 'bg-blue-600'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ragDocsApp = new RAGDocsApp();
});