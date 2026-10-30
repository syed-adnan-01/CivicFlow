import React from 'react';
import { clsx } from 'clsx';
import { AppointmentStatus } from '../../types/appointment';
import { QueueTokenStatus } from '../../types/queue';

type AllStatuses = AppointmentStatus | QueueTokenStatus | string;

interface StatusBadgeProps {
  status: AllStatuses;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className }) => {
  const getBadgeConfig = (val: string) => {
    switch (val) {
      case 'BOOKED':
        return { label: 'Booked', bg: 'bg-blue-100 text-blue-950 border-blue-300 font-bold' };
      case 'CHECKED_IN':
        return { label: 'Checked In', bg: 'bg-forest-100 text-forest-900 border-forest-300 font-bold' };
      case 'WAITING':
        return { label: 'Waiting in Queue', bg: 'bg-civic-100 text-civic-900 border-civic-400 font-bold' };
      case 'CALLED':
        return { label: 'Proceed to Counter', bg: 'bg-gold-200 text-gold-950 border-2 border-gold-500 font-black pulse-glow' };
      case 'SERVING':
        return { label: 'In Service', bg: 'bg-forest-700 text-white border border-forest-800 font-black shadow-sm' };
      case 'ON_HOLD':
        return { label: 'Temporarily On Hold', bg: 'bg-amber-100 text-amber-950 border-amber-400 font-bold' };
      case 'COMPLETED':
        return { label: 'Completed', bg: 'bg-slate-200 text-slate-800 border-slate-300 font-bold' };
      case 'CANCELLED':
        return { label: 'Cancelled', bg: 'bg-rose-100 text-rose-950 border-rose-300 font-bold' };
      case 'NO_SHOW':
        return { label: 'No Show', bg: 'bg-rose-100 text-rose-950 border-rose-300 font-bold' };
      case 'RESCHEDULED':
        return { label: 'Rescheduled', bg: 'bg-indigo-100 text-indigo-950 border-indigo-300 font-bold' };
      default:
        return { label: val, bg: 'bg-civic-100 text-civic-900 border-civic-300 font-bold' };
    }
  };

  const config = getBadgeConfig(status);

  return (
    <span
      className={clsx(
        'inline-flex items-center px-3 py-1 rounded-full text-xs border tracking-wide uppercase',
        config.bg,
        className
      )}
    >
      {config.label}
    </span>
  );
};
