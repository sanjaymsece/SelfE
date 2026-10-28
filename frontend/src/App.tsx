import React from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { SocioSyncDashboard } from './components/SocioSyncDashboard';
import { AuthPage } from './pages/AuthPage';

const AppContent: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#F4EFEA] flex flex-col items-center justify-center text-[#523B50] gap-3 font-display">
        <div className="h-10 w-10 border-3 border-[#D66882] border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold tracking-wide">Syncing SocioSync AI Manager...</p>
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return <SocioSyncDashboard />;
};

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
