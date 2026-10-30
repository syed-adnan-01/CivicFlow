import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../lib/api/client';
import { Service, Office } from '../../types/service';
import { PageHeader } from '../../components/shared/PageHeader';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Alert } from '../../components/ui/Alert';
import { Search, Building2, ChevronRight, FileCheck2, ShieldCheck } from 'lucide-react';

export const ServiceListPage: React.FC = () => {
  const [services, setServices] = useState<Service[]>([]);
  const [offices, setOffices] = useState<Office[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedOffice, setSelectedOffice] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const [servicesRes, officesRes] = await Promise.allSettled([
          api.get<Service[]>('/services'),
          api.get<Office[]>('/offices'),
        ]);

        if (servicesRes.status === 'fulfilled') {
          setServices(servicesRes.value);
        } else {
          setServices([
            {
              id: 'srv-caste-income',
              name: 'Caste & Income Certificate Verification',
              code: 'REV-001',
              department: 'Revenue Department',
              description: 'Physical document scrutiny and counter biometric capture for Nadakacheri Caste & Income certificates.',
              official_portal_url: 'https://sevasindhu.karnataka.gov.in',
              checklist: [
                { id: 'c1', document_name: 'Aadhaar Card of Applicant', is_mandatory: true },
                { id: 'c2', document_name: 'Previous Caste / Income Certificate or Ration Card', is_mandatory: true },
                { id: 'c3', document_name: 'Salary Slip / IT Return or Land Record (RTC)', is_mandatory: false },
              ],
              is_active: true,
            },
            {
              id: 'srv-driving-licence',
              name: 'Driving Licence Biometrics & Skill Test',
              code: 'TRANS-002',
              department: 'Transport Department (RTO)',
              description: 'Kendra token allocation for Learner Licence biometric capture and Driving Skill Test slot validation.',
              official_portal_url: 'https://parivahan.gov.in',
              checklist: [
                { id: 'd1', document_name: 'Application Form Acknowledgement (Form 2)', is_mandatory: true },
                { id: 'd2', document_name: 'Medical Certificate (Form 1A if age > 40)', is_mandatory: false },
                { id: 'd3', document_name: 'Address & Age Proof (Passport / Voter ID)', is_mandatory: true },
              ],
              is_active: true,
            },
            {
              id: 'srv-khata-transfer',
              name: 'Khata Transfer & Mutation Verification',
              code: 'BBMP-003',
              department: 'Revenue / Municipal Administration',
              description: 'Original title deed scrutiny and physical token issuance for e-Khata registration and mutation entries.',
              official_portal_url: 'https://bbmpeaasthi.karnataka.gov.in',
              checklist: [
                { id: 'k1', document_name: 'Registered Sale Deed / Title Deed', is_mandatory: true },
                { id: 'k2', document_name: 'Latest Tax Paid Receipt', is_mandatory: true },
                { id: 'k3', document_name: 'Encumbrance Certificate (EC)', is_mandatory: true },
              ],
              is_active: true,
            },
          ]);
        }

        if (officesRes.status === 'fulfilled') {
          setOffices(officesRes.value);
        } else {
          setOffices([
            { id: 'office-blr-central-01', name: 'Bengaluru Central Citizen Service Kendra', code: 'BCSK-01', district: 'Bengaluru Urban', is_active: true },
            { id: 'office-blr-south-02', name: 'Jayanagar Citizen Service Centre', code: 'JCSC-02', district: 'Bengaluru South', is_active: true },
          ]);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load services directory.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const filteredServices = services.filter((srv) => {
    return (
      srv.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      srv.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
      srv.description.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Citizen Services Directory"
        description="Discover public services, review required original document checklists, and reserve physical Kendra arrival slots."
      />

      <div className="bg-[#EBF1E4] border-2 border-[#B3BE7F] rounded-3xl p-5 text-xs text-slate-900 flex items-start gap-3.5 shadow-sm">
        <ShieldCheck className="w-5 h-5 text-[#2A5A24] flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-black text-[#1E421A] uppercase tracking-wide">CivicFlow Visit Preparation Notice:</span>
          <p className="mt-0.5 text-slate-700 leading-relaxed font-medium">
            CivicFlow schedules in-person arrival and issues counter queue tokens. Official government application processing and legal certificate issuance remain exclusively with the authorized government departments.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <Input
            placeholder="Search by service name, department, or keyword..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>
        <div>
          <Select
            options={offices.map((o) => ({ value: o.id, label: `${o.name} (${o.district || ''})` }))}
            value={selectedOffice}
            onChange={(e) => setSelectedOffice(e.target.value)}
            placeholder="Filter by Kendra Location"
          />
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-52 bg-white rounded-3xl border-2 border-slate-200 animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <Alert type="error" message={error} />
      ) : filteredServices.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-3xl border-2 border-slate-200 shadow-sm">
          <p className="text-slate-600 font-bold">No services found matching your query.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredServices.map((service) => (
            <div
              key={service.id}
              className="bg-white rounded-3xl border-2 border-slate-200 p-8 shadow-sm hover:shadow-md hover:border-[#2A5A24] transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between text-xs font-black mb-3">
                  <span className="bg-[#EBF1E4] text-[#1E421A] border border-[#B3BE7F] px-3 py-1 rounded-lg font-mono">
                    {service.code}
                  </span>
                  <span className="text-[#2A5A24] font-extrabold">{service.department}</span>
                </div>
                <h3 className="text-2xl font-black text-slate-950 mb-2.5 group-hover:text-[#2A5A24] transition-colors">
                  {service.name}
                </h3>
                <p className="text-sm text-slate-600 line-clamp-2 leading-relaxed mb-6 font-medium">
                  {service.description}
                </p>
                {service.checklist && service.checklist.length > 0 && (
                  <div className="flex items-center gap-2 text-xs text-slate-800 mb-6 bg-slate-50 border border-slate-200 p-3 rounded-2xl font-bold">
                    <FileCheck2 className="w-4 h-4 text-[#2A5A24]" />
                    <span>{service.checklist.length} document requirements specified</span>
                  </div>
                )}
              </div>

              <div className="pt-5 border-t border-slate-100 flex items-center justify-between">
                <Link
                  to={`/citizen/services/${service.id}`}
                  className="text-xs font-black text-[#2A5A24] hover:text-[#1E421A] transition-colors uppercase tracking-wider"
                >
                  View Checklist & Portal Link
                </Link>
                <Link
                  to={`/citizen/appointments/new?service_id=${service.id}`}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#2A5A24] text-white text-xs font-extrabold hover:bg-[#1E421A] shadow-md transition-all border border-[#1E421A]"
                >
                  <span>Book Slot</span>
                  <ChevronRight className="w-4 h-4 text-[#DAD38C]" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
