import React from 'react';
import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'accent' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon,
  className,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-extrabold rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed select-none tracking-tight';

  const sizeStyles = {
    sm: 'px-3.5 py-1.5 text-xs gap-1.5',
    md: 'px-5 py-2.5 text-sm gap-2',
    lg: 'px-6 py-3.5 text-base gap-2.5',
  };

  const variantStyles = {
    primary:
      'bg-[#2A5A24] text-white hover:bg-[#1E421A] focus:ring-green-700 shadow-md hover:shadow-lg active:scale-[0.99] border-2 border-[#1E421A]',
    secondary:
      'bg-slate-900 text-white hover:bg-black focus:ring-slate-700 shadow-md active:scale-[0.99]',
    accent:
      'bg-[#D97706] text-white hover:bg-[#B45309] focus:ring-amber-500 font-extrabold shadow-md active:scale-[0.99] border-2 border-[#92400E]',
    outline:
      'border-2 border-slate-300 bg-white text-slate-900 hover:bg-slate-100 hover:border-slate-500 focus:ring-green-600 shadow-sm',
    danger:
      'bg-rose-600 text-white hover:bg-rose-700 focus:ring-rose-500 shadow-md',
    ghost:
      'text-slate-800 hover:bg-slate-100 hover:text-black focus:ring-slate-400 font-semibold',
  };

  return (
    <button
      className={clsx(baseStyles, sizeStyles[size], variantStyles[variant], className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : icon}
      {children}
    </button>
  );
};
