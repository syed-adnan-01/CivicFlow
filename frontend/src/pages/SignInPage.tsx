import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthProvider';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Alert } from '../components/ui/Alert';
import { AppRole } from '../types/user';
import { Phone, Shield, ArrowRight, UserCheck, KeyRound, Layers, Sparkles } from 'lucide-react';

export const SignInPage: React.FC = () => {
  const { demoSignIn, sendOtp, setupRecaptcha } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [phoneNumber, setPhoneNumber] = useState('+91');
  const [verificationCode, setVerificationCode] = useState('');
  const [confirmationResult, setConfirmationResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as any)?.from?.pathname || '/citizen';

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phoneNumber || phoneNumber.length < 10) {
      setError('Please provide a valid phone number with country code (e.g. +919876543210).');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const verifier = setupRecaptcha('recaptcha-container');
      const confirmation = await sendOtp(phoneNumber, verifier);
      setConfirmationResult(confirmation);
    } catch (err: any) {
      setError(err?.message || 'Failed to send OTP. You can use Demo Accounts below during development.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verificationCode || verificationCode.length < 4) {
      setError('Please enter the 6-digit verification code.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await confirmationResult.confirm(verificationCode);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Invalid or expired OTP code.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoSignIn = (role: AppRole) => {
    demoSignIn(role);
    if (role === 'OFFICER') {
      navigate('/officer', { replace: true });
    } else if (role === 'OFFICE_ADMIN') {
      navigate('/admin', { replace: true });
    } else {
      navigate('/citizen', { replace: true });
    }
  };

  return (
    <div className="min-h-[calc(100vh-5rem)] flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-civic-lg border border-civic-200 p-8 sm:p-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-civic-100 border border-civic-300 text-civic-800 rounded-2xl mb-4 shadow-civic-sm">
            <Layers className="w-7 h-7 text-civic-700" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-civic-950 tracking-tight">Sign in to CivicFlow</h2>
          <p className="text-xs sm:text-sm text-civic-700 mt-1.5">Enter your phone number to receive an authentication OTP</p>
        </div>

        {error && <Alert type="error" message={error} className="mb-6" />}

        {!confirmationResult ? (
          <form onSubmit={handleSendOtp} className="space-y-4">
            <Input
              label="Mobile Number"
              placeholder="+919876543210"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              leftIcon={<Phone className="w-4 h-4" />}
              helperText="E.164 formatted number with country code"
              required
            />
            <div id="recaptcha-container"></div>
            <Button type="submit" loading={loading} className="w-full" size="lg">
              <span>Send OTP</span>
              <ArrowRight className="w-4 h-4 text-civic-300" />
            </Button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp} className="space-y-4">
            <Input
              label="6-Digit Verification Code"
              placeholder="123456"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value)}
              required
            />
            <Button type="submit" loading={loading} className="w-full" size="lg">
              Verify & Sign In
            </Button>
            <button
              type="button"
              onClick={() => setConfirmationResult(null)}
              className="text-xs text-civic-600 hover:text-civic-900 text-center w-full mt-2 font-medium"
            >
              Change Phone Number
            </button>
          </form>
        )}

        <div className="relative my-8">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-civic-200"></div>
          </div>
          <div className="relative flex justify-center text-[11px] uppercase tracking-wider font-bold">
            <span className="bg-white px-3 text-civic-600">Demo & Testing Fast-Pass</span>
          </div>
        </div>

        <div className="space-y-2.5">
          <button
            onClick={() => handleDemoSignIn('CITIZEN')}
            className="w-full flex items-center justify-between px-4 py-3 rounded-2xl border border-civic-200 text-sm font-semibold text-civic-900 hover:bg-civic-100 hover:border-civic-400 transition-all shadow-civic-sm text-left group"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-civic-200 text-civic-800 flex items-center justify-center font-bold">
                <UserCheck className="w-4 h-4 text-civic-800" />
              </div>
              <div>
                <span className="block font-bold">Sign In as Citizen</span>
                <span className="text-[11px] text-civic-600 font-normal">Ramesh Kumar (Citizen Demo)</span>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-civic-400 group-hover:text-civic-800 transition-colors" />
          </button>

          <button
            onClick={() => handleDemoSignIn('OFFICER')}
            className="w-full flex items-center justify-between px-4 py-3 rounded-2xl border border-civic-800 bg-civic-950 text-sm font-semibold text-white hover:bg-civic-900 transition-all shadow-civic-sm text-left group"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-civic-800 text-civic-300 flex items-center justify-center font-bold">
                <Shield className="w-4 h-4 text-civic-300" />
              </div>
              <div>
                <span className="block font-bold">Sign In as Officer</span>
                <span className="text-[11px] text-civic-400 font-normal">Ananya Sharma (Counter 2)</span>
              </div>
            </div>
            <span className="text-[11px] bg-civic-800 text-civic-300 px-2.5 py-1 rounded-full font-mono font-bold">
              Desk 2
            </span>
          </button>

          <button
            onClick={() => handleDemoSignIn('OFFICE_ADMIN')}
            className="w-full flex items-center justify-between px-4 py-3 rounded-2xl border border-civic-200 bg-white text-sm font-semibold text-civic-900 hover:bg-civic-100 hover:border-civic-300 transition-all shadow-civic-sm text-left group"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-civic-300 text-civic-950 flex items-center justify-center font-bold">
                <Shield className="w-4 h-4 text-civic-950" />
              </div>
              <div>
                <span className="block font-bold">Sign In as Admin</span>
                <span className="text-[11px] text-civic-600 font-normal">Kendra Administrator</span>
              </div>
            </div>
            <span className="text-[11px] bg-civic-200 text-civic-900 px-2.5 py-1 rounded-full font-mono font-bold">
              BCSK-01
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};
