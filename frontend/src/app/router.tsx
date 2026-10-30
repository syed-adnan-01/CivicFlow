import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { PublicLayout } from '../components/layout/PublicLayout';
import { CitizenLayout } from '../components/layout/CitizenLayout';
import { OfficerLayout } from '../components/layout/OfficerLayout';
import { AdminLayout } from '../components/layout/AdminLayout';
import { ProtectedRoute } from './ProtectedRoute';

import { LandingPage } from '../pages/LandingPage';
import { SignInPage } from '../pages/SignInPage';
import { AccessDeniedPage } from '../pages/AccessDeniedPage';

import { ServiceListPage } from '../features/catalogue/ServiceListPage';
import { ServiceDetailPage } from '../features/catalogue/ServiceDetailPage';
import { BookAppointmentPage } from '../features/appointments/BookAppointmentPage';
import { AppointmentListPage } from '../features/appointments/AppointmentListPage';
import { AppointmentDetailPage } from '../features/appointments/AppointmentDetailPage';
import { CitizenQueuePage } from '../features/citizen-queue/CitizenQueuePage';
import { AssistantPage } from '../features/assistant/AssistantPage';
import { DocumentsPage } from '../features/documents/DocumentsPage';

import { CheckinPage } from '../features/checkin/CheckinPage';
import { OfficerQueuePage } from '../features/officer-queue/OfficerQueuePage';

import { AdminOverviewPage } from '../features/admin/AdminOverviewPage';

export const router = createBrowserRouter([
  // Public Routes
  {
    path: '/',
    element: <PublicLayout />,
    children: [
      { index: true, element: <LandingPage /> },
      { path: 'sign-in', element: <SignInPage /> },
      { path: 'access-denied', element: <AccessDeniedPage /> },
    ],
  },

  // Citizen Routes
  {
    path: '/citizen',
    element: (
      <ProtectedRoute allowedRoles={['CITIZEN']}>
        <CitizenLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/citizen/services" replace /> },
      { path: 'services', element: <ServiceListPage /> },
      { path: 'services/:serviceId', element: <ServiceDetailPage /> },
      { path: 'appointments/new', element: <BookAppointmentPage /> },
      { path: 'appointments', element: <AppointmentListPage /> },
      { path: 'appointments/:appointmentId', element: <AppointmentDetailPage /> },
      { path: 'queue/:tokenId', element: <CitizenQueuePage /> },
      { path: 'assistant', element: <AssistantPage /> },
      { path: 'documents', element: <DocumentsPage /> },
    ],
  },

  // Officer Routes
  {
    path: '/officer',
    element: (
      <ProtectedRoute allowedRoles={['OFFICER']}>
        <OfficerLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/officer/queue" replace /> },
      { path: 'queue', element: <OfficerQueuePage /> },
      { path: 'check-in', element: <CheckinPage /> },
    ],
  },

  // Admin Routes
  {
    path: '/admin',
    element: (
      <ProtectedRoute allowedRoles={['OFFICE_ADMIN']}>
        <AdminLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <AdminOverviewPage /> },
      { path: 'analytics', element: <AdminOverviewPage /> },
    ],
  },

  // Fallback Catch-all
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);

