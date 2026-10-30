import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../features/auth/AuthProvider';
import { Layers, BarChart3, LogOut, ShieldAlert } from 'lucide-react';
import { clsx } from 'clsx';

export const AdminLayout: React.FC = () => {
  const { profile, signOut } = useAuth();
  const location = useLocation();

  const navLinks = [
    { to: '/admin', label: 'Overview', icon: <BarChart3 className="w-4 h-4" /> },
    { to: '/admin/analytics', label: 'Analytics', icon: <BarChart3 className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-civic-50 text-civic-950 font-sans">
      <header className="border-b border-civic-200 bg-white sticky top-0 z-40 shadow-civic-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-18">
            <div className="flex items-center gap-8">
              <Link to="/admin" className="flex items-center gap-2.5 text-civic-900 font-extrabold text-xl tracking-tight">
                <div className="w-9 h-9 rounded-xl bg-civic-800 text-civic-300 flex items-center justify-center border border-civic-700 shadow-sm">
                  <Layers className="w-5 h-5 text-civic-300" />
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center gap-2">
                    <span className="leading-none font-extrabold">CivicFlow</span>
                    <span className="text-[10px] bg-civic-100 text-civic-800 border border-civic-300 px-2 py-0.5 rounded-full font-mono font-bold">
                      ADMIN
                    </span>
                  </div>
                  <span className="text-[10px] font-semibold text-civic-600 uppercase tracking-widest mt-0.5">
                    Kendra Operations Control
                  </span>
                </div>
              </Link>

              <nav className="flex items-center gap-1.5">
                {navLinks.map((link) => {
                  const isActive = location.pathname === link.to;
                  return (
                    <Link
                      key={link.to}
                      to={link.to}
                      className={clsx(
                        'flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-semibold transition-all',
                        isActive
                          ? 'bg-civic-700 text-white shadow-civic-sm'
                          : 'text-civic-700 hover:text-civic-950 hover:bg-civic-100'
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
              <div className="flex items-center gap-2 text-xs text-civic-900 bg-civic-100 px-3.5 py-1.5 rounded-full border border-civic-200 shadow-sm">
                <ShieldAlert className="w-4 h-4 text-civic-700" />
                <span className="font-bold">{profile?.display_name || 'Office Admin'}</span>
              </div>
              <button
                onClick={signOut}
                title="Sign Out"
                className="p-2 text-civic-600 hover:text-rose-700 hover:bg-rose-50 rounded-xl transition-colors"
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

      <footer className="border-t border-civic-200 bg-white py-4 text-center text-xs text-civic-600">
        CivicFlow 2.3 — Office Administration & Throughput Analytics
      </footer>
    </div>
  );
};
