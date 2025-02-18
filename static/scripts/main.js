// Initialize the document processing interface when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Create session storage for request IDs if it doesn't exist
    if (!sessionStorage.getItem('processingRequests')) {
        sessionStorage.setItem('processingRequests', JSON.stringify([]));
    }

    // Initialize the UI
    const docUI = new DocumentUI();

    // Restore any in-progress requests from session storage
    const requests = JSON.parse(sessionStorage.getItem('processingRequests'));
    if (requests.length > 0) {
        // Resume polling for the most recent request
        const latestRequest = requests[requests.length - 1];
        docUI.requestIdSpan.textContent = latestRequest;
        docUI.showStatus();
        docUI.startPolling(latestRequest);
    }

    // Add request ID to session storage when processing starts
    const originalHandleStartProcessing = docUI.handleStartProcessing;
    docUI.handleStartProcessing = async function() {
        try {
            await originalHandleStartProcessing.call(this);
            const requests = JSON.parse(sessionStorage.getItem('processingRequests'));
            requests.push(this.requestIdSpan.textContent);
            sessionStorage.setItem('processingRequests', JSON.stringify(requests));
        } catch (error) {
            this.showError(error.message);
        }
    };

    // Remove request ID from session storage when processing completes or fails
    const originalShowResults = docUI.showResults;
    const originalShowError = docUI.showError;
    
    docUI.showResults = function(result) {
        originalShowResults.call(this, result);
        removeCurrentRequest();
    };

    docUI.showError = function(message) {
        originalShowError.call(this, message);
        removeCurrentRequest();
    };

    function removeCurrentRequest() {
        const requests = JSON.parse(sessionStorage.getItem('processingRequests'));
        const currentRequest = docUI.requestIdSpan.textContent;
        const index = requests.indexOf(currentRequest);
        if (index > -1) {
            requests.splice(index, 1);
            sessionStorage.setItem('processingRequests', JSON.stringify(requests));
        }
    }
}); 