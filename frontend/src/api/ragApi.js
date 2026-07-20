import axios from 'axios';

// Create a centralized Axios instance configured for the localhost FastAPI backend
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000, // Generous timeout to allow local CPU embeddings / LLM backoffs
});

/**
 * Sends a natural language query to the RAG backend.
 * @param {string} question - The user's question
 * @param {object} searchFilter - Optional dynamic metadata filters
 * @returns {Promise<object>} Response data containing answer, citations, contexts, and telemetry
 */
export const queryRAG = async (question, history = [], searchFilter = {}) => {
  try {
    const response = await api.post('/query', {
      question,
      history,
      search_filter: searchFilter,
    });
    return response.data;
  } catch (error) {
    console.error('API queryRAG failed:', error);
    throw error;
  }
};

/**
 * Clears the persistent SQLite query cache on the backend.
 * @returns {Promise<object>} Confirmation message
 */
export const clearCache = async () => {
  try {
    const response = await api.post('/cache/clear');
    return response.data;
  } catch (error) {
    console.error('API clearCache failed:', error);
    throw error;
  }
};

/**
 * Checks the operational health status and config parameters of the backend.
 * @returns {Promise<object>} Health metrics payload
 */
export const checkHealth = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    console.error('API checkHealth failed:', error);
    throw error;
  }
};

/**
 * Uploads a document file to the RAG backend.
 * @param {File} file - The file to upload
 * @param {Function} onUploadProgress - Callback for upload progress events
 * @returns {Promise<object>} Upload response
 */
export const uploadDocument = async (file, onUploadProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
      timeout: 300000, // 5 minutes timeout to allow CPU OCR / indexing of large documents
    });
    return response.data;
  } catch (error) {
    console.error('API uploadDocument failed:', error);
    throw error;
  }
};

/**
 * Fetches the list of indexed documents.
 * @returns {Promise<Array>} List of documents
 */
export const listDocuments = async () => {
  try {
    const response = await api.get('/documents');
    return response.data;
  } catch (error) {
    console.error('API listDocuments failed:', error);
    throw error;
  }
};

/**
 * Deletes a document from the Knowledge Base.
 * @param {string} filename - Name of the file to delete
 * @returns {Promise<object>} Confirmation response
 */
export const deleteDocument = async (filename) => {
  try {
    const response = await api.delete(`/documents/${encodeURIComponent(filename)}`);
    return response.data;
  } catch (error) {
    console.error('API deleteDocument failed:', error);
    throw error;
  }
};

/**
 * Re-indexes a document in the Knowledge Base.
 * @param {string} filename - Name of the file to re-index
 * @returns {Promise<object>} Confirmation response
 */
export const reindexDocument = async (filename) => {
  try {
    const response = await api.post(`/documents/${encodeURIComponent(filename)}/reindex`, {}, {
      timeout: 300000, // 5 minutes timeout to allow CPU OCR / reindexing of large documents
    });
    return response.data;
  } catch (error) {
    console.error('API reindexDocument failed:', error);
    throw error;
  }
};

export default {
  queryRAG,
  clearCache,
  checkHealth,
  uploadDocument,
  listDocuments,
  deleteDocument,
  reindexDocument,
};
