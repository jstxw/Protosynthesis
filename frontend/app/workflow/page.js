'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { ReactFlowProvider } from 'reactflow';
import ControlPanel from '@/components/ControlPanel';
import dynamic from 'next/dynamic';
import ExecutionLog from '@/components/ExecutionLog';
import AIAssistantPanel from '@/components/Assistant/AIAssistantPanel';
import ReactIDE from '@/components/ReactIDE'; // Import new ReactIDE
import ChatButton from '@/components/ChatButton';
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
  const nodes = useStore((state) => state.nodes);
  const edges = useStore((state) => state.edges);
  const activeBlockId = useStore((state) => state.activeBlockId);
  const selectedNodeId = useStore((state) => state.selectedNodeId || state.activeBlockId);

  const projectId = searchParams.get('project');
  const workflowId = searchParams.get('workflow');

  // Get node types for AI context
  const currentNodeTypes = nodes.map(node => node.data?.type || node.type).filter(Boolean);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  // Load workflow when project and workflow IDs are available
  // Only load once when the IDs change, not when store functions update
  useEffect(() => {
    if (projectId && workflowId && user) {
      console.log('Loading workflow:', { projectId, workflowId });
      setCurrentWorkflow(projectId, workflowId);
      loadWorkflowFromV2(projectId, workflowId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, workflowId, user]);

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

        {/* React IDE as popup/modal */}
        <ReactIDE />

        {/* AI Assistant positioned at bottom-right */}
        <AIAssistantPanel
          currentNodes={currentNodeTypes}
          selectedNode={activeBlockId}
          projectId={projectId}
          workflowId={workflowId}
          nodes={nodes}
          edges={edges}
        />

        {/* Floating chat button */}
        <ChatButton />
      </div>
    </ReactFlowProvider>
  );
}
