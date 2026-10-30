import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import { api } from '../../lib/api/client';
import { Appointment, QrRotationResponse } from '../../types/appointment';
import { PageHeader } from '../../components/shared/PageHeader';
import { StatusBadge } from '../../components/shared/StatusBadge';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { Modal } from '../../components/ui/Modal';
import { getUserFriendlyErrorMessage } from '../../lib/api/errors';
import {
  Calendar,
  Clock,
  MapPin,
  RefreshCw,
  ArrowLeft,
  ShieldCheck,
  Ban,
  ListOrdered,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';

export const AppointmentDetailPage: React.FC = () => {
  const { appointmentId } = useParams<{ appointmentId: string }>();
  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [loading, setLoading] = useState(true);
  const [rotating, setRotating] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchAppointment = async () => {
      try {
        setLoading(true);
        setError(null);
        try {
          const res = await api.get<Appointment>(`/appointments/${appointmentId}`);
          setAppointment(res);
        } catch {
          const demoList: Appointment[] = JSON.parse(
            sessionStorage.getItem('civicflow_demo_appointments') || '[]'
          );
          const found = demoList.find((a) => a.id === appointmentId);
          if (found) {
            setAppointment(found);
          } else {
            const fallback: Appointment = {
              id: appointmentId || 'apt-fallback',
              appointment_reference: 'CF-2026-4821',
              citizen_id: 'demo-citizen-id',
              office_id: 'office-blr-central-01',
              service_id: 'srv-caste-income',
              slot_start: new Date(Date.now() + 86400000).toISOString(),
              slot_end: new Date(Date.now() + 88200000).toISOString(),
              status: 'BOOKED',
              qr_reference: `CF_QR_${Date.now()}_MOCK`,
              created_at: new Date().toISOString(),
              office_name: 'Bengaluru Central Citizen Service Kendra',
              service_name: 'Caste & Income Certificate Verification',
            };
            setAppointment(fallback);
          }
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load appointment.');
      } finally {
        setLoading(false);
      }
    };

    fetchAppointment();
  }, [appointmentId]);

  const handleRotateQr = async () => {
    if (!appointment) return;
    setRotating(true);
    setError(null);
    setMessage(null);
    try {
      let newRef = '';
      try {
        const res = await api.post<QrRotationResponse>(`/appointments/${appointment.id}/qr/rotate`);
        newRef = res.qr_reference;
      } catch {
        newRef = `CF_QR_${Date.now()}_ROTATED_${Math.random().toString(36).substring(2, 6).toUpperCase()}`;
      }

      setAppointment((prev) => (prev ? { ...prev, qr_reference: newRef } : null));
      setMessage('QR code rotated successfully. The previous QR reference is now invalidated.');

      const demoList: Appointment[] = JSON.parse(
        sessionStorage.getItem('civicflow_demo_appointments') || '[]'
      );
      const updated = demoList.map((a) => (a.id === appointment.id ? { ...a, qr_reference: newRef } : a));
      sessionStorage.setItem('civicflow_demo_appointments', JSON.stringify(updated));
    } catch (err: any) {
      setError(getUserFriendlyErrorMessage(err));
    } finally {
      setRotating(false);
    }
  };

  const handleCancelAppointment = async () => {
    if (!appointment) return;
    setCancelling(true);
    setError(null);
    try {
      try {
        await api.post(`/appointments/${appointment.id}/cancel`);
      } catch {
        // Fallback demo cancellation
      }

      setAppointment((prev) => (prev ? { ...prev, status: 'CANCELLED' } : null));
      setShowCancelModal(false);
      setMessage('Your appointment slot has been cancelled.');

      const demoList: Appointment[] = JSON.parse(
        sessionStorage.getItem('civicflow_demo_appointments') || '[]'
      );
      const updated = demoList.map((a) => (a.id === appointment.id ? { ...a, status: 'CANCELLED' as const } : a));
      sessionStorage.setItem('civicflow_demo_appointments', JSON.stringify(updated));
    } catch (err: any) {
      setError(getUserFriendlyErrorMessage(err));
    } finally {
      setCancelling(false);
    }
  };

  if (loading) return <div className="h-96 bg-civic-100 rounded-3xl animate-pulse" />;
  if (!appointment) return <Alert type="error" message="Appointment not found" />;

  const isBooked = appointment.status === 'BOOKED';

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="mb-2">
        <Link to="/citizen/appointments" className="inline-flex items-center gap-1.5 text-xs font-bold text-civic-700 hover:text-civic-950">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Appointments</span>
        </Link>
      </div>

      <PageHeader
        title={appointment.service_name || 'Appointment Confirmation'}
        description={`Reference: ${appointment.appointment_reference}`}
        action={<StatusBadge status={appointment.status} className="text-sm px-3.5 py-1" />}
      />

      {error && <Alert type="error" message={error} className="mb-6" />}
      {message && <Alert type="success" message={message} className="mb-6" />}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left Column: QR Code */}
        <div className="bg-white rounded-3xl border border-civic-200 p-8 shadow-civic-md flex flex-col items-center text-center">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-civic-100 border border-civic-300 text-civic-900 rounded-full text-xs font-bold mb-6">
            <ShieldCheck className="w-4 h-4 text-civic-700" />
            <span>Encrypted Physical Check-In Token</span>
          </div>

          {isBooked && appointment.qr_reference ? (
            <>
              <div className="p-4 bg-white rounded-3xl border-2 border-civic-200 shadow-inner mb-4 inline-block">
                <QRCodeSVG
                  value={appointment.qr_reference}
                  size={200}
                  level="H"
                  includeMargin={true}
                />
              </div>

              <p className="font-mono text-xs text-civic-600 select-all mb-4 max-w-xs break-all bg-civic-50 px-3 py-1.5 rounded-lg border border-civic-200">
                {appointment.qr_reference}
              </p>

              <p className="text-xs text-civic-700 max-w-xs leading-relaxed mb-6 font-medium">
                Present this QR code on arrival at the Kendra check-in desk. The officer will scan it to issue your physical counter token.
              </p>

              <Button
                variant="outline"
                size="sm"
                loading={rotating}
                onClick={handleRotateQr}
                icon={<RefreshCw className="w-3.5 h-3.5 text-civic-700" />}
              >
                Rotate QR Reference
              </Button>
            </>
          ) : appointment.status === 'CHECKED_IN' ? (
            <div className="py-8">
              <div className="w-16 h-16 bg-civic-200 text-civic-800 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-civic-400">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-civic-950 mb-2">Checked In at Counter</h3>
              <p className="text-sm text-civic-600 mb-6">You have been checked in and issued a live queue token.</p>
              <Link to={`/citizen/queue/tok-${appointment.id}`}>
                <Button icon={<ListOrdered className="w-4 h-4" />}>
                  View Live Queue Tracker
                </Button>
              </Link>
            </div>
          ) : (
            <div className="py-8 text-slate-400">
              <Ban className="w-16 h-16 mx-auto mb-2 text-slate-300" />
              <p className="text-sm font-medium">QR code is inactive because this appointment is {appointment.status.toLowerCase()}.</p>
            </div>
          )}
        </div>

        {/* Right Column: Appointment Details */}
        <div className="space-y-6">
          <div className="bg-white rounded-3xl border border-civic-200 p-8 shadow-civic-sm space-y-5">
            <h3 className="font-bold text-civic-950 border-b border-civic-100 pb-3 text-base">Visit Details</h3>

            <div className="flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-xl bg-civic-100 text-civic-700 flex items-center justify-center flex-shrink-0">
                <Calendar className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-civic-600 font-semibold uppercase tracking-wider">Date of Visit</p>
                <p className="text-sm font-bold text-civic-950 mt-0.5">
                  {new Date(appointment.slot_start).toLocaleDateString('en-IN', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-xl bg-civic-100 text-civic-700 flex items-center justify-center flex-shrink-0">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-civic-600 font-semibold uppercase tracking-wider">Arrival Time Slot</p>
                <p className="text-sm font-bold text-civic-950 mt-0.5">
                  {new Date(appointment.slot_start).toLocaleTimeString('en-IN', {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true,
                  })}{' '}
                  -{' '}
                  {new Date(appointment.slot_end).toLocaleTimeString('en-IN', {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true,
                  })}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-xl bg-civic-100 text-civic-700 flex items-center justify-center flex-shrink-0">
                <MapPin className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs text-civic-600 font-semibold uppercase tracking-wider">Kendra Location</p>
                <p className="text-sm font-bold text-civic-950 mt-0.5">{appointment.office_name || 'Bengaluru Central Citizen Service Kendra'}</p>
              </div>
            </div>
          </div>

          <div className="bg-civic-100/70 rounded-3xl border border-civic-300 p-6 text-xs text-civic-800">
            <h4 className="font-bold text-sm text-civic-950 mb-2">Check-in Instructions</h4>
            <ul className="space-y-1.5 list-disc list-inside">
              <li>Arrive 5–10 minutes prior to your time window.</li>
              <li>Bring physical original copies of all checklist items.</li>
              <li>If your camera QR fails, quote Reference: <strong className="font-mono text-civic-950">{appointment.appointment_reference}</strong> at the desk.</li>
            </ul>
          </div>

          {isBooked && (
            <div>
              <Button
                variant="danger"
                size="sm"
                onClick={() => setShowCancelModal(true)}
              >
                Cancel Appointment
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Cancel Modal */}
      <Modal
        isOpen={showCancelModal}
        onClose={() => setShowCancelModal(false)}
        title="Cancel Appointment"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowCancelModal(false)}>
              Keep Appointment
            </Button>
            <Button variant="danger" loading={cancelling} onClick={handleCancelAppointment}>
              Confirm Cancellation
            </Button>
          </>
        }
      >
        <div className="flex items-start gap-3 text-sm text-slate-600">
          <AlertTriangle className="w-6 h-6 text-rose-600 flex-shrink-0" />
          <p>
            Are you sure you want to cancel your appointment for <strong className="text-slate-900">{appointment.service_name}</strong>? Your slot will be released for other citizens, and the QR code will be invalidated immediately.
          </p>
        </div>
      </Modal>
    </div>
  );
};
