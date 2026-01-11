import { apiClient } from './api';

export interface Project {
  project_id: string;
  name: string;
  created_at: string;
  workflows: Workflow[];
}

export interface Workflow {
  workflow_id: string;
  name: string;
  created_at: string;
  updated_at: string;
  data: {
    nodes: any[];
    edges: any[];
  };
}

export interface CreateProjectRequest {
  name: string;
}

export interface CreateWorkflowRequest {
  name: string;
  data?: {
    nodes: any[];
    edges: any[];
  };
}

export interface UpdateWorkflowRequest {
  data?: {
    nodes: any[];
    edges: any[];
  };
  name?: string;
}

/**
 * Project API Service
 */
export const projectService = {
  /**
   * Get all projects for the current user
   */
  async getAllProjects(): Promise<Project[]> {
    const response = await apiClient.get('/v2/projects');
    return response.data.projects || [];
  },

  /**
   * Get a specific project by ID
   */
  async getProject(projectId: string): Promise<Project> {
    const response = await apiClient.get(`/v2/projects/${projectId}`);
    return response.data;
  },

  /**
   * Create a new project
   */
  async createProject(data: CreateProjectRequest): Promise<Project> {
    const response = await apiClient.post('/v2/projects', data);
    return response.data.project;
  },

  /**
   * Update project metadata
   */
  async updateProject(projectId: string, data: { name: string }): Promise<void> {
    await apiClient.put(`/v2/projects/${projectId}`, data);
  },

  /**
   * Delete a project
   */
  async deleteProject(projectId: string): Promise<void> {
    await apiClient.delete(`/v2/projects/${projectId}`);
  },
};

/**
 * Workflow API Service
 */
export const workflowService = {
  /**
   * Get all workflows for a project
   */
  async getAllWorkflows(projectId: string): Promise<Workflow[]> {
    const response = await apiClient.get(`/v2/projects/${projectId}/workflows`);
    return response.data.workflows || [];
  },

  /**
   * Get a specific workflow
   */
  async getWorkflow(projectId: string, workflowId: string): Promise<Workflow> {
    const response = await apiClient.get(`/v2/projects/${projectId}/workflows/${workflowId}`);
    return response.data;
  },

  /**
   * Create a new workflow in a project
   */
  async createWorkflow(projectId: string, data: CreateWorkflowRequest): Promise<Workflow> {
    const response = await apiClient.post(`/v2/projects/${projectId}/workflows`, data);
    return response.data.workflow;
  },

  /**
   * Update workflow data or metadata
   */
  async updateWorkflow(
    projectId: string,
    workflowId: string,
    data: UpdateWorkflowRequest
  ): Promise<void> {
    await apiClient.put(`/v2/projects/${projectId}/workflows/${workflowId}`, data);
  },

  /**
   * Delete a workflow
   */
  async deleteWorkflow(projectId: string, workflowId: string): Promise<void> {
    await apiClient.delete(`/v2/projects/${projectId}/workflows/${workflowId}`);
  },

  /**
   * Execute a workflow
   */
  async executeWorkflow(projectId: string, workflowId: string): Promise<any> {
    const response = await apiClient.post(
      `/v2/projects/${projectId}/workflows/${workflowId}/execute`
    );
    return response.data;
  },
};
