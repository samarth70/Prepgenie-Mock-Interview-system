import React, { useState, useRef, useEffect } from 'react';
import { interviewAPI } from '../services/api';
import { Upload, Send, User, Bot, Loader2, AlertCircle, MessageSquare } from 'lucide-react';
import { toast } from 'sonner';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const ChatWithResume: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [resumeText, setResumeText] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError(null);
    } else {
      toast.error('Please upload a PDF file');
    }
  };

  const processResume = async () => {
    if (!file) { toast.error('Please upload a resume first'); return; }
    setIsProcessing(true);
    setError(null);
    try {
      const data = await interviewAPI.processResume(file);
      setResumeText(data.formatted_text || data.raw_text);
      setMessages([{
        role: 'assistant',
        content: "Hi! I've analysed your resume. Ask me anything — I can suggest improvements, identify missing keywords, or help tailor it for a specific role.",
      }]);
      toast.success('Resume processed!');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to process resume';
      setError(msg);
      toast.error(msg);
    } finally {
      setIsProcessing(false);
    }
  };

  const sendMessage = async () => {
    if (!query.trim() || !resumeText) { toast.error('Upload a resume first'); return; }
    const userMessage: Message = { role: 'user', content: query };
    setMessages((prev) => [...prev, userMessage]);
    setQuery('');
    setIsLoading(true);

    try {
      const data = await interviewAPI.chatWithResume(resumeText, query);
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to get response';
      toast.error(msg);
      setMessages((prev) => [...prev, { role: 'assistant', content: `Sorry, I couldn't process that. ${msg}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      <div className="glass-card-elevated p-8">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-100">Chat with Resume</h1>
        </div>

        {/* Upload Section */}
        {!resumeText && (
          <div className="space-y-6 animate-fade-in">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-3">Upload Resume (PDF)</label>
              <div className="flex items-center gap-4">
                <label className="flex-1 cursor-pointer">
                  <div className="border-2 border-dashed border-white/10 rounded-xl p-8 text-center hover:border-purple-500/30 transition-all group">
                    <Upload className="w-8 h-8 text-slate-600 mx-auto mb-3 group-hover:text-purple-400 transition-colors" />
                    <p className="text-sm text-slate-500 group-hover:text-slate-400">
                      {file ? file.name : 'Drop your resume here or click to upload'}
                    </p>
                  </div>
                  <input type="file" accept=".pdf" onChange={handleFileUpload} className="hidden" />
                </label>
                <button onClick={processResume} disabled={!file || isProcessing} className="btn-primary">
                  {isProcessing ? <span className="flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" />Processing</span> : 'Process'}
                </button>
              </div>
            </div>
            {error && (
              <div className="flex items-center p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                <AlertCircle className="w-5 h-5 mr-3" />{error}
              </div>
            )}
          </div>
        )}

        {/* Chat Interface */}
        {resumeText && (
          <div className="flex flex-col h-[550px] animate-fade-in">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto mb-4 space-y-4 p-4 bg-white/[0.02] rounded-xl border border-white/5">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex items-start gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user'
                      ? 'bg-brand-500'
                      : 'bg-gradient-to-br from-purple-500 to-pink-500'
                  }`}>
                    {message.role === 'user' ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
                  </div>
                  <div className={`max-w-[75%] p-4 rounded-xl text-sm leading-relaxed ${
                    message.role === 'user'
                      ? 'bg-brand-500/15 text-brand-200 border border-brand-500/20'
                      : 'glass-card text-slate-300'
                  }`}>
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex items-center gap-2 text-slate-500 text-sm">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  AI is thinking...
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your resume..."
                className="input-dark flex-1"
              />
              <button onClick={sendMessage} disabled={isLoading || !query.trim()} className="btn-primary !px-4">
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatWithResume;
