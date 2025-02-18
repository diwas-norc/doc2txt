// Environment configuration
const ENV = {
    dev: {
        baseUrl: '',  // Local development Azure Functions
        apiKey: '',  // Add API key if needed for development
        corsMode: 'cors',  // Enable CORS for development
        origin: 'http://localhost:8000'  // Development frontend origin
    },
    prod: {
        baseUrl: 'https://api.example.com/api',  // Replace with actual production URL
        apiKey: '',  // Add API key if needed for production
        corsMode: 'cors',  // Enable CORS for production
        origin: 'https://your-production-domain.com'  // Production frontend origin
    }
};

// Current environment - can be switched between 'dev' and 'prod'
const CURRENT_ENV = 'dev';

const DOC2TXT_CONFIG = {
    // Environment settings
    env: ENV[CURRENT_ENV],
    
    // API endpoints
    endpoints: {
        process: '/ProcessDocument',
        status: '/CheckStatus',
        download: '/DownloadResult',
        cancel: '/CancelProcessing'
    },
    
    // File upload constraints
    upload: {
        maxSizeBytes: 10 * 1024 * 1024, // 10MB
        allowedTypes: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    },
    
    // Status polling configuration
    polling: {
        interval: 2000, // 2 seconds
        timeout: 300000 // 5 minutes
    },

    // Helper function to get full endpoint URL
    getEndpointUrl: function(endpoint) {
        return this.env.baseUrl + endpoint;
    }
}; 