import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import Navbar from './components/Navbar';
import MockInterview from './pages/MockInterview';
import ChatWithResume from './pages/ChatWithResume';
import InterviewHistory from './pages/InterviewHistory';
import Home from './pages/Home';

function App() {
  const [activeTab, setActiveTab] = useState<'home' | 'interview' | 'chat' | 'history'>('home');

  return (
    <Router>
      <div className="min-h-screen relative">
        {/* Ambient background effects */}
        <div className="fixed inset-0 -z-10">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-brand-600/8 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-600/6 rounded-full blur-3xl" />
        </div>

        <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
        <Toaster
          position="top-right"
          richColors
          duration={2000}
          theme="dark"
          toastOptions={{
            style: {
              background: '#1e293b',
              border: '1px solid rgba(148, 163, 184, 0.15)',
              color: '#f1f5f9',
            },
          }}
        />

        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/interview" element={<MockInterview />} />
          <Route path="/chat" element={<ChatWithResume />} />
          <Route path="/history" element={<InterviewHistory />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
