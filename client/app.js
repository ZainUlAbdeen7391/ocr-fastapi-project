// Configuration
const API_BASE_URL = 'https://ocr-fastapi-project.onrender.com';
// const API_BASE_URL = 'http://localhost:8000'; // For local testing

// State Management
const state = {
    currentUser: null,
    apiKey: null,
    selectedFiles: [],
    currentTab: 'image',
    isProcessing: false
};

// DOM Elements
const elements = {
    authModal: document.getElementById('authModal'),
    authBtn: document.getElementById('authBtn'),
    closeModal: document.querySelector('.close'),
    loginForm: document.getElementById('loginForm'),
    registerForm: document.getElementById('registerForm'),
    tabBtns: document.querySelectorAll('.tab-btn'),
    userMenu: document.getElementById('userMenu'),
    userEmail: document.getElementById('userEmail'),
    logoutBtn: document.getElementById('logoutBtn'),
    apiStatus: document.getElementById('apiStatus'),
    dropZone: document.getElementById('dropZone'),
    fileInput: document.getElementById('fileInput'),
    filePreview: document.getElementById('filePreview'),
    fileList: document.getElementById('fileList'),
    uploadTabs: document.querySelectorAll('.upload-tab'),
    structuredOptions: document.getElementById('structuredOptions'),
    processBtn: document.getElementById('processBtn'),
    clearBtn: document.getElementById('clearBtn'),
    progressContainer: document.getElementById('progressContainer'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    resultsSection: document.getElementById('resultsSection'),
    extractedText: document.getElementById('extractedText'),
    jsonDisplay: document.getElementById('jsonDisplay'),
    resultTabs: document.querySelectorAll('.result-tab'),
    copyBtn: document.getElementById('copyBtn'),
    downloadBtn: document.getElementById('downloadBtn'),
    apiKeyDisplay: document.getElementById('apiKeyDisplay'),
    toggleApiKey: document.getElementById('toggleApiKey'),
    copyApiKey: document.getElementById('copyApiKey'),
    toastContainer: document.getElementById('toastContainer')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuthStatus();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // Auth Modal
    elements.authBtn.addEventListener('click', () => {
        elements.authModal.style.display = 'block';
    });
    
    elements.closeModal.addEventListener('click', closeAuthModal);
    
    window.addEventListener('click', (e) => {
        if (e.target === elements.authModal) closeAuthModal();
    });

    // Auth Tabs
    elements.tabBtns.forEach(btn => {
        btn.addEventListener('click', () => switchAuthTab(btn.dataset.tab));
    });

    // Forms
    elements.loginForm.addEventListener('submit', handleLogin);
    elements.registerForm.addEventListener('submit', handleRegister);
    elements.logoutBtn.addEventListener('click', handleLogout);

    // File Upload
    elements.dropZone.addEventListener('click', () => elements.fileInput.click());
    elements.dropZone.addEventListener('dragover', handleDragOver);
    elements.dropZone.addEventListener('dragleave', handleDragLeave);
    elements.dropZone.addEventListener('drop', handleDrop);
    elements.fileInput.addEventListener('change', handleFileSelect);

    // Upload Type Tabs
    elements.uploadTabs.forEach(tab => {
        tab.addEventListener('click', () => switchUploadTab(tab.dataset.type));
    });

    // Action Buttons
    elements.processBtn.addEventListener('click', processFiles);
    elements.clearBtn.addEventListener('click', clearAll);

    // Result Tabs
    elements.resultTabs.forEach(tab => {
        tab.addEventListener('click', () => switchResultTab(tab.dataset.view));
    });

    // Copy/Download
    elements.copyBtn.addEventListener('click', copyResults);
    elements.downloadBtn.addEventListener('click', downloadResults);
    elements.toggleApiKey.addEventListener('click', toggleApiKeyVisibility);
    elements.copyApiKey.addEventListener('click', copyApiKeyToClipboard);
}

// Auth Functions
function switchAuthTab(tab) {
    elements.tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    
    if (tab === 'login') {
        elements.loginForm.classList.remove('hidden');
        elements.registerForm.classList.add('hidden');
    } else {
        elements.loginForm.classList.add('hidden');
        elements.registerForm.classList.remove('hidden');
    }
}

function closeAuthModal() {
    elements.authModal.style.display = 'none';
    elements.loginForm.reset();
    elements.registerForm.reset();
    document.getElementById('loginError').textContent = '';
    document.getElementById('registerError').textContent = '';
    document.getElementById('registerSuccess').textContent = '';
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            state.currentUser = data;
            state.apiKey = data.api_usage; // API key info from login response
            localStorage.setItem('ocr_token', data.access_token);
            localStorage.setItem('ocr_user', JSON.stringify(data));
            updateUIForLoggedInUser(data);
            closeAuthModal();
            showToast('Login successful!', 'success');
        } else {
            errorDiv.textContent = data.detail || 'Login failed';
        }
    } catch (error) {
        errorDiv.textContent = 'Network error. Please try again.';
        console.error('Login error:', error);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const full_name = document.getElementById('regName').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const errorDiv = document.getElementById('registerError');
    const successDiv = document.getElementById('registerSuccess');

    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name, email, password })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            successDiv.textContent = `Registration successful! Your API Key: ${data.api_key}`;
            errorDiv.textContent = '';
            showToast('Registration successful! Please login.', 'success');
            setTimeout(() => switchAuthTab('login'), 2000);
        } else {
            errorDiv.textContent = data.detail || 'Registration failed';
            successDiv.textContent = '';
        }
    } catch (error) {
        errorDiv.textContent = 'Network error. Please try again.';
        console.error('Register error:', error);
    }
}

function handleLogout() {
    state.currentUser = null;
    state.apiKey = null;
    localStorage.removeItem('ocr_token');
    localStorage.removeItem('ocr_user');
    updateUIForLoggedOutUser();
    showToast('Logged out successfully', 'info');
}

function checkAuthStatus() {
    const token = localStorage.getItem('ocr_token');
    const user = localStorage.getItem('ocr_user');
    
    if (token && user) {
        state.currentUser = JSON.parse(user);
        state.apiKey = state.currentUser.api_usage;
        updateUIForLoggedInUser(state.currentUser);
    }
}

function updateUIForLoggedInUser(data) {
    elements.authBtn.classList.add('hidden');
    elements.userMenu.classList.remove('hidden');
    elements.userEmail.textContent = data.user?.email || 'User';
    elements.apiStatus.classList.remove('hidden');
    
    // Update quota display
    if (data.api_usage) {
        document.getElementById('planName').textContent = data.api_usage.monthly_limit <= 50 ? 'Free' : 'Pro';
        document.getElementById('usedHits').textContent = data.api_usage.used_hits;
        document.getElementById('remainingHits').textContent = data.api_usage.remaining_hits;
        elements.apiKeyDisplay.value = data.api_usage.api_key || 'N/A';
        
        // Show warning if low quota
        const warningDiv = document.getElementById('quotaWarning');
        if (data.api_usage.warning) {
            warningDiv.textContent = data.api_usage.warning;
            warningDiv.classList.remove('hidden');
        } else {
            warningDiv.classList.add('hidden');
        }
    }
}

function updateUIForLoggedOutUser() {
    elements.authBtn.classList.remove('hidden');
    elements.userMenu.classList.add('hidden');
    elements.apiStatus.classList.add('hidden');
}

// File Handling
function handleDragOver(e) {
    e.preventDefault();
    elements.dropZone.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    elements.dropZone.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    elements.dropZone.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files);
    addFiles(files);
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFiles(files);
}

function addFiles(files) {
    const validTypes = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp', 'application/pdf'];
    
    files.forEach(file => {
        // Check by extension for broader compatibility
        const ext = file.name.toLowerCase().split('.').pop();
        const validExts = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'webp', 'pdf'];
        
        if (validExts.includes(ext)) {
            // Prevent duplicates
            if (!state.selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
                state.selectedFiles.push(file);
            }
        } else {
            showToast(`Invalid file type: ${file.name}`, 'error');
        }
    });
    
    updateFilePreview();
    updateProcessButton();
}

function updateFilePreview() {
    if (state.selectedFiles.length === 0) {
        elements.filePreview.classList.add('hidden');
        return;
    }
    
    elements.filePreview.classList.remove('hidden');
    elements.fileList.innerHTML = state.selectedFiles.map((file, index) => `
        <div class="file-item">
            <i class="fas ${file.type === 'application/pdf' ? 'fa-file-pdf' : 'fa-image'}"></i>
            <div>
                <div class="file-name">${file.name}</div>
                <small class="file-size">${formatFileSize(file.size)}</small>
            </div>
            <i class="fas fa-times remove-file" onclick="removeFile(${index})"></i>
        </div>
    `).join('');
}

function removeFile(index) {
    state.selectedFiles.splice(index, 1);
    updateFilePreview();
    updateProcessButton();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function updateProcessButton() {
    elements.processBtn.disabled = state.selectedFiles.length === 0 || !state.currentUser || state.isProcessing;
}

function switchUploadTab(type) {
    state.currentTab = type;
    elements.uploadTabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.type === type);
    });
    
    // Show/hide structured options
    if (type === 'structured') {
        elements.structuredOptions.classList.remove('hidden');
    } else {
        elements.structuredOptions.classList.add('hidden');
    }
    
    // Update accepted file types
    const acceptTypes = type === 'pdf' ? '.pdf' : '.jpg,.jpeg,.png,.bmp,.tiff,.tif,.webp,.pdf';
    elements.fileInput.setAttribute('accept', acceptTypes);
}

// OCR Processing
async function processFiles() {
    if (state.selectedFiles.length === 0 || !state.currentUser) return;
    
    state.isProcessing = true;
    updateProcessButton();
    elements.progressContainer.classList.remove('hidden');
    elements.resultsSection.classList.add('hidden');
    
    const formData = new FormData();
    state.selectedFiles.forEach(file => formData.append('files', file));
    
    let endpoint = '/extract-images';
    if (state.currentTab === 'pdf') endpoint = '/extract-pdfs';
    if (state.currentTab === 'structured') endpoint = '/ocr/structure';
    
    // Add structuring prompt if applicable
    if (state.currentTab === 'structured') {
        const prompt = document.getElementById('structuringPrompt').value;
        if (prompt) {
            formData.append('structuring_prompt', prompt);
        }
    }
    
    try {
        updateProgress(30, 'Uploading files...');
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'X-API-Key': state.currentUser.api_usage?.api_key || ''
            },
            body: formData
        });
        
        updateProgress(70, 'Processing with OCR...');
        
        const data = await response.json();
        
        updateProgress(100, 'Complete!');
        
        if (response.ok && data.success) {
            displayResults(data);
            showToast('Extraction successful!', 'success');
            
            // Update quota after processing
            if (data.remaining_hits !== undefined) {
                document.getElementById('remainingHits').textContent = data.remaining_hits;
                if (data.warning) {
                    showToast(data.warning, 'warning');
                }
            }
        } else {
            throw new Error(data.message || data.detail?.message || 'Processing failed');
        }
    } catch (error) {
        showToast(error.message, 'error');
        console.error('Processing error:', error);
    } finally {
        state.isProcessing = false;
        updateProcessButton();
        setTimeout(() => {
            elements.progressContainer.classList.add('hidden');
            updateProgress(0, '');
        }, 1000);
    }
}

function updateProgress(percent, text) {
    elements.progressFill.style.width = percent + '%';
    elements.progressText.textContent = text || `Processing... ${percent}%`;
}

function displayResults(data) {
    elements.resultsSection.classList.remove('hidden');
    
    // Handle different response formats
    let textContent = '';
    let jsonContent = {};
    
    if (state.currentTab === 'structured' && data.data) {
        jsonContent = data.data;
        textContent = JSON.stringify(data.data, null, 2);
        
        // Also try to extract text fields for display
        if (data.data.fields) {
            textContent = Object.entries(data.data.fields)
                .map(([key, value]) => `${key}: ${value || 'N/A'}`)
                .join('\n');
        }
        if (data.data.line_items) {
            textContent += '\n\nLine Items:\n' + data.data.line_items.map(item => 
                Object.entries(item).map(([k, v]) => `  ${k}: ${v}`).join(', ')
            ).join('\n');
        }
    } else {
        textContent = data.text || data.data || 'No text extracted';
        jsonContent = data;
    }
    
    elements.extractedText.value = textContent;
    elements.jsonDisplay.textContent = JSON.stringify(jsonContent, null, 2);
    
    // Meta info
    const metaDiv = document.querySelector('.result-meta');
    metaDiv.innerHTML = `
        <strong>Type:</strong> ${data.type || state.currentTab} | 
        <strong>Status:</strong> ${data.success ? 'Success' : 'Failed'} |
        <strong>Time:</strong> ${new Date().toLocaleString()}
    `;
    
    // Scroll to results
    elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function switchResultTab(view) {
    elements.resultTabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.view === view);
    });
    
    document.getElementById('textOutput').classList.toggle('hidden', view !== 'text');
    document.getElementById('jsonOutput').classList.toggle('hidden', view !== 'json');
}

function copyResults() {
    const text = elements.extractedText.value;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    });
}

function downloadResults() {
    const text = elements.extractedText.value;
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ocr-result-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Download started!', 'success');
}

function clearAll() {
    state.selectedFiles = [];
    elements.fileInput.value = '';
    updateFilePreview();
    elements.resultsSection.classList.add('hidden');
    elements.extractedText.value = '';
    elements.jsonDisplay.textContent = '';
    updateProcessButton();
    showToast('Cleared all files', 'info');
}

function toggleApiKeyVisibility() {
    const input = elements.apiKeyDisplay;
    const icon = elements.toggleApiKey.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

function copyApiKeyToClipboard() {
    navigator.clipboard.writeText(elements.apiKeyDisplay.value).then(() => {
        showToast('API Key copied!', 'success');
    });
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <span>${message}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Expose removeFile to global scope for onclick
window.removeFile = removeFile;