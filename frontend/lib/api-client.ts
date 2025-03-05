/**
 * API client for interacting with the backend services
 */

import { API_CONFIG } from './config';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || API_CONFIG.baseUrl;

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: string;
  error?: string;
}

export interface ValidationResult {
  title: string;
  snippet: string;
  link: string;
}

class ApiClient {
  /**
   * Upload a PDF file for processing
   */
  async uploadPdf(file: File): Promise<{ job_id: string }> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}${API_CONFIG.endpoints.upload}`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'Failed to upload PDF');
    }
    
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Upload failed');
    }
    
    return { job_id: data.job_id };
  }
  
  /**
   * Get the status of a job
   */
  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await fetch(`${API_BASE_URL}${API_CONFIG.endpoints.status}?job_id=${jobId}`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'Failed to get job status');
    }
    
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to get job status');
    }
    
    return data.data;
  }
  
  /**
   * Generate a memo from text
   */
  async generateMemo(text: string, template: string = 'default'): Promise<{ job_id: string }> {
    const response = await fetch(`${API_BASE_URL}${API_CONFIG.endpoints.generateMemo}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, template }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'Failed to generate memo');
    }
    
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to generate memo');
    }
    
    return { job_id: data.job_id };
  }
  
  /**
   * Validate a selection of text
   */
  async validateSelection(text: string): Promise<ValidationResult[]> {
    const response = await fetch(`${API_BASE_URL}${API_CONFIG.endpoints.validateSelection}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'Failed to validate selection');
    }
    
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to validate selection');
    }
    
    return data.results;
  }
  
  /**
   * Clean up a job
   */
  async cleanupJob(jobId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}${API_CONFIG.endpoints.cleanup}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ job_id: jobId }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'Failed to clean up job');
    }
    
    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to clean up job');
    }
  }
}

// Export a singleton instance
export const apiClient = new ApiClient(); 