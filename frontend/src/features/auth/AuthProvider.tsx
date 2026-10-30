import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  User as FirebaseUser,
  onAuthStateChanged,
  signOut as firebaseSignOut,
  signInWithPhoneNumber,
  RecaptchaVerifier,
  ConfirmationResult,
} from 'firebase/auth';
import { firebaseAuth } from './firebase';
import { UserProfile, AppRole } from '../../types/user';
import { api } from '../../lib/api/client';

interface AuthContextType {
  firebaseUser: FirebaseUser | null;
  profile: UserProfile | null;
  role: AppRole | null;
  loading: boolean;
  error: string | null;
  signOut: () => Promise<void>;
  setupRecaptcha: (containerId: string) => RecaptchaVerifier;
  sendOtp: (phoneNumber: string, verifier: RecaptchaVerifier) => Promise<ConfirmationResult>;
  demoSignIn: (role: AppRole) => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(() => {
    // Check if demo profile stored in memory/session
    const saved = sessionStorage.getItem('queueless_demo_profile');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = async () => {
    try {
      setError(null);
      const data = await api.get<UserProfile>('/users/me');
      setProfile(data);
    } catch (err: any) {
      console.warn('Could not load authoritative profile from /users/me:', err);
      // If user is logged in to Firebase but /users/me fails or is still being implemented, keep record
      if (!profile) {
        setError('Failed to load user profile from server.');
      }
    }
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(firebaseAuth, async (user) => {
      setFirebaseUser(user);
      if (user) {
        await fetchProfile();
      } else {
        // If not in demo mode, clear profile
        if (!sessionStorage.getItem('queueless_demo_profile')) {
          setProfile(null);
        }
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const signOut = async () => {
    sessionStorage.removeItem('queueless_demo_profile');
    setProfile(null);
    setFirebaseUser(null);
    try {
      await firebaseSignOut(firebaseAuth);
    } catch (err) {
      console.warn('Firebase sign-out warning:', err);
    }
  };

  // Demo sign-in enables testing all 3 roles before/alongside Member 1's live endpoints
  const demoSignIn = (targetRole: AppRole) => {
    const demoProfile: UserProfile = {
      id: `demo-${targetRole.toLowerCase()}-id`,
      firebase_uid: `demo-${targetRole.toLowerCase()}-uid`,
      phone_number: targetRole === 'CITIZEN' ? '+919876543210' : '+919876543211',
      display_name:
        targetRole === 'CITIZEN'
          ? 'Ramesh Kumar (Citizen Demo)'
          : targetRole === 'OFFICER'
          ? 'Officer Ananya Sharma (Counter 2)'
          : 'Suresh Patil (Office Admin)',
      role: targetRole,
      active: true,
      office_ids: ['office-blr-central-01'],
      assigned_counter_ids: targetRole === 'OFFICER' ? ['counter-02'] : undefined,
    };
    sessionStorage.setItem('queueless_demo_profile', JSON.stringify(demoProfile));
    setProfile(demoProfile);
    setError(null);
  };

  const setupRecaptcha = (containerId: string): RecaptchaVerifier => {
    return new RecaptchaVerifier(firebaseAuth, containerId, {
      size: 'invisible',
      callback: () => {
        // reCAPTCHA solved
      },
    });
  };

  const sendOtp = async (phoneNumber: string, verifier: RecaptchaVerifier) => {
    return await signInWithPhoneNumber(firebaseAuth, phoneNumber, verifier);
  };

  const role = profile?.role || null;

  return (
    <AuthContext.Provider
      value={{
        firebaseUser,
        profile,
        role,
        loading,
        error,
        signOut,
        setupRecaptcha,
        sendOtp,
        demoSignIn,
        refreshProfile: fetchProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

