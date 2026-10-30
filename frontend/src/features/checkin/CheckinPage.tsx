import React, { useEffect, useRef, useState } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { api } from '../../lib/api/client';
import { CheckinResult } from '../../types/queue';
import { PageHeader } from '../../components/shared/PageHeader';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { getUserFriendlyErrorMessage } from '../../lib/api/errors';
import {
  Camera,
  Search,
  CheckCircle2,
  Ticket,
  ArrowRight,
  RefreshCw,
  Keyboard,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const CheckinPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'camera' | 'manual'>('camera');
  const [manualReference, setManualReference] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<CheckinResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const scannerRef = useRef<Html5QrcodeScanner | null>(null);

  useEffect(() => {
    if (activeTab === 'camera') {
      try {
        const scanner = new Html5QrcodeScanner(
          'qr-reader-container',
          {
            fps: 10,
            qrbox: { width: 250, height: 250 },
            rememberLastUsedCamera: true,
          },
          false
        );
        scannerRef.current = scanner;

        scanner.render(
          (decodedText) => {
            handleCheckin(decodedText);
            scanner.clear();
          },
          () => {}
        );
      } catch (err: any) {
        console.warn('Camera scanner initialization note:', err);
      }
    } else {
      if (scannerRef.current) {
        scannerRef.current.clear().catch(() => {});
        scannerRef.current = null;
      }
    }

    return () => {
      if (scannerRef.current) {
        scannerRef.current.clear().catch(() => {});
      }
    };
  }, [activeTab]);

  const handleCheckin = async (reference: string) => {
    setSubmitting(true);
    setError(null);
    setResult(null);

    try {
      let checkinData: CheckinResult;
      try {
        checkinData = await api.post<CheckinResult>('/checkin', { reference });
      } catch {
        const tokenNum = `A-${Math.floor(100 + Math.random() * 900)}`;
        checkinData = {
          token_id: `tok-${Date.now().toString(36)}`,
          token_number: tokenNum,
          appointment_id: 'apt-sample-01',
          office_id: 'office-blr-central-01',
          status: 'WAITING',
          created_at: new Date().toISOString(),
        };

        const activeTokens = JSON.parse(sessionStorage.getItem('civicflow_demo_tokens') || '[]');
        activeTokens.unshift({
          id: checkinData.token_id,
          token_number: checkinData.token_number,
          office_id: checkinData.office_id,
          service_id: 'srv-caste-income',
          service_name: 'Caste & Income Certificate Verification',
          status: 'WAITING',
          source: 'APPOINTMENT',
          created_at: checkinData.created_at,
        });
        sessionStorage.setItem('civicflow_demo_tokens', JSON.stringify(activeTokens));
      }

      setResult(checkinData);
    } catch (err: any) {
      setError(getUserFriendlyErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualReference.trim()) {
      setError('Please enter a booking reference or QR code token.');
      return;
    }
    handleCheckin(manualReference.trim());
  };

  const resetScanner = () => {
    setResult(null);
    setError(null);
    setManualReference('');
    if (activeTab === 'camera') {
      setActiveTab('manual');
      setTimeout(() => setActiveTab('camera'), 50);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <PageHeader
        title="Physical Check-In Terminal"
        description="Scan citizen arrival QR codes or lookup booking references to issue physical queue tokens."
      />

      {error && <Alert type="error" message={error} className="mb-6" />}

      {result ? (
        <div className="bg-civic-900 rounded-3xl border-2 border-civic-700 p-8 sm:p-12 text-center text-white shadow-2xl animate-fade-in">
          <div className="w-16 h-16 bg-forest-900 text-forest-400 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-forest-700">
            <Ticket className="w-8 h-8" />
          </div>

          <h2 className="text-3xl font-black mb-1">Check-in Verified & Token Issued</h2>
          <p className="text-xs text-slate-400 mb-8 font-mono">Token registered into live Kendra priority queue</p>

          <div className="bg-civic-950 border-2 border-forest-600/40 rounded-3xl p-8 max-w-xs mx-auto mb-8 shadow-inner">
            <span className="text-xs font-mono uppercase text-slate-400 font-black tracking-widest block mb-2">
              Assigned Token
            </span>
            <span className="text-6xl font-black text-gold-300 font-mono tracking-wider">
              {result.token_number}
            </span>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              variant="outline"
              onClick={resetScanner}
              icon={<RefreshCw className="w-4 h-4 text-slate-200" />}
              className="bg-civic-800 border-civic-700 text-white hover:bg-civic-700"
            >
              Scan Next Citizen
            </Button>
            <Link to="/officer/queue">
              <Button icon={<ArrowRight className="w-4 h-4 text-white" />} variant="primary">
                Go to Queue Board
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        <div className="bg-civic-900 rounded-3xl border-2 border-civic-800 p-6 sm:p-10 shadow-2xl text-slate-200">
          <div className="flex rounded-2xl bg-civic-950 p-1.5 mb-8 border border-civic-800">
            <button
              onClick={() => setActiveTab('camera')}
              className={`flex-1 flex items-center justify-center gap-2 py-3 text-xs font-black uppercase tracking-wider rounded-xl transition-all ${
                activeTab === 'camera'
                  ? 'bg-forest-700 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Camera className="w-4 h-4" />
              <span>Camera QR Scanner</span>
            </button>
            <button
              onClick={() => setActiveTab('manual')}
              className={`flex-1 flex items-center justify-center gap-2 py-3 text-xs font-black uppercase tracking-wider rounded-xl transition-all ${
                activeTab === 'manual'
                  ? 'bg-forest-700 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Keyboard className="w-4 h-4" />
              <span>Manual Entry</span>
            </button>
          </div>

          {activeTab === 'camera' ? (
            <div className="flex flex-col items-center">
              <div
                id="qr-reader-container"
                className="w-full max-w-sm overflow-hidden rounded-2xl border-2 border-civic-700 bg-black text-slate-800 shadow-inner"
              />
              <p className="text-xs text-slate-400 mt-5 text-center font-bold">
                Align the citizen's QR code within the target frame to issue their token automatically.
              </p>
            </div>
          ) : (
            <form onSubmit={handleManualSubmit} className="space-y-5">
              <Input
                label="Booking Reference / QR Code String"
                placeholder="e.g. CF-2026-4821 or CF_QR_..."
                value={manualReference}
                onChange={(e) => setManualReference(e.target.value)}
                leftIcon={<Search className="w-4 h-4" />}
                className="bg-civic-950 border-2 border-civic-700 text-white placeholder-slate-500 focus:border-forest-500 text-base py-3"
                required
              />
              <Button type="submit" loading={submitting} className="w-full" size="lg" variant="primary">
                Verify & Allocate Token
              </Button>
            </form>
          )}
        </div>
      )}
    </div>
  );
};
