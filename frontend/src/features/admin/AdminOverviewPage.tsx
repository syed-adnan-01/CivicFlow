import React, { useState } from 'react';
import { PageHeader } from '../../components/shared/PageHeader';
import {
  CalendarCheck,
  Users,
  Clock,
  CheckCircle,
  TrendingUp,
  Building,
  ShieldAlert,
  Layers,
} from 'lucide-react';

export const AdminOverviewPage: React.FC = () => {
  const [metrics] = useState({
    total_appointments: 142,
    walk_ins: 38,
    currently_waiting: 14,
    completed_today: 128,
    avg_wait_minutes: 11.4,
  });

  return (
    <div className="space-y-8">
      <PageHeader
        title="Kendra Operations Overview"
        description="Daily throughput, appointment slot capacity, and live counter queue metrics."
      />

      <div className="bg-forest-100 border-2 border-forest-300 rounded-2xl p-4 text-xs text-slate-900 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center gap-2.5">
          <ShieldAlert className="w-5 h-5 text-forest-700 flex-shrink-0" />
          <span className="font-bold">Showing live operations aggregate for: <strong>Bengaluru Central Kendra (BCSK-01)</strong></span>
        </div>
        <span className="text-xs bg-forest-200 text-forest-950 px-3 py-1 rounded-full font-mono font-black border border-forest-400 w-fit uppercase">
          Live Dataset
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-3xl border-2 border-civic-200 p-7 shadow-civic-sm hover:border-forest-600 transition-colors">
          <div className="flex items-center justify-between text-slate-600 mb-2">
            <span className="text-xs font-black uppercase tracking-wider">Booked Visits</span>
            <div className="w-10 h-10 rounded-2xl bg-blue-100 text-blue-800 flex items-center justify-center">
              <CalendarCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="text-4xl sm:text-5xl font-black text-slate-950 font-mono">{metrics.total_appointments}</div>
          <span className="text-xs text-slate-600 mt-2 block font-bold">Scheduled advance slots</span>
        </div>

        <div className="bg-white rounded-3xl border-2 border-civic-200 p-7 shadow-civic-sm hover:border-forest-600 transition-colors">
          <div className="flex items-center justify-between text-slate-600 mb-2">
            <span className="text-xs font-black uppercase tracking-wider">Walk-in Registrations</span>
            <div className="w-10 h-10 rounded-2xl bg-forest-100 text-forest-800 flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <div className="text-4xl sm:text-5xl font-black text-slate-950 font-mono">{metrics.walk_ins}</div>
          <span className="text-xs text-slate-600 mt-2 block font-bold">Direct desk check-ins</span>
        </div>

        <div className="bg-white rounded-3xl border-2 border-civic-200 p-7 shadow-civic-sm hover:border-forest-600 transition-colors">
          <div className="flex items-center justify-between text-slate-600 mb-2">
            <span className="text-xs font-black uppercase tracking-wider">Citizens Waiting</span>
            <div className="w-10 h-10 rounded-2xl bg-gold-100 text-gold-800 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="text-4xl sm:text-5xl font-black text-gold-600 font-mono">{metrics.currently_waiting}</div>
          <span className="text-xs text-slate-600 mt-2 block font-bold">Across 6 active counters</span>
        </div>

        <div className="bg-white rounded-3xl border-2 border-civic-200 p-7 shadow-civic-sm hover:border-forest-600 transition-colors">
          <div className="flex items-center justify-between text-slate-600 mb-2">
            <span className="text-xs font-black uppercase tracking-wider">Avg Wait Time</span>
            <div className="w-10 h-10 rounded-2xl bg-forest-700 text-white flex items-center justify-center shadow-sm">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="text-4xl sm:text-5xl font-black text-forest-700 font-mono">{metrics.avg_wait_minutes}m</div>
          <span className="text-xs text-forest-700 mt-2 block font-black">↓ 68% vs uncoordinated queues</span>
        </div>
      </div>

      <div className="bg-white rounded-3xl border-2 border-civic-200 p-8 shadow-civic-sm">
        <h3 className="font-black text-slate-950 mb-5 text-base">Counter Performance & Utilization</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-800">
            <thead className="bg-civic-50 text-xs uppercase text-slate-700 border-b-2 border-civic-200 font-black">
              <tr>
                <th className="px-5 py-4">Counter</th>
                <th className="px-5 py-4">Assigned Officer</th>
                <th className="px-5 py-4">Service Stream</th>
                <th className="px-5 py-4">Status</th>
                <th className="px-5 py-4">Citizens Served</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              <tr className="hover:bg-civic-50 transition-colors">
                <td className="px-5 py-4 font-black font-mono text-slate-950">Counter 1</td>
                <td className="px-5 py-4 font-bold">Rajeshwari M.</td>
                <td className="px-5 py-4 font-medium">Caste & Income Certificates</td>
                <td className="px-5 py-4"><span className="text-xs px-3 py-1 rounded-full bg-forest-100 text-forest-900 font-black border border-forest-300">Active</span></td>
                <td className="px-5 py-4 font-mono font-black text-forest-700">24</td>
              </tr>
              <tr className="hover:bg-civic-50 transition-colors">
                <td className="px-5 py-4 font-black font-mono text-slate-950">Counter 2</td>
                <td className="px-5 py-4 font-bold">Ananya Sharma</td>
                <td className="px-5 py-4 font-medium">Revenue Verification & Mutations</td>
                <td className="px-5 py-4"><span className="text-xs px-3 py-1 rounded-full bg-forest-100 text-forest-900 font-black border border-forest-300">Active</span></td>
                <td className="px-5 py-4 font-mono font-black text-forest-700">29</td>
              </tr>
              <tr className="hover:bg-civic-50 transition-colors">
                <td className="px-5 py-4 font-black font-mono text-slate-950">Counter 3</td>
                <td className="px-5 py-4 font-bold">Vikram Patel</td>
                <td className="px-5 py-4 font-medium">Driving Licences & Biometrics</td>
                <td className="px-5 py-4"><span className="text-xs px-3 py-1 rounded-full bg-forest-100 text-forest-900 font-black border border-forest-300">Active</span></td>
                <td className="px-5 py-4 font-mono font-black text-forest-700">31</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
