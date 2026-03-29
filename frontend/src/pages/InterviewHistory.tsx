import React, { useState, useEffect } from 'react';
import { interviewAPI, InterviewHistory as InterviewHistoryType } from '../services/api';
import { History, TrendingUp, Award, Trash2, Loader2, AlertCircle, RefreshCw, Clock } from 'lucide-react';
import { toast } from 'sonner';

const InterviewHistory: React.FC = () => {
  const [history, setHistory] = useState<InterviewHistoryType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [stats, setStats] = useState({ totalInterviews: 0, averageScore: 0, bestScore: 0 });

  const loadHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await interviewAPI.getHistory();
      setHistory(data.history || []);
      if (data.history && data.history.length > 0) {
        const scores = data.history.map((h: any) => h.average_rating || 0);
        setStats({
          totalInterviews: data.history.length,
          averageScore: scores.reduce((a: number, b: number) => a + b, 0) / scores.length,
          bestScore: Math.max(...scores),
        });
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to load history';
      setError(msg);
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (!confirm('Are you sure you want to clear all history?')) return;
    try {
      await interviewAPI.clearHistory();
      setHistory([]);
      setStats({ totalInterviews: 0, averageScore: 0, bestScore: 0 });
      toast.success('History cleared');
    } catch {
      toast.error('Failed to clear history');
    }
  };

  useEffect(() => { loadHistory(); }, []);

  const scoreColor = (score: number) =>
    score >= 8 ? 'text-emerald-400' : score >= 6 ? 'text-amber-400' : 'text-red-400';
  const scoreBg = (score: number) =>
    score >= 8 ? 'bg-emerald-500/10 border-emerald-500/20' : score >= 6 ? 'bg-amber-500/10 border-amber-500/20' : 'bg-red-500/10 border-red-500/20';

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      <div className="glass-card-elevated p-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
              <History className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-slate-100">Interview History</h1>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={loadHistory} disabled={isLoading} className="btn-ghost flex items-center gap-2 text-sm">
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            {history.length > 0 && (
              <button onClick={handleClearHistory} className="btn-ghost flex items-center gap-2 text-sm !text-red-400 !border-red-500/20 hover:!bg-red-500/10">
                <Trash2 className="w-4 h-4" />
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Statistics Row */}
        {stats.totalInterviews > 0 && (
          <div className="grid grid-cols-3 gap-4 mb-8 stagger">
            {[
              { icon: Clock, label: 'Total Interviews', value: stats.totalInterviews.toString(), color: 'text-brand-400', bg: 'bg-brand-500/10 border-brand-500/20' },
              { icon: TrendingUp, label: 'Average Score', value: `${stats.averageScore.toFixed(1)}/10`, color: scoreColor(stats.averageScore), bg: scoreBg(stats.averageScore) },
              { icon: Award, label: 'Best Score', value: `${stats.bestScore.toFixed(1)}/10`, color: scoreColor(stats.bestScore), bg: scoreBg(stats.bestScore) },
            ].map((stat, i) => {
              const Icon = stat.icon;
              return (
                <div key={i} className={`rounded-xl p-5 border animate-slide-up ${stat.bg}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className={`w-4 h-4 ${stat.color}`} />
                    <span className="text-xs font-medium text-slate-500">{stat.label}</span>
                  </div>
                  <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                </div>
              );
            })}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="flex items-center p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm mb-6">
            <AlertCircle className="w-5 h-5 mr-3" />{error}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && history.length === 0 && !error && (
          <div className="text-center py-20">
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
              <History className="w-8 h-8 text-slate-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-300 mb-2">No History Yet</h3>
            <p className="text-sm text-slate-500">Complete a mock interview to see your results here.</p>
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-brand-400" />
            <span className="ml-3 text-slate-500">Loading history...</span>
          </div>
        )}

        {/* History List */}
        {!isLoading && history.length > 0 && (
          <div className="space-y-4">
            {history.map((interview, index) => (
              <div
                key={interview.session_id || index}
                className="glass-card p-5 cursor-pointer hover:border-brand-500/20 transition-all"
                onClick={() => setExpandedId(expandedId === interview.session_id ? null : interview.session_id)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-slate-200">
                        Interview #{history.length - index}
                      </h3>
                      {interview.is_fallback && (
                        <span className="px-1.5 py-0.5 rounded-md bg-amber-500/10 text-[9px] font-bold text-amber-500 border border-amber-500/20 uppercase tracking-wider">
                          AI Offline
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      {new Date(interview.timestamp).toLocaleString()} · {interview.roles?.join(', ')}
                    </p>
                  </div>
                  <div className={`text-2xl font-bold ${scoreColor(interview.average_rating)}`}>
                    {interview.average_rating.toFixed(1)}<span className="text-sm text-slate-600">/10</span>
                  </div>
                </div>

                {/* Metrics row (compact) */}
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
                  {Object.entries(interview.metrics || {}).map(([skill, score]) => (
                    <div key={skill} className="text-center bg-white/[0.02] rounded-lg py-2 px-1 flex flex-col justify-between min-h-[60px]">
                      <div className="text-[9px] text-slate-500 leading-tight" title={skill}>
                        {skill}
                      </div>
                      <div className={`text-sm font-semibold ${scoreColor(score)}`}>{score.toFixed(1)}</div>
                    </div>
                  ))}
                </div>

                {/* Expanded Details */}
                {expandedId === interview.session_id && (
                  <div className="mt-4 pt-4 border-t border-white/5 space-y-3 animate-fade-in">
                    {Object.entries(interview.interactions || {}).map(([q, a], idx) => (
                      <div key={idx} className="bg-white/[0.02] rounded-lg p-3">
                        <p className="text-xs font-medium text-brand-300 mb-1">Q: {q}</p>
                        <p className="text-xs text-slate-400">A: {a}</p>
                      </div>
                    ))}
                    {interview.evaluation && (
                      <div className="bg-emerald-500/5 rounded-lg p-3 border border-emerald-500/10">
                        <p className="text-xs font-medium text-emerald-400 mb-1">Evaluation</p>
                        <p className="text-xs text-slate-400 leading-relaxed whitespace-pre-line">
                          {interview.evaluation}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default InterviewHistory;
