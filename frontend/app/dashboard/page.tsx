'use client';

import { useState, useMemo, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Search,
  Plus,
  ChevronDown,
  MoreVertical,
  ArrowRight,
  Link2,
  Clock,
  LogOut,
  CreditCard,
  Mail,
  Database,
  Sparkles,
  MessageSquare,
  Globe,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { projectService, workflowService, type Project as ApiProject } from '@/services/projects';

// Logo component
function Logo() {
  return (
    <div className="flex items-center gap-3">

      <div>
        <h1 className="text-lg font-semibold text-text-primary"></h1>
      </div>
    </div>
  );
}

// Project data type for UI
interface Project {
  id: string;
  name: string;
  nodeCount: number;
  edgeCount: number;
  updatedAt: Date;
  thumbnail?: string;
}

// Convert API project to UI project
function convertApiProject(apiProject: ApiProject): Project {
  // Calculate total nodes and edges across all workflows
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
  if (diffMins < 60) return `${diffMins} minutes ago`;
  if (diffHours < 24) return `${diffHours} hours ago`;
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString();
}

// Sort options
type SortOption = 'newest' | 'oldest' | 'name';
const sortLabels: Record<SortOption, string> = {
  newest: 'Last Modified (Newest)',
  oldest: 'Last Modified (Oldest)',
  name: 'Name (A-Z)',
};

// Project Card Component
function ProjectCard({ project, onOpen }: { project: Project; onOpen: () => void }) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div className="card group">
      {/* Thumbnail */}
      <div className="card-thumbnail relative">
        {/* Dot grid pattern */}
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage: 'radial-gradient(circle, #3A3A3A 1px, transparent 1px)',
            backgroundSize: '20px 20px',
          }}
        />
        {/* Placeholder workflow preview */}
        <div className="relative flex items-center justify-center gap-4">
          <div className="w-16 h-10 bg-app-component rounded-md border border-border flex items-center justify-center">
            <div className="w-3 h-3 rounded-full bg-category-compute" />
          </div>
          <div className="w-8 border-t border-dashed border-border-hover" />
          <div className="w-16 h-10 bg-app-component rounded-md border border-border flex items-center justify-center">
            <div className="w-3 h-3 rounded-full bg-category-storage" />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="card-content">
        <div className="flex items-start justify-between mb-2">
          <h3 className="text-label text-text-primary font-medium truncate pr-2">
            {project.name}
          </h3>
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="btn-icon p-1 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <MoreVertical className="w-4 h-4" />
            </button>
            {showMenu && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowMenu(false)} />
                <div className="dropdown-menu right-0 top-full mt-1">
                  <button className="dropdown-item w-full text-left">Duplicate</button>
                  <button className="dropdown-item w-full text-left">Rename</button>
                  <div className="dropdown-divider" />
                  <button className="dropdown-item w-full text-left text-status-error">Delete</button>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3 text-small text-text-tertiary mb-3">
          <span>{project.nodeCount} nodes</span>
          <span className="w-1 h-1 rounded-full bg-text-tertiary" />
          <span>{project.edgeCount} edges</span>
        </div>

        <div className="flex items-center gap-1 text-small text-text-tertiary mb-4">
          <Clock className="w-3.5 h-3.5" />
          <span>{formatRelativeTime(project.updatedAt)}</span>
        </div>

        <button onClick={onOpen} className="btn-secondary w-full justify-center group/btn">
          <span>Open Project</span>
          <ArrowRight className="w-4 h-4 transition-transform group-hover/btn:translate-x-1" />
        </button>
      </div>
    </div>
  );
}

// Template icon component
function TemplateIcon({ template }: { template: { icon: React.ElementType; color: string } }) {
  const IconComponent = template.icon;
  return (
    <div
      className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
      style={{ backgroundColor: `${template.color}20` }}
    >
      <IconComponent className="w-5 h-5" style={{ color: template.color }} />
    </div>
  );
}

// New Project Modal
function NewProjectModal({
  isOpen,
  onClose,
  onProjectCreated
}: {
  isOpen: boolean;
  onClose: () => void;
  onProjectCreated: () => void;
}) {
  const router = useRouter();
  const [mode, setMode] = useState<'scratch' | 'template'>('scratch');
  const [projectName, setProjectName] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const categories = ['All', 'Payment', 'Email', 'Database', 'AI', 'Messaging', 'Integration'];

  const templates = [
    {
      id: 'stripe-airtable',
      name: 'Stripe → Airtable',
      description: 'Log successful payments from Stripe to Airtable for tracking and analytics',
      complexity: 'simple' as const,
      nodeCount: 2,
      edgeCount: 1,
      category: 'Payment',
      icon: CreditCard,
      color: '#635BFF',
    },
    {
      id: 'stripe-sendgrid-airtable',
      name: 'Stripe → SendGrid → Airtable',
      description: 'Process payments, send confirmation emails, and log to database',
      complexity: 'medium' as const,
      nodeCount: 3,
      edgeCount: 2,
      category: 'Payment',
      icon: CreditCard,
      color: '#635BFF',
    },
    {
      id: 'webhook-openai-email',
      name: 'Webhook → OpenAI → Email',
      description: 'Receive webhooks, process with AI, and send email responses',
      complexity: 'medium' as const,
      nodeCount: 3,
      edgeCount: 2,
      category: 'AI',
      icon: Sparkles,
      color: '#10A37F',
    },
    {
      id: 'form-sheets-sendgrid',
      name: 'Form → Sheets → SendGrid',
      description: 'Capture form submissions, store in Google Sheets, send notifications',
      complexity: 'simple' as const,
      nodeCount: 3,
      edgeCount: 2,
      category: 'Email',
      icon: Mail,
      color: '#1A82E2',
    },
    {
      id: 'airtable-openai-twilio',
      name: 'Airtable → OpenAI → Twilio',
      description: 'Fetch records, generate AI responses, send SMS notifications',
      complexity: 'medium' as const,
      nodeCount: 3,
      edgeCount: 2,
      category: 'AI',
      icon: Sparkles,
      color: '#10A37F',
    },
    {
      id: 'webhook-multi-api',
      name: 'Multi-API Integration',
      description: 'Complex workflow connecting multiple APIs with conditional routing',
      complexity: 'complex' as const,
      nodeCount: 6,
      edgeCount: 7,
      category: 'Integration',
      icon: Globe,
      color: '#6366F1',
    },
    {
      id: 'crm-sync',
      name: 'CRM Data Sync',
      description: 'Sync customer data between multiple platforms automatically',
      complexity: 'complex' as const,
      nodeCount: 5,
      edgeCount: 6,
      category: 'Database',
      icon: Database,
      color: '#18BFFF',
    },
    {
      id: 'notification-hub',
      name: 'Notification Hub',
      description: 'Central notification system with email, SMS, and push notifications',
      complexity: 'complex' as const,
      nodeCount: 5,
      edgeCount: 4,
      category: 'Messaging',
      icon: MessageSquare,
      color: '#F22F46',
    },
  ];

  const filteredTemplates = selectedCategory === 'All'
    ? templates
    : templates.filter(t => t.category === selectedCategory);

  const handleCreate = async () => {
    if (!projectName.trim()) {
      setError('Please enter a project name');
      return;
    }

    setIsCreating(true);
    setError(null);

    try {
      // Create the project
      const project = await projectService.createProject({
        name: projectName.trim()
      });

      console.log('✅ Project created:', project);

      // Create a workflow in the project
      const workflow = await workflowService.createWorkflow(project.project_id, {
        name: 'Main Workflow',
        data: { nodes: [], edges: [] }
      });

      console.log('✅ Workflow created:', workflow);

      // Notify parent to refresh projects list
      onProjectCreated();

      // Navigate to the workflow editor with the project and workflow IDs
      router.push(`/workflow?project=${project.project_id}&workflow=${workflow.workflow_id}`);
      onClose();
    } catch (err: any) {
      console.error('❌ Failed to create project:', err);
      setError(err.message || 'Failed to create project. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-container max-w-2xl flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header flex-shrink-0">
          <h2 className="modal-title">Create New Project</h2>
          <button onClick={onClose} className="btn-icon">
            <span className="text-xl leading-none">&times;</span>
          </button>
        </div>

        <div className="modal-body space-y-6 flex-1 overflow-y-auto">
          {/* Start with options */}
          <div>
            <p className="text-body text-text-secondary mb-4">Start with:</p>
            <div className="space-y-3">
              {/* Start from Scratch */}
              <label
                className={`flex items-start gap-4 p-4 rounded-lg border cursor-pointer transition-all ${mode === 'scratch'
                  ? 'border-accent-blue bg-accent-blue/5'
                  : 'border-border hover:border-border-hover'
                  }`}
              >
                <input
                  type="radio"
                  name="mode"
                  checked={mode === 'scratch'}
                  onChange={() => setMode('scratch')}
                  className="mt-1 accent-accent-blue"
                />
                <div className="flex items-center gap-3 flex-1">
                  <div className="w-8 h-8 rounded-md bg-app-component flex items-center justify-center">
                    <Plus className="w-5 h-5 text-text-secondary" />
                  </div>
                  <div>
                    <p className="text-label text-text-primary">Start from Scratch</p>
                    <p className="text-small text-text-tertiary">
                      Create an empty project and build your API workflow from the ground up
                    </p>
                  </div>
                </div>
              </label>

              {/* Use Template */}
              <label
                className={`flex items-start gap-4 p-4 rounded-lg border cursor-pointer transition-all ${mode === 'template'
                  ? 'border-accent-blue bg-accent-blue/5'
                  : 'border-border hover:border-border-hover'
                  }`}
              >
                <input
                  type="radio"
                  name="mode"
                  checked={mode === 'template'}
                  onChange={() => setMode('template')}
                  className="mt-1 accent-accent-blue"
                />
                <div className="flex items-center gap-3 flex-1">
                  <div className="w-8 h-8 rounded-md bg-app-component flex items-center justify-center">
                    <Link2 className="w-5 h-5 text-text-secondary" />
                  </div>
                  <div>
                    <p className="text-label text-text-primary">Use Template</p>
                    <p className="text-small text-text-tertiary">
                      Start from a pre-built API connection template
                    </p>
                  </div>
                </div>
              </label>
            </div>
          </div>

          {/* Template Selection */}
          {mode === 'template' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-body text-text-secondary">Select a Template</p>
                <button onClick={() => setSelectedTemplate(null)} className="text-small text-text-tertiary hover:text-text-secondary">
                  Clear
                </button>
              </div>

              {/* Category pills */}
              <div className="flex flex-wrap gap-2">
                {categories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`px-3 py-1.5 rounded-md text-small font-medium transition-colors ${selectedCategory === cat
                      ? 'bg-accent-blue text-white'
                      : 'bg-app-component text-text-secondary hover:text-text-primary'
                      }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* Template grid */}
              <div className="grid grid-cols-2 gap-3 max-h-[240px] overflow-y-auto pr-2">
                {filteredTemplates.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => setSelectedTemplate(template.id)}
                    className={`p-4 rounded-lg border text-left transition-all ${selectedTemplate === template.id
                      ? 'border-accent-blue bg-accent-blue/5'
                      : 'border-border hover:border-border-hover'
                      }`}
                  >
                    <div className="flex items-start gap-3 mb-3">
                      <TemplateIcon template={template} />
                      <div className="flex-1 min-w-0">
                        <p className="text-label text-text-primary">{template.name}</p>
                        <p className="text-small text-text-tertiary line-clamp-2 mt-0.5">
                          {template.description}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`badge ${template.complexity === 'simple'
                          ? 'badge-simple'
                          : template.complexity === 'medium'
                            ? 'badge-medium'
                            : 'badge-complex'
                          }`}
                      >
                        {template.complexity}
                      </span>
                      <span className="text-small text-text-tertiary">
                        {template.nodeCount} APIs &bull; {template.edgeCount} connections
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Project Name */}
          <div>
            <label className="form-label">Project Name</label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="My API Workflow"
              className="form-input"
              autoFocus
              disabled={isCreating}
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 rounded-lg bg-status-error/10 border border-status-error/20">
              <p className="text-small text-status-error">{error}</p>
            </div>
          )}
        </div>

        <div className="modal-footer flex-shrink-0 border-t border-border bg-black">
          <button onClick={onClose} className="btn-secondary" disabled={isCreating}>
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={isCreating || !projectName.trim() || (mode === 'template' && !selectedTemplate)}
            className="btn-primary"
          >
            {isCreating ? 'Creating...' : 'Create Project'}
          </button>
        </div>
      </div>
    </div>
  );
}

// Main Dashboard Component
export function Dashboard() {
  const router = useRouter();
  const { user, signOut } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [showSortMenu, setShowSortMenu] = useState(false);
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch projects on mount
  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const apiProjects = await projectService.getAllProjects();
      const uiProjects = apiProjects.map(convertApiProject);
      setProjects(uiProjects);
      console.log('✅ Fetched projects:', uiProjects);
    } catch (err: any) {
      console.error('❌ Failed to fetch projects:', err);
      setError('Failed to load projects');
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

  // Filter and sort projects
  const filteredProjects = useMemo(() => {
    let result = [...projects];

    // Filter by search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter((p) => p.name.toLowerCase().includes(query));
    }

    // Sort
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

  return (
    <div className="min-h-screen bg-app-bg">
      {/* Header */}
      <header className="border-b border-border-subtle">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Logo />
          <button onClick={handleLogout} className="btn-ghost text-small">
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-hero text bold italic text-text-primary mb-2">
            Welcome {user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'},
          </h2>
          <p className="text-body text-text-secondary">
            Build and manage your API workflows visually
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between mb-6">
          {/* Search */}
          <div className="relative w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search projects..."
              className="form-input pl-10"
            />
          </div>

          <div className="flex items-center gap-4">
            {/* Sort Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowSortMenu(!showSortMenu)}
                className="btn-secondary text-small"
              >
                <span>{sortLabels[sortBy]}</span>
                <ChevronDown className="w-4 h-4" />
              </button>
              {showSortMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowSortMenu(false)} />
                  <div className="dropdown-menu right-0 top-full mt-1">
                    {(Object.keys(sortLabels) as SortOption[]).map((option) => (
                      <button
                        key={option}
                        onClick={() => {
                          setSortBy(option);
                          setShowSortMenu(false);
                        }}
                        className={`dropdown-item w-full text-left ${sortBy === option ? 'active' : ''}`}
                      >
                        {sortLabels[option]}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* New Project Button */}
            <button onClick={() => setShowNewProjectModal(true)} className="btn-primary">
              <Plus className="w-4 h-4" />
              <span>New Project</span>
            </button>
          </div>
        </div>

        {/* Projects Grid - White Border Container */}
        <div className="border-2 border-white/20 mt-9 rounded-sm p-8 min-h-[400px]">
          {isLoading ? (
            <div className="text-center my-24">
              <p className="text-body text-text-secondary">Loading projects...</p>
            </div>
          ) : error ? (
            <div className="text-center my-24">
              <p className="text-body text-status-error mb-4">{error}</p>
              <button onClick={fetchProjects} className="btn-secondary">
                Retry
              </button>
            </div>
          ) : filteredProjects.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredProjects.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onOpen={() => router.push('/workflow')}
                />
              ))}
            </div>
          ) : (
            <div className="text-center my-24">

              <h3 className="text-heading text-text-primary mb-2 text-center">
                {searchQuery ? 'No projects found' : 'No projects yet'}
              </h3>
              <p className="text-body text-text-secondary mb-6">
                {searchQuery
                  ? `No projects match "${searchQuery}"`
                  : 'Create your first API workflow to get started'}
              </p>

            </div>
          )}
        </div>
      </main>

      {/* New Project Modal */}
      <NewProjectModal
        isOpen={showNewProjectModal}
        onClose={() => setShowNewProjectModal(false)}
        onProjectCreated={fetchProjects}
      />
    </div>
  );
}

export default Dashboard;
