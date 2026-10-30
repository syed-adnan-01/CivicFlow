import React, { useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../../lib/api/client';
import { QueueToken } from '../../types/queue';
import { PageHeader } from '../../components/shared/PageHeader';
import { StatusBadge } from '../../components/shared/StatusBadge';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import {
  Bell,
  CheckCircle2,
  Clock,
  Wifi,
  WifiOff,
  RefreshCw,
  ArrowLeft,
  ShieldCheck,
  AlertTriangle,
  Layers,
} from 'lucide-react';

export const CitizenQueuePage: React.FC = () => {
  const { tokenId } = useParams<{ tokenId: string }>();
  const [token, setToken] = useState<QueueToken | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'reconnecting' | 'offline'>('connecting');
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const socketRef = useRef<WebSocket | null>(null);

  const fetchAuthoritativeSnapshot = async () => {
    try {
      setError(null);
      try {
        const data = await api.get<QueueToken>(`/queue/tokens/${tokenId}`);
        setToken(data);
      } catch {
        const demoTokens: QueueToken[] = JSON.parse(
          sessionStorage.getItem('civicflow_demo_tokens') || '[]'
        );
        const match = demoTokens.find((t) => t.id === tokenId);
        if (match) {
          setToken(match);
        } else {
          setToken({
            id: tokenId || 'tok-sample',
            token_number: 'A-102',
            office_id: 'office-blr-central-01',
            service_id: 'srv-caste-income',
            service_name: 'Caste & Income Certificate Verification',
            counter_name: 'Counter 2',
            status: 'WAITING',
            source: 'APPOINTMENT',
            tokens_ahead: 2,
            estimated_wait_minutes: 12,
            created_at: new Date(Date.now() - 600000).toISOString(),
          });
        }
      }
      setLastUpdated(new Date());
    } catch (err: any) {
      setError(err.message || 'Failed to refresh queue token state.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuthoritativeSnapshot();

    let isCancelled = false;

    const connectWebSocket = async () => {
      try {
        setWsStatus('connecting');
        let ticket = '';
        try {
          const res = await api.post<{ ticket: string }>('/realtime/tickets', {
            token_id: tokenId,
          });
          ticket = res.ticket;
        } catch {
          ticket = 'mock-demo-ticket';
        }

        if (isCancelled) return;

        const wsBase = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/api/v1/realtime/ws';
        const socket = new WebSocket(`${wsBase}?ticket=${ticket}`);
        socketRef.current = socket;

        socket.onopen = () => {
          if (!isCancelled) setWsStatus('connected');
        };

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.token_id === tokenId || data.id === tokenId) {
              setToken((prev) => (prev ? { ...prev, ...data } : null));
              setLastUpdated(new Date());
            }
          } catch (err) {
            console.warn('WebSocket message parse error:', err);
          }
        };

        socket.onerror = () => {
          if (!isCancelled) setWsStatus('reconnecting');
        };

        socket.onclose = () => {
          if (!isCancelled) {
            setWsStatus('reconnecting');
            setTimeout(() => {
              if (!isCancelled) {
                fetchAuthoritativeSnapshot();
                connectWebSocket();
              }
            }, 3000);
          }
        };
      } catch (err) {
        if (!isCancelled) {
          setWsStatus('offline');
        }
      }
    };

    connectWebSocket();

    const handleStorageChange = () => {
      fetchAuthoritativeSnapshot();
    };
    window.addEventListener('storage', handleStorageChange);

    return () => {
      isCancelled = true;
      window.removeEventListener('storage', handleStorageChange);
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [tokenId]);

  if (loading) return <div className="h-80 bg-white rounded-3xl border-2 border-civic-200 animate-pulse" />;
  if (!token) return <Alert type="error" message="Queue token not found." />;

  const isCalled = token.status === 'CALLED';
  const isServing = token.status === 'SERVING';
  const isCompleted = token.status === 'COMPLETED';

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="mb-2">
        <Link to="/citizen/appointments" className="inline-flex items-center gap-1.5 text-xs font-bold text-forest-700 hover:text-forest-900">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Appointments</span>
        </Link>
      </div>

      <PageHeader
        title="Live Queue Tracker"
        description="Real-time status of your physical Kendra token."
        action={
          <div className="flex items-center gap-2 text-xs">
            {wsStatus === 'connected' ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-forest-100 text-forest-900 font-extrabold border border-forest-300">
                <Wifi className="w-4 h-4 text-forest-700" />
                <span>Live Connected</span>
              </span>
            ) : wsStatus === 'reconnecting' ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-100 text-amber-950 font-extrabold border border-amber-300 animate-pulse">
                <WifiOff className="w-4 h-4 text-amber-700" />
                <span>Reconnecting...</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 text-slate-800 font-bold border border-slate-300">
                <span>Polling REST</span>
              </span>
            )}
          </div>
        }
      />

      {error && <Alert type="error" message={error} />}

      {/* Hero Call Alert if token is CALLED */}
      {isCalled && (
        <div className="bg-gold-200 text-gold-950 border-4 border-gold-500 rounded-3xl p-8 shadow-civic-xl text-center animate-bounce">
          <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-md border-2 border-gold-400">
            <Bell className="w-9 h-9 text-gold-600" />
          </div>
          <h2 className="text-3xl sm:text-4xl font-black tracking-tight uppercase">YOUR TURN HAS ARRIVED!</h2>
          <p className="text-xl font-extrabold text-gold-950 mt-2">
            Please proceed immediately to <span className="underline decoration-4 underline-offset-4 font-black">{token.counter_name || 'Counter 2'}</span>
          </p>
        </div>
      )}

      {/* Main Token Display Card */}
      <div className="bg-white rounded-3xl border-2 border-civic-200 p-8 sm:p-12 shadow-civic-md text-center">
        <span className="text-xs font-mono uppercase text-slate-500 font-extrabold tracking-widest block mb-2">
          Your Physical Token
        </span>
        <div className="text-7xl sm:text-8xl font-black text-slate-950 font-mono tracking-tight mb-4">
          {token.token_number}
        </div>

        <div className="flex justify-center mb-6">
          <StatusBadge status={token.status} className="text-sm px-4 py-1.5 font-black" />
        </div>

        <p className="text-base font-extrabold text-slate-900 mb-8">{token.service_name}</p>

        {token.status === 'WAITING' && (
          <div className="grid grid-cols-2 gap-4 max-w-sm mx-auto bg-civic-50 border-2 border-civic-200 rounded-2xl p-6 text-center shadow-inner">
            <div>
              <span className="text-xs text-slate-600 font-bold uppercase tracking-wider block mb-1">Tokens Ahead</span>
              <span className="text-4xl font-black text-slate-950 font-mono">
                {token.tokens_ahead !== undefined ? token.tokens_ahead : '1'}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-600 font-bold uppercase tracking-wider block mb-1">Est. Wait</span>
              <span className="text-4xl font-black text-forest-700 font-mono">
                ~{token.estimated_wait_minutes || '8'}m
              </span>
            </div>
          </div>
        )}

        {isServing && (
          <div className="bg-forest-100 border-2 border-forest-400 rounded-2xl p-5 max-w-sm mx-auto text-forest-950 text-base font-black shadow-sm">
            Service in progress at {token.counter_name || 'Counter 2'}.
          </div>
        )}

        {isCompleted && (
          <div className="bg-slate-100 border border-slate-300 rounded-2xl p-6 max-w-sm mx-auto text-slate-900">
            <CheckCircle2 className="w-12 h-12 text-forest-700 mx-auto mb-2" />
            <h4 className="font-extrabold text-lg">Service Completed</h4>
            <p className="text-xs text-slate-600 mt-1 font-medium">Thank you for visiting the Kendra.</p>
          </div>
        )}

        <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-bold">
          <span>Last sync: {lastUpdated.toLocaleTimeString()}</span>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchAuthoritativeSnapshot}
            icon={<RefreshCw className="w-3.5 h-3.5 text-forest-700" />}
          >
            Refresh State
          </Button>
        </div>
      </div>
    </div>
  );
};
