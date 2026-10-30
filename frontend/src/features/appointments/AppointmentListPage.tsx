import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../lib/api/client';
import { Appointment } from '../../types/appointment';
import { PageHeader } from '../../components/shared/PageHeader';
import { StatusBadge } from '../../components/shared/StatusBadge';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { Calendar, Clock, MapPin, ChevronRight, PlusCircle, QrCode } from 'lucide-react';

export const AppointmentListPage: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        setLoading(true);
        setError(null);
        try {
          const res = await api.get<Appointment[]>('/appointments');
          setAppointments(res);
        } catch {
          const demoList: Appointment[] = JSON.parse(
            sessionStorage.getItem('civicflow_demo_appointments') || '[]'
          );
          if (demoList.length > 0) {
            setAppointments(demoList);
          } else {
            const sample: Appointment = {
              id: 'apt-sample-01',
              appointment_reference: 'CF-2026-4821',
              citizen_id: 'demo-citizen-id',
              office_id: 'office-blr-central-01',
              service_id: 'srv-caste-income',
              slot_start: new Date(Date.now() + 86400000).toISOString(),
              slot_end: new Date(Date.now() + 88200000).toISOString(),
              status: 'BOOKED',
              qr_reference: 'CF_QR_DEMO_SAMPLE_892',
              created_at: new Date().toISOString(),
              office_name: 'Bengaluru Central Citizen Service Kendra',
              service_name: 'Caste & Income Certificate Verification',
            };
            setAppointments([sample]);
            sessionStorage.setItem('civicflow_demo_appointments', JSON.stringify([sample]));
          }
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load appointments.');
      } finally {
        setLoading(false);
      }
    };

    fetchAppointments();
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Kendra Appointments"
        description="View your reserved slots, display check-in QR codes, or manage upcoming visits."
        action={
          <Link to="/citizen/appointments/new">
            <Button icon={<PlusCircle className="w-4 h-4" />}>Book New Slot</Button>
          </Link>
        }
      />

      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-36 bg-civic-100/60 rounded-3xl animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <Alert type="error" message={error} />
      ) : appointments.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-3xl border border-civic-200 p-8 shadow-civic-sm">
          <Calendar className="w-14 h-14 text-civic-300 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-civic-950 mb-1">No Scheduled Visits</h3>
          <p className="text-sm text-civic-600 mb-6">You currently have no active appointment slots reserved.</p>
          <Link to="/citizen/appointments/new">
            <Button>Schedule a Kendra Visit</Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {appointments.map((apt) => {
            const dateStr = new Date(apt.slot_start).toLocaleDateString('en-IN', {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            });
            const timeStr = `${new Date(apt.slot_start).toLocaleTimeString('en-IN', {
              hour: '2-digit',
              minute: '2-digit',
              hour12: true,
            })} - ${new Date(apt.slot_end).toLocaleTimeString('en-IN', {
              hour: '2-digit',
              minute: '2-digit',
              hour12: true,
            })}`;

            return (
              <div
                key={apt.id}
                className="bg-white rounded-3xl border border-civic-200 p-7 shadow-civic-sm hover:shadow-civic-md transition-all flex flex-col md:flex-row md:items-center justify-between gap-6"
              >
                <div className="space-y-2.5">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold bg-civic-100 text-civic-900 border border-civic-300 px-3 py-1 rounded-lg">
                      {apt.appointment_reference}
                    </span>
                    <StatusBadge status={apt.status} />
                  </div>

                  <h3 className="text-xl font-extrabold text-civic-950">
                    {apt.service_name || 'Government Citizen Service'}
                  </h3>

                  <div className="flex flex-wrap items-center gap-5 text-xs text-civic-700 font-medium">
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-4 h-4 text-civic-700" />
                      <span>{dateStr}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-4 h-4 text-civic-700" />
                      <span>{timeStr}</span>
                    </div>
                    {apt.office_name && (
                      <div className="flex items-center gap-1.5">
                        <MapPin className="w-4 h-4 text-civic-600" />
                        <span>{apt.office_name}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Link to={`/citizen/appointments/${apt.id}`}>
                    <Button variant="outline" size="sm" icon={<QrCode className="w-4 h-4 text-civic-700" />}>
                      Show QR Code
                    </Button>
                  </Link>
                  <Link to={`/citizen/appointments/${apt.id}`}>
                    <Button size="sm" icon={<ChevronRight className="w-4 h-4 text-civic-300" />}>
                      View Details
                    </Button>
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
