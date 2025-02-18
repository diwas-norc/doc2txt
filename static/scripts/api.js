class DocumentAPI {
    static getHeaders() {
        const headers = new Headers();
        if (DOC2TXT_CONFIG.env.apiKey) {
            headers.append('x-api-key', DOC2TXT_CONFIG.env.apiKey);
        }
        // Add common headers for CORS
        headers.append('Accept', 'application/json');
        return headers;
    }

    static getRequestOptions(options = {}) {
        return {
            mode: DOC2TXT_CONFIG.env.corsMode,
            ...options,
            headers: {
                ...this.getHeaders(),
                ...(options.headers || {})
            }
        };
    }

    static async uploadDocument(file, mode) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(
                `${DOC2TXT_CONFIG.getEndpointUrl(DOC2TXT_CONFIG.endpoints.process)}?mode=${mode}`,
                this.getRequestOptions({
                    method: 'POST',
                    body: formData,
                    headers: {
                        // Don't set Content-Type for FormData, browser will set it with boundary
                    }
                })
            );

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            return data.data.request_id;
        } catch (error) {
            throw new Error(`Upload failed: ${error.message}`);
        }
    }

    static async checkStatus(requestId) {
        try {
            const response = await fetch(
                `${DOC2TXT_CONFIG.getEndpointUrl(DOC2TXT_CONFIG.endpoints.status)}?request_id=${requestId}`,
                this.getRequestOptions({
                    method: 'GET'
                })
            );
            
            if (!response.ok) {
                throw new Error(`Status check failed: ${response.statusText}`);
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            return {
                status: data.data.status,
                message: data.message
            };
        } catch (error) {
            throw new Error(`Status check failed: ${error.message}`);
        }
    }

    static async downloadResult(requestId) {
        try {
            const response = await fetch(
                `${DOC2TXT_CONFIG.getEndpointUrl(DOC2TXT_CONFIG.endpoints.download)}?request_id=${requestId}`,
                this.getRequestOptions({
                    method: 'GET'
                })
            );
            
            if (!response.ok) {
                throw new Error(`Download failed: ${response.statusText}`);
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            return data.data.content;
        } catch (error) {
            throw new Error(`Download failed: ${error.message}`);
        }
    }

    static async cancelProcessing(requestId) {
        try {
            const response = await fetch(
                `${DOC2TXT_CONFIG.getEndpointUrl(DOC2TXT_CONFIG.endpoints.cancel)}?request_id=${requestId}`,
                this.getRequestOptions({
                    method: 'POST'
                })
            );
            
            if (!response.ok) {
                throw new Error(`Cancellation failed: ${response.statusText}`);
            }

            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            return {
                status: data.data.status,
                message: data.message
            };
        } catch (error) {
            throw new Error(`Cancellation failed: ${error.message}`);
        }
    }
} 