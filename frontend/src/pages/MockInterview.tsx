import React, { useState, useRef } from 'react';
import { useInterviewStore } from '../store/interviewStore';
import { interviewAPI } from '../services/api';
import { Upload, Mic, MicOff, Send, CheckCircle, AlertCircle, Loader2, Sparkles, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

const MockInterview: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [resumeProcessed, setResumeProcessed] = useState(false);
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);
  const [answerText, setAnswerText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [evaluation, setEvaluation] = useState<{
    evaluation: string;
    metrics: Record<string, number>;
    averageRating: number;
    is_fallback: boolean;
    question_feedback?: any[];
    strengths?: string[];
    improvements?: string[];
  } | null>(null);

  const mediaRecorderRef = useRef<any>(null);

  const {
    currentQuestion,
    questionNumber,
    totalQuestions,
    isInterviewActive,
    isInterviewComplete,
    isLoading,
    error,
    startInterview,
    submitAnswer,
    submitFinalInterview,
    resetInterview,
  } = useInterviewStore();

  const roleOptions = [
    'Software Engineer', 'Data Scientist', 'Product Manager',
    'Data Analyst', 'Business Analyst', 'Frontend Developer',
    'Backend Developer', 'Full Stack Developer', 'DevOps Engineer', 'ML Engineer',
  ];

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
    } else {
      toast.error('Please upload a PDF file');
    }
  };

  const processResume = async () => {
    if (!file) { toast.error('Please upload a resume first'); return; }
    setIsProcessing(true);
    try {
      await interviewAPI.processResume(file);
      setResumeProcessed(true);
      toast.success('Resume processed successfully!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to process resume');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStartInterview = async () => {
    if (selectedRoles.length === 0) { toast.error('Please select at least one role'); return; }
    setIsStarting(true);
    try {
      const data = await interviewAPI.processResume(file!);
      await startInterview(selectedRoles, data.formatted_text || data.raw_text);
      toast.success('Interview started! Good luck!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to start interview');
    } finally {
      setIsStarting(false);
    }
  };

  const startRecording = async () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      toast.error('Speech recognition is not supported in your browser. Use Chrome or Edge, or type your answer.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    let finalTranscript = '';

    recognition.onstart = () => { setIsRecording(true); toast.success('Listening...'); };

    recognition.onresult = (event: any) => {
      finalTranscript = '';
      let interimTranscript = '';
      for (let i = 0; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }
      setAnswerText((finalTranscript + interimTranscript).trim());
    };

    recognition.onerror = (event: any) => {
      setIsRecording(false);
      const errorMessages: Record<string, string> = {
        'no-speech': 'No speech detected. Please speak clearly.',
        'audio-capture': 'No microphone detected.',
        'not-allowed': 'Microphone permission denied.',
      };
      if (event.error !== 'aborted') {
        toast.error(errorMessages[event.error] || `Speech error: ${event.error}`);
      }
    };

    recognition.onend = () => {
      setIsRecording(false);
      if (answerText.trim()) toast.success('Recording complete!');
    };

    try { recognition.start(); mediaRecorderRef.current = recognition; }
    catch { toast.error('Failed to start recording.'); setIsRecording(false); }
  };

  const stopRecording = () => {
    try { mediaRecorderRef.current?.stop(); } catch {}
    setIsRecording(false);
  };

  const handleSubmitAnswer = async () => {
    if (!answerText.trim()) { toast.error('Please provide an answer'); return; }
    try {
      const result = await submitAnswer(answerText);
      toast.success('Answer submitted!');
      setAnswerText('');
      if (result.isComplete) toast.info('All questions answered! Submit for evaluation.');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to submit answer');
    }
  };

  const handleSubmitInterview = async () => {
    try {
      const result = await submitFinalInterview();
      setEvaluation(result);
      toast.success('Interview evaluated!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to evaluate interview');
    }
  };

  const handleReset = () => {
    resetInterview();
    setFile(null);
    setResumeProcessed(false);
    setSelectedRoles([]);
    setAnswerText('');
    setEvaluation(null);
    toast.info('Ready for a new interview');
  };

  const progress = totalQuestions > 0 ? ((questionNumber) / totalQuestions) * 100 : 0;

  // Helper: color for score
  const scoreColor = (score: number) =>
    score >= 8 ? 'text-emerald-400' : score >= 6 ? 'text-amber-400' : 'text-red-400';
  const scoreBg = (score: number) =>
    score >= 8 ? 'bg-emerald-500/10 border-emerald-500/20' : score >= 6 ? 'bg-amber-500/10 border-amber-500/20' : 'bg-red-500/10 border-red-500/20';

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      <div className="glass-card-elevated p-8">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-blue-500 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-100">Mock Interview</h1>
        </div>

        {/* ── Evaluation Results ── */}
        {evaluation && (
          <div className="space-y-8 animate-slide-up">
            {/* Fallback Warning */}
            {evaluation.is_fallback && (
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 flex items-start gap-4 mb-6">
                <div className="w-10 h-10 rounded-full bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                  <span className="text-xl">⚠️</span>
                </div>
                <div>
                  <h3 className="text-amber-400 font-semibold text-sm mb-1">System Evaluation (AI Offline)</h3>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    Personalized AI analysis is currently unavailable. This is a simplified evaluation based on 
                    response metrics. To enable full AI feedback, please check your API configuration in the backend.
                  </p>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between pb-5 border-b border-white/10">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-6 h-6 text-emerald-400" />
                <h2 className="text-xl font-semibold text-slate-100">Interview Complete</h2>
              </div>
              <div className="text-right">
                <div className={`text-4xl font-bold ${scoreColor(evaluation.averageRating)}`}>
                  {evaluation.averageRating.toFixed(1)}<span className="text-lg text-slate-500">/10</span>
                </div>
                <div className="text-xs text-slate-500 mt-1">Overall Rating</div>
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 stagger">
              {Object.entries(evaluation.metrics).map(([skill, score]) => (
                <div key={skill} className={`metric-badge animate-slide-up ${scoreBg(score)}`}>
                  <div className="text-[10px] text-slate-400 mb-1.5 font-medium leading-tight flex items-end justify-center" title={skill}>
                    {skill}
                  </div>
                  <div className={`text-xl font-bold ${scoreColor(score)}`}>
                    {score.toFixed(1)}
                  </div>
                </div>
              ))}
            </div>

            {/* Question Feedback */}
            {evaluation.question_feedback && evaluation.question_feedback.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-slate-200">Question Analysis</h3>
                {evaluation.question_feedback.map((qf, idx) => (
                  <div key={idx} className="glass-card p-5 space-y-3">
                    <div className="flex items-start justify-between">
                      <h4 className="text-sm font-semibold text-slate-300">Question {idx + 1}</h4>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${scoreBg(qf.score || 0)} ${scoreColor(qf.score || 0)}`}>
                        {(qf.score || 0).toFixed(1)}/10
                      </span>
                    </div>
                    <div className="bg-brand-500/5 rounded-lg p-3 border-l-2 border-brand-500">
                      <p className="text-sm text-slate-300">{qf.question}</p>
                    </div>
                    {qf.answer_summary && (
                      <div className="bg-white/[0.02] rounded-lg p-3">
                        <p className="text-xs font-medium text-slate-500 mb-1">Your Answer</p>
                        <p className="text-sm text-slate-400">{qf.answer_summary}</p>
                      </div>
                    )}
                    {(qf.sample_answer || qf.ideal_answer) && (
                      <div className="bg-emerald-500/5 rounded-lg p-3 border-l-2 border-emerald-500">
                        <p className="text-xs font-medium text-emerald-400 mb-1">💡 Sample Answer</p>
                        <p className="text-sm text-slate-300 leading-relaxed">{qf.sample_answer || qf.ideal_answer}</p>
                      </div>
                    )}
                    {qf.feedback && (
                      <div className="bg-purple-500/5 rounded-lg p-3 border-l-2 border-purple-500">
                        <p className="text-xs font-medium text-purple-400 mb-1">Feedback</p>
                        <p className="text-sm text-slate-400">{qf.feedback}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Strengths & Improvements */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {evaluation.strengths && evaluation.strengths.length > 0 && (
                <div className="glass-card p-5">
                  <h3 className="text-sm font-semibold text-emerald-400 mb-3">✓ Key Strengths</h3>
                  <ul className="space-y-2">
                    {evaluation.strengths.map((s, i) => (
                      <li key={i} className="flex items-start text-sm text-slate-300">
                        <span className="text-emerald-500 mr-2 mt-0.5">•</span>{s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {evaluation.improvements && evaluation.improvements.length > 0 && (
                <div className="glass-card p-5">
                  <h3 className="text-sm font-semibold text-amber-400 mb-3">📈 Areas to Improve</h3>
                  <ul className="space-y-2">
                    {evaluation.improvements.map((imp, i) => (
                      <li key={i} className="flex items-start text-sm text-slate-300">
                        <span className="text-amber-500 mr-2 mt-0.5">→</span>{imp}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Overall */}
            <div className="glass-card p-5">
              <h3 className="text-sm font-semibold text-slate-300 mb-3">Overall Evaluation</h3>
              <div className="text-sm text-slate-400 leading-relaxed whitespace-pre-line">
                {evaluation.evaluation}
              </div>
            </div>

            <button onClick={handleReset} className="btn-primary w-full py-4">
              Start New Interview
            </button>
          </div>
        )}

        {/* ── Interview In Progress ── */}
        {isInterviewActive && currentQuestion && !evaluation && (
          <div className="space-y-6 animate-fade-in">
            {/* Progress */}
            <div className="flex items-center justify-between pb-4 border-b border-white/10">
              <span className="px-3 py-1 bg-brand-500/10 text-brand-300 rounded-full text-sm font-medium border border-brand-500/20">
                Question {questionNumber} of {totalQuestions}
              </span>
              <span className="text-sm text-slate-500">{selectedRoles.join(', ')}</span>
            </div>
            <div className="progress-bar">
              <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
            </div>

            {/* Question Card */}
            <div className="bg-brand-500/5 rounded-xl p-6 border border-brand-500/10">
              <h2 className="text-lg font-medium text-slate-100 leading-relaxed">{currentQuestion}</h2>
            </div>

            {/* Answer Area */}
            <div className="space-y-4">
              <label className="block text-sm font-medium text-slate-400">Your Answer</label>
              <textarea
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                placeholder="Type your answer here or click Record Audio..."
                rows={5}
                className="input-dark resize-none"
              />

              <div className="flex items-center gap-3">
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isInterviewComplete}
                  type="button"
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all border ${
                    isRecording
                      ? 'bg-red-500/10 text-red-400 border-red-500/30 animate-pulse'
                      : 'bg-white/5 text-slate-400 border-white/10 hover:bg-white/10 hover:text-slate-200'
                  } disabled:opacity-40 disabled:cursor-not-allowed`}
                >
                  {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  {isRecording ? 'Stop Recording' : 'Record Audio'}
                </button>

                {isRecording && (
                  <div className="flex items-center gap-2 text-red-400 text-sm">
                    <div className="flex gap-0.5">
                      {[0, 150, 300, 450].map((d) => (
                        <div key={d} className="w-0.5 h-3 bg-red-400 rounded-full animate-pulse" style={{ animationDelay: `${d}ms` }} />
                      ))}
                    </div>
                    Listening...
                  </div>
                )}

                <button
                  onClick={handleSubmitAnswer}
                  disabled={isLoading || !answerText.trim() || isRecording}
                  className="btn-primary flex items-center gap-2 ml-auto"
                >
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  Submit Answer
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Interview Complete — Ready to Submit ── */}
        {isInterviewComplete && !evaluation && (
          <div className="text-center py-16 space-y-6 animate-slide-up">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center mx-auto">
              <CheckCircle className="w-10 h-10 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-100 mb-2">All Questions Answered</h2>
              <p className="text-slate-400">Submit your interview to receive a detailed AI evaluation.</p>
            </div>
            <div className="flex justify-center gap-4">
              <button onClick={handleSubmitInterview} disabled={isLoading} className="btn-primary flex items-center gap-2">
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                {isLoading ? 'Evaluating...' : 'Submit for Evaluation'}
              </button>
              <button onClick={handleReset} className="btn-ghost">Start Over</button>
            </div>
          </div>
        )}

        {/* ── Pre-Interview Setup ── */}
        {!isInterviewActive && !isInterviewComplete && !evaluation && (
          <div className="space-y-8 animate-fade-in">
            {/* Upload */}
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-3">Upload Resume (PDF)</label>
              <div className="flex items-center gap-4">
                <label className="flex-1 cursor-pointer">
                  <div className="border-2 border-dashed border-white/10 rounded-xl p-8 text-center hover:border-brand-500/30 transition-all group">
                    <Upload className="w-8 h-8 text-slate-600 mx-auto mb-3 group-hover:text-brand-400 transition-colors" />
                    <p className="text-sm text-slate-500 group-hover:text-slate-400 transition-colors">
                      {file ? file.name : 'Drop your resume here or click to upload'}
                    </p>
                  </div>
                  <input type="file" accept=".pdf" onChange={handleFileUpload} className="hidden" />
                </label>
                <button onClick={processResume} disabled={!file || isProcessing} className="btn-primary">
                  {isProcessing ? (
                    <span className="flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" />Processing</span>
                  ) : 'Process'}
                </button>
              </div>
            </div>

            {/* Role Selection */}
            {resumeProcessed && (
              <div className="animate-slide-up">
                <label className="block text-sm font-medium text-slate-400 mb-4">Select Target Role(s)</label>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 mb-6">
                  {roleOptions.map((role) => (
                    <button
                      key={role}
                      onClick={() => setSelectedRoles((prev) => prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role])}
                      className={`px-3 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 border ${
                        selectedRoles.includes(role)
                          ? 'bg-brand-500/15 text-brand-300 border-brand-500/30 shadow-sm shadow-brand-500/10'
                          : 'bg-white/[0.02] text-slate-500 border-white/5 hover:bg-white/5 hover:text-slate-300'
                      }`}
                    >
                      {role}
                    </button>
                  ))}
                </div>
                <button
                  onClick={handleStartInterview}
                  disabled={selectedRoles.length === 0 || isLoading || isStarting}
                  className="btn-primary w-full py-4 flex items-center justify-center gap-2"
                >
                  {isLoading || isStarting ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                  Start Interview
                </button>
              </div>
            )}

            {error && (
              <div className="flex items-center p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                <AlertCircle className="w-5 h-5 mr-3 flex-shrink-0" />
                {error}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MockInterview;
