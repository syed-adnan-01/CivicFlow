import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { Layers, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';

export const PublicLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-[#F7F9F4] text-slate-900 font-sans">
      <header className="border-b border-slate-200 bg-white sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-11 h-11 rounded-2xl bg-[#2A5A24] text-[#DAD38C] flex items-center justify-center shadow-md border border-[#1E421A] group-hover:scale-105 transition-transform">
              <Layers className="w-6 h-6 text-[#DAD38C]" />
            </div>
            <div className="flex flex-col">
              <span className="text-2xl font-black tracking-tight text-slate-950 flex items-center gap-1.5 leading-none">
                CivicFlow
                <span className="w-2.5 h-2.5 rounded-full bg-[#2A5A24] inline-block animate-pulse"></span>
              </span>
              <span className="text-[11px] font-bold text-slate-600 uppercase tracking-widest mt-1">
                Citizen Queue Coordination
              </span>
            </div>
          </Link>

          <div className="flex items-center gap-6">
            <Link
              to="/citizen/services"
              className="text-sm font-bold text-slate-800 hover:text-[#2A5A24] transition-colors hidden sm:block"
            >
              Services Directory
            </Link>
            <Link
              to="/sign-in"
              className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-extrabold rounded-xl bg-[#2A5A24] text-white hover:bg-[#1E421A] shadow-md transition-all active:scale-[0.99] border-2 border-[#1E421A]"
            >
              <span>Sign In</span>
              <ArrowRight className="w-4 h-4 text-[#DAD38C]" />
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white py-10 text-center text-xs text-slate-600">
        <div className="max-w-7xl mx-auto px-4 space-y-2.5">
          <div className="flex items-center justify-center gap-2 font-black text-slate-950 text-sm">
            <Layers className="w-4 h-4 text-[#2A5A24]" />
            <span>CivicFlow 2.3 — Physical Visit Preparation & Live Queue Coordination</span>
          </div>
          <p className="text-slate-600 max-w-2xl mx-auto leading-relaxed font-medium">
            Complements official Karnataka citizen portals. Official application filings, fee collections, and formal legal determinations remain with the respective government departments.
          </p>
        </div>
      </footer>
    </div>
  );
};
