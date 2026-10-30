import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldX, ArrowLeft } from 'lucide-react';
import { useAuth } from '../features/auth/AuthProvider';

export const AccessDeniedPage: React.FC = () => {
  const { role, signOut } = useAuth();

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white p-8 sm:p-10 rounded-3xl shadow-civic-lg border border-civic-200 text-center">
        <div className="w-16 h-16 bg-rose-100 text-rose-600 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-rose-200">
          <ShieldX className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-black text-civic-950 mb-2">Access Restricted</h2>
        <p className="text-xs sm:text-sm text-civic-700 mb-6 leading-relaxed">
          Your active session role <span className="font-mono font-bold text-civic-950 bg-civic-100 px-2 py-0.5 rounded border border-civic-300">({role || 'Unknown'})</span> is not authorized for this portal section.
        </p>

        <div className="flex flex-col gap-3">
          <Link
            to={role === 'OFFICER' ? '/officer' : role === 'OFFICE_ADMIN' ? '/admin' : '/citizen'}
            className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-civic-700 text-white font-bold hover:bg-civic-800 shadow-civic-sm transition-all"
          >
            <ArrowLeft className="w-4 h-4 text-civic-300" />
            <span>Return to Your Portal</span>
          </Link>
          <button
            onClick={signOut}
            className="text-xs font-semibold text-civic-600 hover:text-civic-950 underline mt-2"
          >
            Sign out and switch accounts
          </button>
        </div>
      </div>
    </div>
  );
};
