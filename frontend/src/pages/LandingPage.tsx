import React from 'react';
import { Link } from 'react-router-dom';
import {
  Layers,
  QrCode,
  Clock,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  Users,
  Building2,
  Smartphone,
  ChevronRight,
  FileCheck2,
  Zap,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="py-12 sm:py-20 overflow-hidden">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2.5 px-4.5 py-2 rounded-full bg-[#EBF1E4] border-2 border-[#B3BE7F] text-[#1E421A] text-xs font-black mb-8 shadow-sm">
            <span className="w-2.5 h-2.5 rounded-full bg-[#2A5A24] animate-ping"></span>
            <span>CIVICFLOW 2.3 • CITIZEN QUEUE COORDINATION</span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black text-slate-950 tracking-tight leading-[1.08] mb-6">
            Eliminate Physical Queues in <br />
            <span className="text-[#2A5A24] bg-gradient-to-r from-[#1E421A] via-[#2A5A24] to-[#486230] bg-clip-text text-transparent">
              Citizen Service Kendras
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-slate-700 max-w-2xl mx-auto leading-relaxed font-medium mb-10">
            Book guaranteed arrival slots in advance, verify your document checklist from home, and track your counter call live on your smartphone with encrypted QR check-ins.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/citizen/services"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-3 px-9 py-4 rounded-2xl bg-[#2A5A24] text-white font-black hover:bg-[#1E421A] shadow-xl shadow-green-950/25 transition-all text-base active:scale-[0.99] border-2 border-[#1E421A]"
            >
              <span className="text-white font-black tracking-tight text-base">Explore Services & Book Slots</span>
              <ArrowRight className="w-5 h-5 text-[#DAD38C]" />
            </Link>
            <Link
              to="/sign-in"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-4 rounded-2xl bg-white border-2 border-slate-300 text-slate-900 font-extrabold hover:bg-slate-100 hover:border-slate-500 shadow-md transition-all text-base"
            >
              <span>Citizen & Officer Sign In</span>
            </Link>
          </div>
        </div>

        {/* Live Metrics Ticker Banner */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 p-8 rounded-3xl bg-white border-2 border-slate-200 shadow-civic-md text-center">
          <div className="p-3">
            <span className="text-3xl sm:text-4xl font-black text-[#2A5A24] font-mono block">68%</span>
            <span className="text-xs text-slate-700 font-extrabold uppercase tracking-wider mt-1 block">Reduced Wait Time</span>
          </div>
          <div className="p-3 border-l-2 border-slate-100">
            <span className="text-3xl sm:text-4xl font-black text-slate-950 font-mono block">100%</span>
            <span className="text-xs text-slate-700 font-extrabold uppercase tracking-wider mt-1 block">Anti-Tamper Tokens</span>
          </div>
          <div className="p-3 border-l-0 md:border-l-2 border-slate-100">
            <span className="text-3xl sm:text-4xl font-black text-[#D97706] font-mono block">&lt; 30s</span>
            <span className="text-xs text-slate-700 font-extrabold uppercase tracking-wider mt-1 block">Desk QR Check-In</span>
          </div>
          <div className="p-3 border-l-2 border-slate-100">
            <span className="text-3xl sm:text-4xl font-black text-[#2A5A24] font-mono block">0</span>
            <span className="text-xs text-slate-700 font-extrabold uppercase tracking-wider mt-1 block">Manual Page Refreshes</span>
          </div>
        </div>

        {/* 4-Step Interactive Journey */}
        <div className="mt-20">
          <div className="text-center mb-12">
            <span className="text-xs uppercase font-mono font-black text-[#1E421A] tracking-widest bg-[#EBF1E4] border border-[#B3BE7F] px-4 py-1.5 rounded-full">
              Seamless Citizen Flow
            </span>
            <h2 className="text-3xl sm:text-4xl font-black text-slate-950 mt-3">
              How Citizen Visits Flow Smoothly
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Step 1 */}
            <div className="bg-white p-7 rounded-3xl border-2 border-slate-200 shadow-sm hover:shadow-md hover:border-[#2A5A24] transition-all flex flex-col justify-between group">
              <div>
                <div className="w-12 h-12 rounded-2xl bg-[#EBF1E4] border-2 border-[#B3BE7F] text-[#1E421A] flex items-center justify-center font-mono font-black text-lg mb-4">
                  01
                </div>
                <h3 className="text-xl font-black text-slate-950 mb-2">Service Discovery</h3>
                <p className="text-sm text-slate-600 leading-relaxed font-medium">
                  Browse public citizen services and check required original document checklists before traveling.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center gap-2 text-xs text-[#2A5A24] font-extrabold">
                <FileCheck2 className="w-4 h-4 text-[#2A5A24]" />
                <span>Checklist verification</span>
              </div>
            </div>

            {/* Step 2 */}
            <div className="bg-white p-7 rounded-3xl border-2 border-slate-200 shadow-sm hover:shadow-md hover:border-[#D97706] transition-all flex flex-col justify-between group">
              <div>
                <div className="w-12 h-12 rounded-2xl bg-amber-50 border-2 border-amber-300 text-amber-900 flex items-center justify-center font-mono font-black text-lg mb-4">
                  02
                </div>
                <h3 className="text-xl font-black text-slate-950 mb-2">Slot Reservation</h3>
                <p className="text-sm text-slate-600 leading-relaxed font-medium">
                  Select your preferred Kendra location and time window. Slots update based on live desk capacity.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center gap-2 text-xs text-amber-700 font-extrabold">
                <Clock className="w-4 h-4 text-amber-600" />
                <span>Asia/Kolkata scheduling</span>
              </div>
            </div>

            {/* Step 3 */}
            <div className="bg-white p-7 rounded-3xl border-2 border-slate-200 shadow-sm hover:shadow-md hover:border-blue-600 transition-all flex flex-col justify-between group">
              <div>
                <div className="w-12 h-12 rounded-2xl bg-blue-50 border-2 border-blue-300 text-blue-900 flex items-center justify-center font-mono font-black text-lg mb-4">
                  03
                </div>
                <h3 className="text-xl font-black text-slate-950 mb-2">Instant QR Check-in</h3>
                <p className="text-sm text-slate-600 leading-relaxed font-medium">
                  Flash your check-in QR code at the desk. Officers scan in one second to issue your physical token.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center gap-2 text-xs text-blue-700 font-extrabold">
                <QrCode className="w-4 h-4 text-blue-600" />
                <span>Opaque encrypted token</span>
              </div>
            </div>

            {/* Step 4 */}
            <div className="bg-white p-7 rounded-3xl border-2 border-slate-200 shadow-sm hover:shadow-md hover:border-[#2A5A24] transition-all flex flex-col justify-between group">
              <div>
                <div className="w-12 h-12 rounded-2xl bg-[#2A5A24] text-white flex items-center justify-center font-mono font-black text-lg mb-4 shadow-sm">
                  04
                </div>
                <h3 className="text-xl font-black text-slate-950 mb-2">Live Realtime Call</h3>
                <p className="text-sm text-slate-600 leading-relaxed font-medium">
                  Relax in the seating lounge. Your smartphone alerts you in real time via WebSockets when your counter is ready.
                </p>
              </div>
              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center gap-2 text-xs text-[#2A5A24] font-extrabold">
                <Smartphone className="w-4 h-4 text-[#2A5A24]" />
                <span>Real-time WebSocket feed</span>
              </div>
            </div>
          </div>
        </div>

        {/* Official Department Notice */}
        <div className="mt-20 bg-[#EBF1E4] border-2 border-[#B3BE7F] rounded-3xl p-7 text-xs text-slate-900 flex flex-col sm:flex-row items-center justify-between gap-5 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-white border-2 border-[#B3BE7F] flex items-center justify-center flex-shrink-0 text-[#2A5A24] shadow-sm">
              <ShieldCheck className="w-6 h-6 text-[#2A5A24]" />
            </div>
            <div>
              <p className="font-black text-base text-slate-950">Official Government Scope & Boundary</p>
              <p className="text-slate-700 mt-0.5 leading-relaxed font-medium">
                CivicFlow coordinates physical Kendra arrival, slot management, and queue tokens. Official government application processing and legal certificate issuance remain exclusively with the authorized Karnataka departmental portals.
              </p>
            </div>
          </div>
          <Link
            to="/citizen/services"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#2A5A24] text-white text-xs font-black hover:bg-[#1E421A] transition-colors whitespace-nowrap shadow-md"
          >
            <span>Explore Services</span>
            <ChevronRight className="w-4 h-4 text-[#DAD38C]" />
          </Link>
        </div>
      </div>
    </div>
  );
};
