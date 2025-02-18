class DocumentUI {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.selectedFile = null;
    }

    initializeElements() {
        // Sections
        this.uploadSection = document.querySelector('.upload-section');
        this.statusSection = document.querySelector('.status-section');
        this.resultsSection = document.querySelector('.results-section');
        this.errorSection = document.querySelector('.error-section');

        // Upload elements
        this.dropzone = document.getElementById('dropzone');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.fileInput = document.getElementById('fileInput');
        this.processingMode = document.getElementById('processingMode');
        this.startProcessingBtn = document.getElementById('startProcessingBtn');

        // Status elements
        this.statusValue = document.getElementById('statusValue');
        this.requestIdSpan = document.getElementById('requestId');
        this.cancelBtn = document.getElementById('cancelBtn');

        // Results elements
        this.resultsContent = document.getElementById('resultsContent');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.copyBtn = document.getElementById('copyBtn');

        // Error elements
        this.errorMessage = document.getElementById('errorMessage');
        this.retryBtn = document.getElementById('retryBtn');
    }

    bindEvents() {
        // File upload events
        this.dropzone.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.dropzone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.dropzone.addEventListener('drop', (e) => this.handleDrop(e));
        this.uploadBtn.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Button events
        this.cancelBtn.addEventListener('click', () => this.handleCancel());
        this.downloadBtn.addEventListener('click', () => this.handleDownload());
        this.retryBtn.addEventListener('click', () => this.reset());
        this.startProcessingBtn.addEventListener('click', () => this.handleStartProcessing());
        this.copyBtn.addEventListener('click', () => this.handleCopy());
    }

    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        this.dropzone.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        this.dropzone.classList.remove('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        this.dropzone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.validateAndPrepareFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.validateAndPrepareFile(files[0]);
        }
    }

    validateAndPrepareFile(file) {
        if (file.size > DOC2TXT_CONFIG.upload.maxSizeBytes) {
            this.showError('File size exceeds the maximum limit of 10MB');
            return;
        }

        if (!DOC2TXT_CONFIG.upload.allowedTypes.includes(file.type)) {
            this.showError('Invalid file type. Please upload a PDF or Word document.');
            return;
        }

        this.selectedFile = file;
        this.startProcessingBtn.style.display = 'block';
    }

    async handleStartProcessing() {
        if (!this.selectedFile) {
            this.showError('Please select a file first');
            return;
        }

        try {
            this.showStatus();
            const requestId = await DocumentAPI.uploadDocument(this.selectedFile, this.processingMode.value);
            this.requestIdSpan.textContent = requestId;
            this.startPolling(requestId);
        } catch (error) {
            this.showError(error.message);
        }
    }

    async handleCancel() {
        const requestId = this.requestIdSpan.textContent;
        try {
            await DocumentAPI.cancelProcessing(requestId);
            this.reset();
        } catch (error) {
            this.showError(error.message);
        }
    }

    async handleDownload() {
        const text = this.resultsContent.textContent;
        const blob = new Blob([text], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'document.md';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    async handleCopy() {
        try {
            const text = this.resultsContent.textContent;
            await navigator.clipboard.writeText(text);
            // Optional: Add visual feedback
            const originalText = this.copyBtn.innerHTML;
            this.copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
            setTimeout(() => {
                this.copyBtn.innerHTML = originalText;
            }, 2000);
        } catch (error) {
            this.showError('Failed to copy text to clipboard');
        }
    }

    startPolling(requestId) {
        let startTime = Date.now();
        
        const poll = async () => {
            try {
                const status = await DocumentAPI.checkStatus(requestId);
                this.updateStatus(status);

                if (status.status === 'completed') {
                    const result = await DocumentAPI.downloadResult(requestId);
                    this.showResults(result);
                } else if (status.status === 'error') {
                    this.showError(status.message || 'Processing failed');
                } else if (status.status === 'cancelled') {
                    this.reset();
                } else if (Date.now() - startTime < DOC2TXT_CONFIG.polling.timeout) {
                    setTimeout(poll, DOC2TXT_CONFIG.polling.interval);
                } else {
                    this.showError('Processing timeout');
                }
            } catch (error) {
                this.showError(error.message);
            }
        };

        poll();
    }

    updateStatus(status) {
        this.statusValue.textContent = status.status;
        if (status.message) {
            this.statusValue.title = status.message;
        }
    }

    showStatus() {
        this.uploadSection.style.display = 'none';
        this.statusSection.style.display = 'block';
        this.resultsSection.style.display = 'none';
        this.errorSection.style.display = 'none';
    }

    showResults(result) {
        this.uploadSection.style.display = 'none';
        this.statusSection.style.display = 'none';
        this.resultsSection.style.display = 'block';
        this.errorSection.style.display = 'none';
        this.resultsContent.textContent = result;
    }

    showError(message) {
        this.uploadSection.style.display = 'none';
        this.statusSection.style.display = 'none';
        this.resultsSection.style.display = 'none';
        this.errorSection.style.display = 'block';
        this.errorMessage.textContent = message;
    }

    reset() {
        this.uploadSection.style.display = 'block';
        this.statusSection.style.display = 'none';
        this.resultsSection.style.display = 'none';
        this.errorSection.style.display = 'none';
        this.fileInput.value = '';
        this.resultsContent.textContent = '';
        this.selectedFile = null;
        this.startProcessingBtn.style.display = 'none';
    }
} 