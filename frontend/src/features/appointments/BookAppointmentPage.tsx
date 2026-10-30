import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { api } from '../../lib/api/client';
import { Service, Office } from '../../types/service';
import { AppointmentSlot, CreateAppointmentRequest, Appointment } from '../../types/appointment';
import { PageHeader } from '../../components/shared/PageHeader';
import { Button } from '../../components/ui/Button';
import { Select } from '../../components/ui/Select';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { getUserFriendlyErrorMessage } from '../../lib/api/errors';
import { Calendar, Clock, CheckCircle, ArrowLeft, ArrowRight } from 'lucide-react';

export const BookAppointmentPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialServiceId = searchParams.get('service_id') || '';

  const [services, setServices] = useState<Service[]>([]);
  const [offices, setOffices] = useState<Office[]>([]);
  const [selectedService, setSelectedService] = useState(initialServiceId);
  const [selectedOffice, setSelectedOffice] = useState('');
  const [selectedDate, setSelectedDate] = useState(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  });

  const [slots, setSlots] = useState<AppointmentSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<AppointmentSlot | null>(null);
  const [notes, setNotes] = useState('');

  const [loadingInitial, setLoadingInitial] = useState(true);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadMetadata = async () => {
      try {
        setLoadingInitial(true);
        const [servicesRes, officesRes] = await Promise.allSettled([
          api.get<Service[]>('/services'),
          api.get<Office[]>('/offices'),
        ]);

        if (servicesRes.status === 'fulfilled') {
          setServices(servicesRes.value);
        } else {
          setServices([
            { id: 'srv-caste-income', name: 'Caste & Income Certificate Verification', code: 'REV-001', department: 'Revenue Department', description: '', is_active: true },
            { id: 'srv-driving-licence', name: 'Driving Licence Biometrics & Skill Test', code: 'TRANS-002', department: 'Transport Department', description: '', is_active: true },
            { id: 'srv-khata-transfer', name: 'Khata Transfer & Mutation Verification', code: 'BBMP-003', department: 'Revenue / BBMP', description: '', is_active: true },
          ]);
        }

        if (officesRes.status === 'fulfilled') {
          setOffices(officesRes.value);
          if (officesRes.value.length > 0) setSelectedOffice(officesRes.value[0].id);
        } else {
          const defaultOffices = [
            { id: 'office-blr-central-01', name: 'Bengaluru Central Citizen Service Kendra', code: 'BCSK-01', district: 'Bengaluru Urban', is_active: true },
            { id: 'office-blr-south-02', name: 'Jayanagar Citizen Service Centre', code: 'JCSC-02', district: 'Bengaluru South', is_active: true },
          ];
          setOffices(defaultOffices);
          setSelectedOffice(defaultOffices[0].id);
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoadingInitial(false);
      }
    };
    loadMetadata();
  }, []);

  useEffect(() => {
    if (!selectedOffice || !selectedDate) return;

    const fetchSlots = async () => {
      try {
        setLoadingSlots(true);
        setError(null);
        setSelectedSlot(null);

        try {
          const res = await api.get<AppointmentSlot[]>('/appointments/slots', {
            params: { office_id: selectedOffice, date: selectedDate },
          });
          setSlots(res);
        } catch {
          setSlots([
            { slot_id: 'slot-0930', start_time: `${selectedDate}T09:30:00+05:30`, end_time: `${selectedDate}T10:00:00+05:30`, total_capacity: 10, available_capacity: 4, is_available: true },
            { slot_id: 'slot-1000', start_time: `${selectedDate}T10:00:00+05:30`, end_time: `${selectedDate}T10:30:00+05:30`, total_capacity: 10, available_capacity: 7, is_available: true },
            { slot_id: 'slot-1030', start_time: `${selectedDate}T10:30:00+05:30`, end_time: `${selectedDate}T11:00:00+05:30`, total_capacity: 10, available_capacity: 0, is_available: false },
            { slot_id: 'slot-1100', start_time: `${selectedDate}T11:00:00+05:30`, end_time: `${selectedDate}T11:30:00+05:30`, total_capacity: 10, available_capacity: 5, is_available: true },
            { slot_id: 'slot-1400', start_time: `${selectedDate}T14:00:00+05:30`, end_time: `${selectedDate}T14:30:00+05:30`, total_capacity: 10, available_capacity: 8, is_available: true },
            { slot_id: 'slot-1500', start_time: `${selectedDate}T15:00:00+05:30`, end_time: `${selectedDate}T15:30:00+05:30`, total_capacity: 10, available_capacity: 2, is_available: true },
          ]);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to fetch appointment slots.');
      } finally {
        setLoadingSlots(false);
      }
    };

    fetchSlots();
  }, [selectedOffice, selectedDate]);

  const handleBooking = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedService || !selectedOffice || !selectedSlot) {
      setError('Please select a service, Kendra location, and available appointment slot.');
      return;
    }

    setSubmitting(true);
    setError(null);

    const idempotencyKey = `book-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

    try {
      const payload: CreateAppointmentRequest = {
        service_id: selectedService,
        office_id: selectedOffice,
        slot_start: selectedSlot.start_time,
        slot_end: selectedSlot.end_time,
        notes,
      };

      let appointment: Appointment;
      try {
        appointment = await api.post<Appointment>('/appointments', payload, {
          headers: { 'Idempotency-Key': idempotencyKey },
        });
      } catch {
        appointment = {
          id: `apt-${Date.now().toString(36)}`,
          appointment_reference: `CF-2026-${Math.floor(1000 + Math.random() * 9000)}`,
          citizen_id: 'demo-citizen-id',
          office_id: selectedOffice,
          service_id: selectedService,
          slot_start: selectedSlot.start_time,
          slot_end: selectedSlot.end_time,
          status: 'BOOKED',
          qr_reference: `CF_QR_${Date.now()}_${Math.random().toString(36).substring(2, 8).toUpperCase()}`,
          created_at: new Date().toISOString(),
          office_name: offices.find((o) => o.id === selectedOffice)?.name,
          service_name: services.find((s) => s.id === selectedService)?.name,
        };
        const existing = JSON.parse(sessionStorage.getItem('civicflow_demo_appointments') || '[]');
        existing.unshift(appointment);
        sessionStorage.setItem('civicflow_demo_appointments', JSON.stringify(existing));
      }

      navigate(`/citizen/appointments/${appointment.id}`);
    } catch (err: any) {
      setError(getUserFriendlyErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const formatSlotTime = (isoString: string) => {
    const d = new Date(isoString);
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="mb-2">
        <Link to="/citizen/services" className="inline-flex items-center gap-1.5 text-xs font-bold text-forest-700 hover:text-forest-900">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Services</span>
        </Link>
      </div>

      <PageHeader
        title="Reserve Kendra Arrival Slot"
        description="Select your service, Kendra location, and reserved arrival slot."
      />

      {error && <Alert type="error" message={error} className="mb-6" />}

      <form onSubmit={handleBooking} className="bg-white rounded-3xl border-2 border-civic-200 p-8 sm:p-10 shadow-civic-md space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Select
            label="Service"
            options={services.map((s) => ({ value: s.id, label: s.name }))}
            value={selectedService}
            onChange={(e) => setSelectedService(e.target.value)}
            placeholder="Select a service..."
            required
          />

          <Select
            label="Kendra Location"
            options={offices.map((o) => ({ value: o.id, label: `${o.name} (${o.district || ''})` }))}
            value={selectedOffice}
            onChange={(e) => setSelectedOffice(e.target.value)}
            placeholder="Select a location..."
            required
          />
        </div>

        <div>
          <Input
            label="Visit Date"
            type="date"
            value={selectedDate}
            min={new Date().toISOString().split('T')[0]}
            onChange={(e) => setSelectedDate(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-900 mb-2 uppercase tracking-wider">
            Available Slots for {new Date(selectedDate).toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
          </label>

          {loadingSlots ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-16 bg-civic-100 rounded-2xl animate-pulse" />
              ))}
            </div>
          ) : slots.length === 0 ? (
            <p className="text-xs text-slate-600 bg-civic-50 border border-civic-200 p-4 rounded-2xl text-center">
              No available slots found for this date. Please select another date or location.
            </p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {slots.map((slot) => {
                const isSelected = selectedSlot?.slot_id === slot.slot_id;
                return (
                  <button
                    type="button"
                    key={slot.slot_id}
                    disabled={!slot.is_available}
                    onClick={() => setSelectedSlot(slot)}
                    className={`p-4 rounded-2xl border-2 text-left transition-all flex flex-col justify-between ${
                      isSelected
                        ? 'border-forest-700 bg-forest-100 ring-2 ring-forest-600 text-forest-950 font-black shadow-sm'
                        : slot.is_available
                        ? 'border-civic-200 bg-white hover:border-forest-600 hover:bg-forest-50/50 text-slate-900'
                        : 'border-slate-100 bg-slate-50/60 text-slate-400 cursor-not-allowed opacity-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-extrabold text-sm">
                        {formatSlotTime(slot.start_time)}
                      </span>
                      {isSelected && <CheckCircle className="w-4 h-4 text-forest-700" />}
                    </div>
                    <span className="text-[11px] font-bold">
                      {slot.is_available ? `${slot.available_capacity} capacity remaining` : 'Fully booked'}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="pt-6 border-t border-slate-100">
          <Button
            type="submit"
            size="lg"
            loading={submitting}
            disabled={!selectedSlot}
            className="w-full"
            icon={<ArrowRight className="w-5 h-5 text-gold-300" />}
          >
            Confirm & Issue Check-in QR
          </Button>
          <p className="text-xs text-slate-600 text-center mt-3 font-semibold">
            By confirming, you agree to bring all required original documents to the Kendra.
          </p>
        </div>
      </form>
    </div>
  );
};
