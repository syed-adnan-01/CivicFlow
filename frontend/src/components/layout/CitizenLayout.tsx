import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { Layers, Calendar, Bot, FileText, LogOut, User } from 'lucide-react';
import { clsx } from 'clsx';

export const CitizenLayout: React.FC = () => {
  const { profile, signOut } = useAuth();
  const location = useLocation();

  const navLinks = [
    { to: '/citizen/services', label: 'Services', icon: <Layers className="w-4 h-4" /> },
    { to: '/citizen/appointments', label: 'My Appointments', icon: <Calendar className="w-4 h-4" /> },
    { to: '/citizen/assistant', label: 'AI Assistant', icon: <Bot className="w-4 h-4" /> },
    { to: '/citizen/documents', label: 'Document Check', icon: <FileText className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-civic-50 text-slate-900 font-sans">
      <header className="border-b border-civic-200 bg-white sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            <div className="flex items-center gap-8">
              <Link to="/citizen" className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-forest-700 text-gold-300 flex items-center justify-center border border-forest-800 shadow-sm">
                  <Layers className="w-5 h-5 text-gold-300" />
                </div>
                <div className="flex flex-col">
                  <span className="text-xl font-black text-forest-900 leading-none">CivicFlow</span>
                  <span className="text-[10px] font-bold text-civic-700 uppercase tracking-widest mt-1">Citizen Portal</span>
                </div>
              </Link>

              <nav className="hidden md:flex items-center gap-2">
                {navLinks.map((link) => {
                  const isActive = location.pathname.startsWith(link.to);
                  return (
                    <Link
                      key={link.to}
                      to={link.to}
                      className={clsx(
                        'flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all duration-150',
                        isActive
                          ? 'bg-forest-700 text-white shadow-civic-sm'
                          : 'text-slate-700 hover:text-black hover:bg-civic-100'
                      )}
                    >
                      {link.icon}
                      <span>{link.label}</span>
                    </Link>
                  );
                })}
              </nav>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2.5 text-xs text-slate-900 bg-civic-100 px-4 py-2 rounded-full border border-civic-300 shadow-sm">
                <User className="w-4 h-4 text-forest-700" />
                <span className="font-extrabold">{profile?.display_name || profile?.phone_number || 'Citizen'}</span>
                <span className="bg-gold-200 text-gold-950 px-2.5 py-0.5 rounded-full font-black uppercase text-[10px] tracking-wider border border-gold-400">
                  Citizen
                </span>
              </div>
              <button
                onClick={signOut}
                title="Sign Out"
                className="p-2.5 text-slate-500 hover:text-rose-700 hover:bg-rose-50 rounded-xl transition-colors border border-transparent hover:border-rose-200"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-civic-200 bg-white py-5 text-center text-xs text-slate-500 font-semibold">
        CivicFlow 2.3 — Government Citizen Visit Coordination
      </footer>
    </div>
  );
};
