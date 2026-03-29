import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, MessageSquare, History, ArrowRight, Sparkles, Zap, Shield } from 'lucide-react';

const Home: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: Briefcase,
      title: 'Mock Interviews',
      description: 'AI-powered interviews with 5 personalized questions based on your resume and target role.',
      path: '/interview',
      gradient: 'from-brand-500 to-blue-500',
    },
    {
      icon: MessageSquare,
      title: 'Chat with Resume',
      description: 'Get instant AI feedback and actionable suggestions to level up your resume.',
      path: '/chat',
      gradient: 'from-purple-500 to-pink-500',
    },
    {
      icon: History,
      title: 'Interview History',
      description: 'Track your progress across sessions with persistent analytics and insights.',
      path: '/history',
      gradient: 'from-emerald-500 to-teal-500',
    },
  ];

  const stats = [
    { icon: Zap, value: '5', label: 'AI Questions per Session' },
    { icon: Shield, value: '10+', label: 'Supported Roles' },
    { icon: Sparkles, value: '∞', label: 'Practice Rounds' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero Section */}
      <div className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-20">
        <div className="max-w-5xl mx-auto text-center">
          {/* Badge */}
          <div className="animate-fade-in mb-8">
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium bg-brand-500/10 text-brand-300 border border-brand-500/20">
              <Sparkles className="w-3.5 h-3.5" />
              AI-Powered Interview Prep
            </span>
          </div>

          {/* Title */}
          <h1 className="animate-slide-up text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight mb-6">
            <span className="text-gradient">PrepGenie</span>
          </h1>

          <p className="animate-slide-up text-lg sm:text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed" style={{ animationDelay: '0.1s' }}>
            Practice smarter, not harder. Get personalized mock interviews, 
            real-time AI feedback, and track your growth — all in one place.
          </p>

          {/* CTA */}
          <div className="animate-slide-up flex flex-col sm:flex-row items-center justify-center gap-4" style={{ animationDelay: '0.2s' }}>
            <button
              onClick={() => navigate('/interview')}
              className="btn-primary text-lg px-8 py-4 flex items-center gap-2 animate-glow"
            >
              Start Mock Interview
              <ArrowRight className="w-5 h-5" />
            </button>
            <button
              onClick={() => navigate('/chat')}
              className="btn-ghost text-base"
            >
              Chat with Resume
            </button>
          </div>

          {/* Stats */}
          <div className="animate-slide-up mt-16 grid grid-cols-3 gap-6 max-w-md mx-auto" style={{ animationDelay: '0.3s' }}>
            {stats.map((stat, i) => {
              const Icon = stat.icon;
              return (
                <div key={i} className="text-center">
                  <Icon className="w-5 h-5 text-brand-400 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-slate-100">{stat.value}</div>
                  <div className="text-xs text-slate-500 mt-1">{stat.label}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 stagger">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                onClick={() => navigate(feature.path)}
                className="glass-card-elevated p-7 cursor-pointer group hover:border-brand-500/30 transition-all duration-300 hover:-translate-y-1 animate-slide-up"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-slate-100 mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  {feature.description}
                </p>
                <div className="mt-4 flex items-center text-brand-400 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  Get started <ArrowRight className="w-4 h-4 ml-1" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-auto py-10 border-t border-white/5 bg-slate-950/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center gap-6">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-brand-500" />
            <span className="text-xl font-bold text-gradient">PrepGenie</span>
          </div>
          <p className="text-slate-500 text-sm text-center max-w-sm">
            Empowering professionals with AI-driven interview preparation and resume insights.
          </p>
          <div className="h-px w-20 bg-gradient-to-r from-transparent via-slate-700 to-transparent" />
          <div className="text-slate-400 text-sm font-medium">
            Created by <span className="text-slate-200">Samarth Agarwal</span>
          </div>
          <div className="text-slate-600 text-[10px] uppercase tracking-widest font-bold">
            © 2026 • Edge Native Architecture
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
