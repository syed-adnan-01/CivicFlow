import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { Layers, QrCode, MonitorCheck, LogOut, ShieldCheck, Activity } from 'lucide-react';
import { clsx } from 'clsx';

export const OfficerLayout: React.FC = () => {
  const { profile, signOut } = useAuth();
  const location = useLocation();

  const navLinks = [
    { to: '/officer/queue', label: 'Live Queue Board', icon: <MonitorCheck className="w-4 h-4" /> },
    { to: '/officer/check-in', label: 'Check-In Terminal', icon: <QrCode className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-civic-950 text-slate-100 font-sans">
      <header className="border-b border-civic-900 bg-civic-950/90 sticky top-0 z-40 backdrop-blur shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-18">
            <div className="flex items-center gap-8">
              <Link to="/officer" className="flex items-center gap-2.5 text-white font-extrabold text-xl tracking-tight">
                <div className="w-9 h-9 rounded-xl bg-civic-800 text-civic-300 flex items-center justify-center border border-civic-700 shadow-sm">
                  <Layers className="w-5 h-5 text-civic-300" />
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center gap-2">
                    <span className="leading-none font-extrabold">CivicFlow</span>
                    <span className="text-[10px] bg-civic-900 text-civic-300 border border-civic-700 px-2 py-0.5 rounded-full font-mono font-bold tracking-wider">
                      OFFICER
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-civic-400 uppercase tracking-widest mt-0.5">
                    Desk Operations Station
                  </span>
                </div>
              </Link>

              <nav className="flex items-center gap-2">
                {navLinks.map((link) => {
                  const isActive = location.pathname.startsWith(link.to);
                  return (
                    <Link
                      key={link.to}
                      to={link.to}
                      className={clsx(
                        'flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-150',
                        isActive
                          ? 'bg-civic-800 text-civic-200 border border-civic-600 shadow-sm'
                          : 'text-civic-400 hover:text-white hover:bg-civic-900'
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
              <div className="flex items-center gap-2.5 text-xs text-civic-200 bg-civic-900/90 px-3.5 py-1.5 rounded-full border border-civic-800 shadow-sm">
                <ShieldCheck className="w-4 h-4 text-civic-400" />
                <span className="font-semibold">{profile?.display_name || 'Officer'}</span>
                {profile?.assigned_counter_ids?.[0] && (
                  <span className="text-[11px] bg-civic-800 text-civic-300 border border-civic-600 px-2 py-0.5 rounded-full font-mono font-bold">
                    Counter {profile.assigned_counter_ids[0].replace('counter-', '')}
                  </span>
                )}
              </div>
              <button
                onClick={signOut}
                title="Sign Out"
                className="p-2 text-civic-400 hover:text-rose-400 hover:bg-civic-900 rounded-xl transition-colors border border-transparent hover:border-civic-800"
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

      <footer className="border-t border-civic-900 bg-civic-950 py-3 text-center text-xs text-civic-500 font-mono">
        CivicFlow 2.3 — Counter Officer Station • Secure Authenticated Session
      </footer>
    </div>
  );
};
