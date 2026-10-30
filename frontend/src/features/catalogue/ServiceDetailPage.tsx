import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../../lib/api/client';
import { Service } from '../../types/service';
import { PageHeader } from '../../components/shared/PageHeader';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { ExternalLink, CheckCircle2, ArrowRight, ArrowLeft, ShieldAlert } from 'lucide-react';

export const ServiceDetailPage: React.FC = () => {
  const { serviceId } = useParams<{ serviceId: string }>();
  const [service, setService] = useState<Service | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchService = async () => {
      try {
        setLoading(true);
        setError(null);
        try {
          const data = await api.get<Service>(`/services/${serviceId}`);
          setService(data);
        } catch {
          setService({
            id: serviceId || 'srv-caste-income',
            name: 'Caste & Income Certificate Verification',
            code: 'REV-001',
            department: 'Revenue Department, Government of Karnataka',
            description:
              'Physical verification of original revenue documents, land records, and biometric validation for issuance of Nadakacheri Caste & Income certificates.',
            official_portal_url: 'https://sevasindhu.karnataka.gov.in',
            checklist: [
              { id: '1', document_name: 'Aadhaar Card (Original + 1 Photocopy)', is_mandatory: true, description: 'Required for applicant identity & address proof' },
              { id: '2', document_name: 'Ration Card / Voter ID', is_mandatory: true, description: 'Family tree and local residence record' },
              { id: '3', document_name: 'Previous Caste Certificate or School TC', is_mandatory: true, description: 'Shows caste mention of applicant or parents' },
              { id: '4', document_name: 'Income Proof (Salary Slip / Land RTC / IT Return)', is_mandatory: false, description: 'Required if declared income exceeds standard rural threshold' },
            ],
            is_active: true,
          });
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load service details.');
      } finally {
        setLoading(false);
      }
    };

    fetchService();
  }, [serviceId]);

  if (loading) {
    return <div className="h-64 bg-civic-100 rounded-3xl animate-pulse" />;
  }

  if (error || !service) {
    return <Alert type="error" message={error || 'Service not found'} />;
  }

  return (
    <div className="space-y-6">
      <div className="mb-2">
        <Link to="/citizen/services" className="inline-flex items-center gap-1.5 text-xs font-bold text-civic-700 hover:text-civic-950">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Services</span>
        </Link>
      </div>

      <PageHeader
        title={service.name}
        description={`Administered by ${service.department}`}
        action={
          <Link to={`/citizen/appointments/new?service_id=${service.id}`}>
            <Button size="lg" icon={<ArrowRight className="w-4 h-4" />}>
              Reserve Arrival Slot
            </Button>
          </Link>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-3xl border border-civic-200 p-8 shadow-civic-sm">
            <h3 className="text-base font-bold text-civic-950 mb-3">Service Scope</h3>
            <p className="text-sm text-civic-700 leading-relaxed">{service.description}</p>
          </div>

          <div className="bg-white rounded-3xl border border-civic-200 p-8 shadow-civic-sm">
            <h3 className="text-base font-bold text-civic-950 mb-4">Required Documents Checklist</h3>
            <div className="space-y-3">
              {service.checklist?.map((item) => (
                <div key={item.id} className="p-4 rounded-2xl border border-civic-100 bg-civic-50/70 flex items-start gap-3.5">
                  <CheckCircle2 className={`w-5 h-5 flex-shrink-0 mt-0.5 ${item.is_mandatory ? 'text-civic-700' : 'text-civic-400'}`} />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-civic-950">{item.document_name}</span>
                      <span className={`text-[11px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${item.is_mandatory ? 'bg-civic-200 text-civic-900 border border-civic-300' : 'bg-slate-100 text-slate-600'}`}>
                        {item.is_mandatory ? 'Mandatory' : 'Optional'}
                      </span>
                    </div>
                    {item.description && <p className="text-xs text-civic-600 mt-1">{item.description}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-civic-100/90 rounded-3xl border border-civic-300 p-6 text-civic-950 shadow-civic-sm">
            <div className="flex items-center gap-2 font-bold text-sm mb-2 text-civic-900">
              <ShieldAlert className="w-5 h-5 text-civic-700" />
              <span>Official Departmental Portal</span>
            </div>
            <p className="text-xs text-civic-700 leading-relaxed mb-4">
              CivicFlow manages physical Kendra arrival and token flow. To review official government statutory rules or file online submissions, visit the portal directly:
            </p>
            {service.official_portal_url && (
              <a
                href={service.official_portal_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-bold text-civic-800 hover:text-civic-950 underline"
              >
                <span>Visit Official Portal</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>

          <div className="bg-white rounded-3xl border border-civic-200 p-8 text-center shadow-civic-sm">
            <h4 className="font-extrabold text-civic-950 mb-1">Ready to visit?</h4>
            <p className="text-xs text-civic-600 mb-5">Reserve your arrival slot to avoid standing in queue.</p>
            <Link to={`/citizen/appointments/new?service_id=${service.id}`} className="block">
              <Button className="w-full" size="lg">Choose Date & Slot</Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
