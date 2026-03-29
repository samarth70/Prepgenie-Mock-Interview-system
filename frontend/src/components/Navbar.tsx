import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Briefcase, MessageSquare, History, Sparkles } from 'lucide-react';

interface NavbarProps {
  activeTab: 'home' | 'interview' | 'chat' | 'history';
  setActiveTab: (tab: 'home' | 'interview' | 'chat' | 'history') => void;
}

const Navbar: React.FC<NavbarProps> = ({ setActiveTab }) => {
  const navigate = useNavigate();
  const location = useLocation();

  if (location.pathname === '/') {
    return null;
  }

  const navItems = [
    { id: 'interview' as const, label: 'Mock Interview', icon: Briefcase },
    { id: 'chat' as const, label: 'Chat with Resume', icon: MessageSquare },
    { id: 'history' as const, label: 'History', icon: History },
  ];

  const handleNavClick = (tabId: 'interview' | 'chat' | 'history') => {
    setActiveTab(tabId);
    navigate(`/${tabId}`);
  };

  return (
    <nav className="sticky top-0 z-50 glass-card border-b border-white/5" style={{ borderRadius: 0 }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div
            className="flex items-center cursor-pointer gap-2 group"
            onClick={() => {
              setActiveTab('home');
              navigate('/');
            }}
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div className="flex flex-col">
              <h1 className="text-lg font-bold text-gradient leading-tight">
                PrepGenie
              </h1>
              <span className="text-[10px] text-slate-500 font-medium -mt-1 group-hover:text-slate-400 transition-colors">
                by Samarth Agarwal
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === `/${item.id}`;

              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  className={`
                    flex items-center px-4 py-2 rounded-lg text-sm font-medium
                    transition-all duration-200
                    ${
                      isActive
                        ? 'bg-brand-500/15 text-brand-300 shadow-sm shadow-brand-500/10'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                    }
                  `}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
