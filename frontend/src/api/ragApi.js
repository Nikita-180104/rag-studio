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
export const queryRAG = async (question, searchFilter = {}) => {
  try {
    const response = await api.post('/query', {
      question,
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

export default {
  queryRAG,
  clearCache,
  checkHealth,
};
