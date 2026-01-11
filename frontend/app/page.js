'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { ReactFlowProvider } from 'reactflow';
import FlowCanvas from '@/components/FlowCanvas';
import TopBar from '@/components/TopBar';
import ControlPanel from '@/components/ControlPanel';
import ExecutionLog from '@/components/ExecutionLog';

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <ReactFlowProvider>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        <TopBar />
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          <ControlPanel />
          <div style={{ flex: 1, position: 'relative' }}>
            <FlowCanvas />
          </div>
          <ExecutionLog />
        </div>
      </div>
    </ReactFlowProvider>
  );
}
