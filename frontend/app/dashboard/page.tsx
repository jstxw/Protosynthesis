'use client';

import { useState, useMemo, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Search,
  Plus,
  ChevronDown,
  LogOut,
  Database,
  Sparkles,
  ArrowRight,
  MoreVertical,
  X
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { projectService, workflowService, type Project as ApiProject } from '@/services/projects';
import './dashboard.css';
import { NodeCard } from '@/components/NodeCard';

// Project data type for UI
interface Project {
  id: string;
  name: string;
  nodeCount: number;
  edgeCount: number;
  updatedAt: Date;
}

// Convert API project to UI project
function convertApiProject(apiProject: ApiProject): Project {
  let totalNodes = 0;
  let totalEdges = 0;
  let latestUpdate = new Date(apiProject.created_at);

  apiProject.workflows?.forEach((workflow) => {
    totalNodes += workflow.data?.nodes?.length || 0;
    totalEdges += workflow.data?.edges?.length || 0;

    const workflowUpdate = new Date(workflow.updated_at || workflow.created_at);
    if (workflowUpdate > latestUpdate) {
      latestUpdate = workflowUpdate;
    }
  });

  return {
    id: apiProject.project_id,
    name: apiProject.name,
    nodeCount: totalNodes,
    edgeCount: totalEdges,
    updatedAt: latestUpdate,
  };
}

// Format relative time
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} mins ago`;
  if (diffHours < 24) return `${diffHours} hours ago`;
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString();
}

type SortOption = 'newest' | 'oldest' | 'name';

// Main Dashboard Component
export function Dashboard() {
  const router = useRouter();
  const { user, signOut, loading } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [newProjectName, setNewProjectName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check authentication
  useEffect(() => {
    if (!loading && !user) {
      console.warn('User not authenticated, redirecting to login...');
      router.push('/login');
    }
  }, [user, loading, router]);

  // Fetch projects on mount (only when user is available)
  useEffect(() => {
    if (user && !loading) {
      fetchProjects();
    }
  }, [user, loading]);

  const fetchProjects = async () => {
    setIsLoading(true);
    try {
      const apiProjects = await projectService.getAllProjects();
      const uiProjects = apiProjects.map(convertApiProject);
      setProjects(uiProjects);
    } catch (err: any) {
      // Only log errors that aren't just "no projects found"
      const errorMessage = err?.message || err?.code || 'Unknown error';
      console.error('❌ Failed to fetch projects:', errorMessage, err);
      // Set empty array as fallback for new users
      setProjects([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('Failed to sign out:', error);
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    setIsCreating(true);
    setError(null);
    try {
      const newProject = await projectService.createProject({ name: newProjectName });

      // Create initial workflow
      const newWorkflow = await workflowService.createWorkflow(newProject.project_id, {
        name: 'Main Workflow',
        data: { nodes: [], edges: [] }
      });

      await fetchProjects();
      setShowNewProjectModal(false);
      setNewProjectName('');
      router.push(`/workflow?project=${newProject.project_id}&workflow=${newWorkflow.workflow_id}`);
    } catch (err: any) {
      console.error('Failed to create project:', err);
      // Handle different error formats
      let errorMessage = 'Failed to create project';
      if (err?.message) {
        errorMessage = err.message;
      } else if (err?.code) {
        errorMessage = `Error: ${err.code}`;
      } else if (typeof err === 'string') {
        errorMessage = err;
      } else if (err?.error) {
        errorMessage = err.error;
      }
      setError(errorMessage);
    } finally {
      setIsCreating(false);
    }
  };

  // Filter and sort projects
  const filteredProjects = useMemo(() => {
    let result = [...projects];

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter((p) => p.name.toLowerCase().includes(query));
    }

    result.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return b.updatedAt.getTime() - a.updatedAt.getTime();
        case 'oldest':
          return a.updatedAt.getTime() - b.updatedAt.getTime();
        case 'name':
          return a.name.localeCompare(b.name);
        default:
          return 0;
      }
    });

    return result;
  }, [projects, searchQuery, sortBy]);

  // Show loading while checking authentication
  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="flex items-center justify-center h-screen">
          <div className="text-[var(--node-text-color)]">Loading...</div>
        </div>
      </div>
    );
  }

  // Don't render if not authenticated
  if (!user) {
    return null;
  }

  return (
    <div className="dashboard-page">
      {/* Grid background */}
      <div className="dashboard-grid-bg" />

      {/* Wooden Sidebar */}
      <aside className="dashboard-sidebar">
        <div className="dashboard-sidebar-header">
          <h2 className="dashboard-sidebar-title">Projects</h2>
          <button onClick={handleLogout} className="dashboard-logout-btn" title="Logout">
            <LogOut size={16} />
          </button>
        </div>

        {/* Search in sidebar */}
        <div className="dashboard-sidebar-search">
          <Search className="dashboard-search-icon" size={14} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search projects..."
            className="dashboard-search-input"
          />
        </div>

        {/* Sort Options in Sidebar */}
        <div className="dashboard-sidebar-sort">
          <div className="dashboard-sort-label">Sort By</div>
          <button
            className={`dashboard-sort-btn ${sortBy === 'newest' ? 'active' : ''}`}
            onClick={() => setSortBy('newest')}
          >
            Newest
          </button>
          <button
            className={`dashboard-sort-btn ${sortBy === 'oldest' ? 'active' : ''}`}
            onClick={() => setSortBy('oldest')}
          >
            Oldest
          </button>
          <button
            className={`dashboard-sort-btn ${sortBy === 'name' ? 'active' : ''}`}
            onClick={() => setSortBy('name')}
          >
            A-Z
          </button>
        </div>

        {/* Projects List */}
        <div className="dashboard-projects-list">
          {isLoading ? (
            <div className="dashboard-sidebar-empty">Loading...</div>
          ) : filteredProjects.length > 0 ? (
            filteredProjects.map((project) => (
              <button
                key={project.id}
                onClick={async () => {
                  try {
                    // Fetch workflows for this project
                    let workflows = await workflowService.getAllWorkflows(project.id);

                    // If no workflows exist, create one
                    if (workflows.length === 0) {
                      console.log('No workflows found, creating default workflow...');
                      const newWorkflow = await workflowService.createWorkflow(project.id, {
                        name: 'Main Workflow',
                        data: { nodes: [], edges: [] }
                      });
                      workflows = [newWorkflow];
                    }

                    // Navigate with both project and workflow IDs
                    router.push(`/workflow?project=${project.id}&workflow=${workflows[0].workflow_id}`);
                  } catch (error) {
                    console.error('Error loading project:', error);
                    alert('Failed to load project. Please try again.');
                  }
                }}
                className="dashboard-project-item"
              >
                <div className="dashboard-project-icon">
                  <Database size={16} />
                </div>
                <div className="dashboard-project-details">
                  <div className="dashboard-project-name">{project.name}</div>
                  <div className="dashboard-project-meta">
                    {project.nodeCount} nodes · {formatRelativeTime(project.updatedAt)}
                  </div>
                </div>
              </button>
            ))
          ) : (
            <div className="dashboard-sidebar-empty">
              {searchQuery ? 'No projects found' : 'No projects yet'}
            </div>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="dashboard-main">
        <div className="dashboard-welcome">
          <h1 className="dashboard-welcome-title">
            Welcome, {user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'}
          </h1>
          <p className="dashboard-welcome-subtitle">Build and manage your API workflows visually</p>
        </div>

        {/* Floating Node-like Action Buttons */}
        <div className="dashboard-actions">
          <NodeCard
            title="Create Project"
            typeBadge="ACTION"
            icon={Plus}
            headerColorClass="node-header-start"
            onClick={() => setShowNewProjectModal(true)}
            className="dashboard-action-node cursor-pointer hover:-translate-y-1 transition-transform"
          >
            <div className="flex flex-col h-full justify-between gap-4">
              <p className="text-[var(--node-text-color)]">Start a new API workflow project from scratch or use a template</p>
              <div className="flex justify-end opacity-60">
                <ArrowRight size={16} />
              </div>
            </div>
          </NodeCard>

          {projects.length > 0 && (
            <NodeCard
              title="Load Project"
              typeBadge="ACTION"
              icon={Database}
              headerColorClass="node-header-react"
              onClick={async () => {
                try {
                  let workflows = await workflowService.getAllWorkflows(projects[0].id);

                  // If no workflows exist, create one
                  if (workflows.length === 0) {
                    console.log('No workflows found, creating default workflow...');
                    const newWorkflow = await workflowService.createWorkflow(projects[0].id, {
                      name: 'Main Workflow',
                      data: { nodes: [], edges: [] }
                    });
                    workflows = [newWorkflow];
                  }

                  router.push(`/workflow?project=${projects[0].id}&workflow=${workflows[0].workflow_id}`);
                } catch (error) {
                  console.error('Error loading project:', error);
                  alert('Failed to load project. Please try again.');
                }
              }}
              className="dashboard-action-node cursor-pointer hover:-translate-y-1 transition-transform"
            >
              <div className="flex flex-col h-full justify-between gap-4">
                <p className="text-[var(--node-text-color)]">Open your most recent project: <strong>{projects[0].name}</strong></p>
                <div className="flex justify-end opacity-60">
                  <ArrowRight size={16} />
                </div>
              </div>
            </NodeCard>
          )}

          <NodeCard
            title="Use Template"
            typeBadge="ACTION"
            icon={Sparkles}
            headerColorClass="node-header-string"
            onClick={() => setShowNewProjectModal(true)}
            className="dashboard-action-node cursor-pointer hover:-translate-y-1 transition-transform"
          >
            <div className="flex flex-col h-full justify-between gap-4">
              <p className="text-[var(--node-text-color)]">Start with pre-built workflows for common use cases</p>
              <div className="flex justify-end opacity-60">
                <ArrowRight size={16} />
              </div>
            </div>
          </NodeCard>
        </div>
      </main>

      {/* New Project Modal as a Node */}
      {showNewProjectModal && (
        <div className="dashboard-modal-overlay" onClick={() => setShowNewProjectModal(false)}>
          <div onClick={e => e.stopPropagation()}>
            <NodeCard
              title="New Project"
              typeBadge="MENU"
              icon={Plus}
              headerColorClass="node-header-start"
              width="500px"
              className="dashboard-modal-content"
            >
              <div style={{ padding: '24px' }}>
                <div style={{ marginBottom: '24px' }}>
                  <label
                    htmlFor="project-name"
                    className="block text-[13px] font-bold text-[var(--node-text-color)]"
                    style={{ marginBottom: '16px', display: 'block' }}
                  >
                    Project Name
                  </label>
                  <input
                    id="project-name"
                    type="text"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    placeholder="My Awesome Workflow"
                    className="w-full p-3 text-[13px] bg-[var(--input-bg-color)] border border-[var(--input-border-color)] rounded text-[var(--node-text-color)] focus:outline-none focus:border-[var(--color-blue)]"
                    autoFocus
                  />
                </div>

                {error && (
                  <div className="p-3 bg-red-100 border border-red-200 text-red-600 rounded text-[12px]" style={{ marginTop: '16px' }}>
                    {error}
                  </div>
                )}

                <div className="flex justify-end" style={{ marginTop: '24px', gap: '24px' }}>
                  <button
                    onClick={() => setShowNewProjectModal(false)}
                    className="px-4 py-2 rounded text-[var(--node-text-color)] text-[13px] font-medium hover:bg-[var(--item-bg-color)] transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateProject}
                    disabled={!newProjectName.trim() || isCreating}
                    className="px-6 py-2 rounded bg-[var(--color-green)] text-white text-[14px] font-bold hover:brightness-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                  >
                    {isCreating ? 'Creating...' : 'Create Project'}
                  </button>
                </div>
              </div>
            </NodeCard>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;

