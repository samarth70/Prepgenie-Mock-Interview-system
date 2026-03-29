import { create } from 'zustand';
import { interviewAPI, InterviewSession } from '../services/api';

interface InterviewState {
  // State
  session: InterviewSession | null;
  currentQuestion: string | null;
  questionNumber: number;
  totalQuestions: number;
  isInterviewActive: boolean;
  isInterviewComplete: boolean;
  resumeText: string;
  selectedRoles: string[];
  
  // UI State
  isLoading: boolean;
  error: string | null;
  feedback: string | null;
  currentMetrics: Record<string, number> | null;
  
  // Actions
  setResumeText: (text: string) => void;
  setSelectedRoles: (roles: string[]) => void;
  startInterview: (roles: string[], resumeText: string) => Promise<void>;
  submitAnswer: (answerText: string) => Promise<{ isComplete: boolean; nextQuestion: string | null }>;
  submitFinalInterview: () => Promise<{ 
    evaluation: string; 
    metrics: Record<string, number>; 
    averageRating: number;
    is_fallback: boolean;
    question_feedback?: any[];
    strengths?: string[];
    improvements?: string[];
  }>;
  resetInterview: () => void;
  setError: (error: string | null) => void;
}

export const useInterviewStore = create<InterviewState>((set, get) => ({
  // Initial State
  session: null,
  currentQuestion: null,
  questionNumber: 0,
  totalQuestions: 5,
  isInterviewActive: false,
  isInterviewComplete: false,
  resumeText: '',
  selectedRoles: [],
  isLoading: false,
  error: null,
  feedback: null,
  currentMetrics: null,

  setResumeText: (text) => set({ resumeText: text }),
  
  setSelectedRoles: (roles) => set({ selectedRoles: roles }),
  
  startInterview: async (roles, resumeText) => {
    set({ isLoading: true, error: null });
    try {
      const data = await interviewAPI.startInterview(roles, resumeText);
      set({
        session: data,
        currentQuestion: data.question,
        questionNumber: data.question_number,
        totalQuestions: data.total_questions,
        isInterviewActive: true,
        isInterviewComplete: false,
        selectedRoles: roles,
        resumeText,
        isLoading: false,
      });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Failed to start interview',
        isLoading: false,
      });
      throw err;
    }
  },

  submitAnswer: async (answerText) => {
    const { session } = get();
    if (!session) throw new Error('No active session');
    
    set({ isLoading: true, error: null });
    try {
      const data = await interviewAPI.submitAnswer(session.session_id, answerText);
      set({
        feedback: data.feedback,
        currentMetrics: data.metrics,
        currentQuestion: data.next_question,
        questionNumber: data.question_number || get().questionNumber + 1,
        isLoading: false,
      });
      
      if (data.is_complete) {
        set({ isInterviewComplete: true, isInterviewActive: false });
      }
      
      return { isComplete: data.is_complete, nextQuestion: data.next_question };
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Failed to submit answer',
        isLoading: false,
      });
      throw err;
    }
  },

  submitFinalInterview: async () => {
    const { session } = get();
    if (!session) throw new Error('No active session');
    
    set({ isLoading: true, error: null });
    try {
      const data = await interviewAPI.submitInterview(session.session_id);
      set({
        isLoading: false,
        isInterviewComplete: true,
      });
      return {
        evaluation: data.evaluation,
        metrics: data.metrics,
        averageRating: data.average_rating,
        is_fallback: data.is_fallback || false,
        question_feedback: data.question_feedback || [],
        strengths: data.strengths || [],
        improvements: data.improvements || [],
      };
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Failed to submit interview',
        isLoading: false,
      });
      throw err;
    }
  },

  resetInterview: () => {
    set({
      session: null,
      currentQuestion: null,
      questionNumber: 0,
      totalQuestions: 5,
      isInterviewActive: false,
      isInterviewComplete: false,
      resumeText: '',
      selectedRoles: [],
      isLoading: false,
      error: null,
      feedback: null,
      currentMetrics: null,
    });
  },

  setError: (error) => set({ error }),
}));
