/**
 * Application configuration
 */

// API configuration
export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001',
  endpoints: {
    upload: '/api/upload',
    status: '/api/status',
    generateMemo: '/api/generate-memo',
    validateSelection: '/api/validate-selection',
    cleanup: '/api/cleanup'
  }
}; 