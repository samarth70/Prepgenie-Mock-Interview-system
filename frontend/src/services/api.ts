import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface InterviewSession {
  session_id: string;
  roles: string[];
  resume_text: string;
  questions: string[];
  current_question_index: number;
  answers: string[];
  interactions: Record<string, string>;
  feedback: string[];
  metrics_list: Record<string, number>[];
  status: 'active' | 'completed';
}

export interface InterviewHistory {
  session_id: string;
  timestamp: string;
  roles: string[];
  interactions: Record<string, string>;
  feedback: string[];
  metrics: Record<string, number>;
  average_rating: number;
  evaluation: string;
  is_fallback?: boolean;
}

export const interviewAPI = {
  /**
   * Process resume PDF
   */
  processResume: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/process-resume', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  /**
   * Start a new interview session
   */
  startInterview: async (roles: string[], resumeText: string) => {
    const response = await api.post('/api/start-interview', {
      roles,
      resume_text: resumeText,
    });
    return response.data;
  },

  /**
   * Submit an answer
   */
  submitAnswer: async (sessionId: string, answerText: string) => {
    const response = await api.post('/api/submit-answer', {
      session_id: sessionId,
      answer_text: answerText,
    });
    return response.data;
  },

  /**
   * Submit completed interview for evaluation
   */
  submitInterview: async (sessionId: string) => {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    
    const response = await api.post('/api/submit-interview', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },

  /**
   * Get interview history
   */
  getHistory: async () => {
    const response = await api.get('/api/interview-history');
    return response.data;
  },

  /**
   * Clear interview history
   */
  clearHistory: async () => {
    const response = await api.delete('/api/clear-history');
    return response.data;
  },

  /**
   * Chat with resume
   */
  chatWithResume: async (resumeText: string, query: string) => {
    const response = await api.post('/api/chat-with-resume', {
      resume_text: resumeText,
      query,
    });
    return response.data;
  },
};

export default api;
