import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api/client';
import { QueueToken, QueueTokenStatus } from '../../types/queue';
import { useAuth } from '../auth/AuthProvider';
import { PageHeader } from '../../components/shared/PageHeader';
import { StatusBadge } from '../../components/shared/StatusBadge';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { Modal } from '../../components/ui/Modal';
import { getUserFriendlyErrorMessage } from '../../lib/api/errors';
import {
  BellRing,
  Play,
  CheckCircle,
  PauseCircle,
  UserX,
  RefreshCw,
  Clock,
  Layers,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

export const OfficerQueuePage: React.FC = () => {
  const { profile } = useAuth();
  const counterId = profile?.assigned_counter_ids?.[0] || 'counter-02';
  const officeId = profile?.office_ids?.[0] || 'office-blr-central-01';

  const [tokens, setTokens] = useState<QueueToken[]>([]);
  const [currentToken, setCurrentToken] = useState<QueueToken | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [holdModalToken, setHoldModalToken] = useState<QueueToken | null>(null);
  const [holdReason, setHoldReason] = useState('');

  const fetchQueue = async () => {
    try {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get<{ tokens: QueueToken[] }>(`/queue/office/${officeId}`);
        setTokens(res.tokens);
        const active = res.tokens.find((t) => t.status === 'CALLED' || t.status === 'SERVING');
        setCurrentToken(active || null);
      } catch {
        const demoTokens: QueueToken[] = JSON.parse(
          sessionStorage.getItem('civicflow_demo_tokens') || '[]'
        );
        if (demoTokens.length > 0) {
          setTokens(demoTokens);
          const active = demoTokens.find((t) => t.status === 'CALLED' || t.status === 'SERVING');
          setCurrentToken(active || null);
        } else {
          const initialQueue: QueueToken[] = [
            {
              id: 'tok-101',
              token_number: 'A-101',
              office_id: officeId,
              service_id: 'srv-caste-income',
              service_name: 'Caste & Income Certificate Verification',
              counter_id: counterId,
              status: 'SERVING',
              source: 'APPOINTMENT',
              created_at: new Date(Date.now() - 900000).toISOString(),
            },
            {
              id: 'tok-102',
              token_number: 'A-102',
              office_id: officeId,
              service_id: 'srv-caste-income',
              service_name: 'Caste & Income Certificate Verification',
              status: 'WAITING',
              source: 'APPOINTMENT',
              created_at: new Date(Date.now() - 600000).toISOString(),
            },
            {
              id: 'tok-103',
              token_number: 'A-103',
              office_id: officeId,
              service_id: 'srv-driving-licence',
              service_name: 'Driving Licence Biometrics & Skill Test',
              status: 'WAITING',
              source: 'WALK_IN',
              created_at: new Date(Date.now() - 300000).toISOString(),
            },
          ];
          setTokens(initialQueue);
          setCurrentToken(initialQueue[0]);
          sessionStorage.setItem('civicflow_demo_tokens', JSON.stringify(initialQueue));
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch queue tokens.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [counterId, officeId]);

  const updateDemoToken = (tokenId: string, newStatus: QueueTokenStatus) => {
    const updated = tokens.map((t) => (t.id === tokenId ? { ...t, status: newStatus } : t));
    setTokens(updated);
    sessionStorage.setItem('civicflow_demo_tokens', JSON.stringify(updated));
    const active = updated.find((t) => t.status === 'CALLED' || t.status === 'SERVING');
    setCurrentToken(active || null);
  };

  const handleCallNext = async () => {
    setActionLoading(true);
    setError(null);
    try {
      try {
        const res = await api.post<QueueToken>(`/counters/${counterId}/call-next`);
        setCurrentToken(res);
        await fetchQueue();
      } catch {
        const nextWaiting = tokens.find((t) => t.status === 'WAITING');
        if (!nextWaiting) {
          setError('No waiting tokens available to call.');
          return;
        }
        updateDemoToken(nextWaiting.id, 'CALLED');
      }
    } catch (err: any) {
      setError(getUserFriendlyErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartService = async (tokenId: string) => {
    setActionLoading(true);
    setError(null);
    try {
      try {
        await api.post(`/queue/tokens/${tokenId}/start`);
        await fetchQueue();
      } catch {
        updateDemoToken(tokenId, 'SERVING');
      }
    } catch (err: any) {
      setError(getUserFriendlyErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCompleteService = async (tokenId: string) => {
    setActionLoading(true);
    setError(null);
    try {
      try {
        await api.post(`/queue/tokens/${tokenId}/complete`);
        await fetchQueue();
      } catch {
        updateDemoToken(tokenId, 'COMPLETED');
      }
    } catch (err: any) {
      setError(getUserFriendlyErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleHoldToken = async () => {
    if (!holdModalToken) return;
    setActionLoading(true);
    setError(null);
    try {
      try {
        await api.post(`/queue/tokens/${holdModalToken.id}/hold`, { reason: holdReason });
        await fetchQueue();
      } catch {
        updateDemoToken(holdModalToken.id, 'ON_HOLD');
      }
      setHoldModalToken(null);
      setHoldReason('');
    } catch (err: any) {
      setError(getUserFriendlyErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleResumeToken = async (tokenId: string) => {
    setActionLoading(true);
    setError(null);
    try {
      try {
        await api.post(`/queue/tokens/${tokenId}/resume`);
        await fetchQueue();
      } catch {
        updateDemoToken(tokenId, 'SERVING');
      }
    } catch (err: any) {
      setError(getUserFriendlyErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleNoShow = async (tokenId: string) => {
    setActionLoading(true);
    setError(null);
    try {
      try {
        await api.post(`/queue/tokens/${tokenId}/no-show`);
        await fetchQueue();
      } catch {
        updateDemoToken(tokenId, 'NO_SHOW');
      }
    } catch (err: any) {
      setError(getUserFriendlyErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  const waitingTokens = tokens.filter((t) => t.status === 'WAITING');
  const onHoldTokens = tokens.filter((t) => t.status === 'ON_HOLD');
  const completedTokens = tokens.filter((t) => t.status === 'COMPLETED');

  return (
    <div className="space-y-8">
      <PageHeader
        title="Counter Workspace & Queue Board"
        description="Active at Counter 2 • Bengaluru Central Kendra"
        action={
          <Button
            variant="outline"
            size="sm"
            onClick={fetchQueue}
            loading={loading}
            icon={<RefreshCw className="w-4 h-4 text-forest-500" />}
            className="text-slate-100 border-civic-700 bg-civic-900 hover:bg-civic-800"
          >
            Refresh Queue
          </Button>
        }
      />

      {error && <Alert type="error" message={error} />}

      {/* Primary Counter Call Station */}
      <div className="bg-civic-900 border-2 border-civic-700 rounded-3xl p-8 sm:p-10 shadow-2xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-8 border-b border-civic-800">
          <div>
            <span className="text-xs uppercase font-mono text-gold-300 font-black tracking-widest block mb-1">
              Currently At Counter 2
            </span>
            <div className="flex items-center gap-5">
              <span className="text-6xl sm:text-7xl font-black text-white font-mono tracking-tight">
                {currentToken ? currentToken.token_number : '—'}
              </span>
              {currentToken && <StatusBadge status={currentToken.status} className="text-sm px-4 py-1.5" />}
            </div>
            {currentToken?.service_name && (
              <p className="text-sm text-slate-300 mt-2 font-bold">{currentToken.service_name}</p>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {!currentToken ? (
              <Button
                size="lg"
                loading={actionLoading}
                onClick={handleCallNext}
                disabled={waitingTokens.length === 0}
                variant="accent"
                icon={<BellRing className="w-5 h-5" />}
              >
                Call Next Token ({waitingTokens.length} waiting)
              </Button>
            ) : currentToken.status === 'CALLED' ? (
              <>
                <Button
                  size="lg"
                  loading={actionLoading}
                  onClick={() => handleStartService(currentToken.id)}
                  variant="primary"
                  icon={<Play className="w-5 h-5 text-gold-300" />}
                >
                  Start Service
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  loading={actionLoading}
                  onClick={() => handleNoShow(currentToken.id)}
                  icon={<UserX className="w-5 h-5 text-rose-400" />}
                  className="text-rose-300 border-rose-800/80 bg-rose-950/30 hover:bg-rose-950/60"
                >
                  Mark No-Show
                </Button>
              </>
            ) : currentToken.status === 'SERVING' ? (
              <>
                <Button
                  size="lg"
                  loading={actionLoading}
                  onClick={() => handleCompleteService(currentToken.id)}
                  variant="accent"
                  icon={<CheckCircle className="w-5 h-5" />}
                >
                  Complete Service
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  loading={actionLoading}
                  onClick={() => setHoldModalToken(currentToken)}
                  icon={<PauseCircle className="w-5 h-5 text-amber-400" />}
                  className="text-amber-300 border-amber-800/80 bg-amber-950/30 hover:bg-amber-950/60"
                >
                  Put On Hold
                </Button>
              </>
            ) : null}
          </div>
        </div>

        {/* Quick summary strip */}
        <div className="grid grid-cols-3 gap-4 pt-6 text-center text-xs">
          <div className="bg-civic-950 p-4 rounded-2xl border border-civic-800">
            <span className="text-slate-400 block mb-1 font-mono uppercase text-[11px] font-bold">Waiting Queue</span>
            <span className="text-3xl font-black text-forest-500 font-mono">{waitingTokens.length}</span>
          </div>
          <div className="bg-civic-950 p-4 rounded-2xl border border-civic-800">
            <span className="text-slate-400 block mb-1 font-mono uppercase text-[11px] font-bold">On Hold</span>
            <span className="text-3xl font-black text-amber-400 font-mono">{onHoldTokens.length}</span>
          </div>
          <div className="bg-civic-950 p-4 rounded-2xl border border-civic-800">
            <span className="text-slate-400 block mb-1 font-mono uppercase text-[11px] font-bold">Completed Today</span>
            <span className="text-3xl font-black text-slate-100 font-mono">{completedTokens.length}</span>
          </div>
        </div>
      </div>

      {/* Queue Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Waiting List */}
        <div className="bg-civic-900 rounded-3xl border-2 border-civic-800 p-7 shadow-xl">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-black text-white flex items-center gap-2.5 text-base">
              <span>Waiting Queue</span>
              <span className="text-xs bg-forest-900 text-forest-300 px-3 py-0.5 rounded-full font-mono font-black border border-forest-700">
                {waitingTokens.length}
              </span>
            </h3>
          </div>

          {waitingTokens.length === 0 ? (
            <div className="py-16 text-center text-slate-400 text-sm font-medium">
              No citizens currently waiting in line.
            </div>
          ) : (
            <div className="space-y-3">
              {waitingTokens.map((token, index) => (
                <div
                  key={token.id}
                  className="bg-civic-950 border border-civic-800 rounded-2xl p-4 flex items-center justify-between hover:border-civic-700 transition-colors"
                >
                  <div className="flex items-center gap-3.5">
                    <span className="w-8 h-8 rounded-xl bg-civic-800 text-slate-200 text-xs flex items-center justify-center font-mono font-black">
                      {index + 1}
                    </span>
                    <div>
                      <span className="font-mono text-xl font-black text-white block">
                        {token.token_number}
                      </span>
                      <span className="text-xs text-slate-400 font-medium">{token.service_name || 'Service'}</span>
                    </div>
                  </div>

                  <span className="text-[11px] font-mono uppercase bg-civic-800 text-slate-200 px-2.5 py-1 rounded-lg font-black">
                    {token.source}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* On Hold List */}
        <div className="bg-civic-900 rounded-3xl border-2 border-civic-800 p-7 shadow-xl">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-black text-white flex items-center gap-2.5 text-base">
              <span>On Hold (Awaiting Documents)</span>
              <span className="text-xs bg-amber-950 text-amber-300 px-3 py-0.5 rounded-full font-mono font-black border border-amber-800">
                {onHoldTokens.length}
              </span>
            </h3>
          </div>

          {onHoldTokens.length === 0 ? (
            <div className="py-16 text-center text-slate-400 text-sm font-medium">
              No tokens currently placed on hold.
            </div>
          ) : (
            <div className="space-y-3">
              {onHoldTokens.map((token) => (
                <div
                  key={token.id}
                  className="bg-civic-950 border border-amber-900/40 rounded-2xl p-4 flex items-center justify-between"
                >
                  <div>
                    <span className="font-mono text-xl font-black text-amber-300 block">
                      {token.token_number}
                    </span>
                    <span className="text-xs text-slate-400 font-medium">{token.service_name}</span>
                  </div>

                  <Button
                    size="sm"
                    variant="outline"
                    loading={actionLoading}
                    onClick={() => handleResumeToken(token.id)}
                    className="text-forest-400 border-civic-700 bg-civic-800 hover:bg-civic-700"
                  >
                    Resume
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Hold Reason Modal */}
      <Modal
        isOpen={Boolean(holdModalToken)}
        onClose={() => setHoldModalToken(null)}
        title={`Place Token ${holdModalToken?.token_number} On Hold`}
        footer={
          <>
            <Button variant="ghost" onClick={() => setHoldModalToken(null)}>
              Cancel
            </Button>
            <Button variant="primary" loading={actionLoading} onClick={handleHoldToken}>
              Confirm Hold
            </Button>
          </>
        }
      >
        <div className="space-y-4 text-slate-900">
          <p className="text-sm font-medium">
            Specify the reason for placing this citizen on temporary hold (e.g. missing original document, biometric retry).
          </p>
          <input
            type="text"
            className="w-full rounded-xl border-2 border-civic-300 px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-forest-600 text-slate-900 font-medium"
            placeholder="e.g. Citizen fetching original revenue record photocopy"
            value={holdReason}
            onChange={(e) => setHoldReason(e.target.value)}
          />
        </div>
      </Modal>
    </div>
  );
};
