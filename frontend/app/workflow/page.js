'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { ReactFlowProvider } from 'reactflow';
import ControlPanel from '@/components/ControlPanel';
import dynamic from 'next/dynamic';
import ExecutionLog from '@/components/ExecutionLog';
import { useStore } from '@/helpers/store';

// Dynamically import client-only components to prevent SSR hydration errors.
// ReactFlow and its related components often rely on browser APIs (like getBoundingClientRect)
// that are not available on the server, leading to mismatches.
const FlowCanvas = dynamic(() => import('@/components/FlowCanvas'), { ssr: false });

export default function WorkflowPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const loadWorkflowFromV2 = useStore((state) => state.loadWorkflowFromV2);
  const setCurrentWorkflow = useStore((state) => state.setCurrentWorkflow);

  const projectId = searchParams.get('project');
  const workflowId = searchParams.get('workflow');

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  // Load workflow when project and workflow IDs are available
  useEffect(() => {
    if (projectId && workflowId && user) {
      console.log('Loading workflow:', { projectId, workflowId });
      setCurrentWorkflow(projectId, workflowId);
      loadWorkflowFromV2(projectId, workflowId);
    }
  }, [projectId, workflowId, user, loadWorkflowFromV2, setCurrentWorkflow]);

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
      <div className="app-layout">
        <ControlPanel />
        <div className="main-content">
          <main className="flow-container">
            <FlowCanvas />
          </main>
          <ExecutionLog />
        </div>
      </div>
    </ReactFlowProvider>
  );
}
