# API Documentation - NodeLink v2

## Architecture Overview

This API uses a hybrid architecture:
- **Authentication**: Supabase Auth (JWT tokens)
- **Database**: MongoDB (nested User -> Projects -> Workflows structure)
- **Format**: JSON

## Authentication

All `/api/v2/*` endpoints require authentication via JWT token from Supabase.

### How to Authenticate

Include the JWT token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

### Getting the JWT Token

When a user logs in via Supabase (from your frontend), you'll receive a JWT token. Pass this token with every request to the backend.

Example from frontend:
```javascript
const { data: { session } } = await supabase.auth.getSession();
const token = session?.access_token;

// Use this token in API requests
fetch('http://localhost:5001/api/v2/projects', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

## Data Structure

```json
{
  "supabase_user_id": "uuid-from-supabase",
  "email": "user@example.com",
  "created_at": "2024-01-10T12:00:00Z",
  "projects": [
    {
      "project_id": "uuid",
      "name": "My Project",
      "created_at": "2024-01-10T12:00:00Z",
      "updated_at": "2024-01-10T12:00:00Z",
      "workflows": [
        {
          "workflow_id": "uuid",
          "name": "My Workflow",
          "created_at": "2024-01-10T12:00:00Z",
          "updated_at": "2024-01-10T12:00:00Z",
          "data": {
            "nodes": [],
            "edges": []
          }
        }
      ]
    }
  ]
}
```

---

## API Endpoints

Base URL: `http://localhost:5001`

### User Endpoints

#### Initialize User
**POST** `/api/v2/user/init`

Call this endpoint after a user signs up via Supabase to create their MongoDB document.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "message": "User initialized",
  "user": {
    "supabase_user_id": "uuid",
    "email": "user@example.com"
  }
}
```

---

#### Get Current User
**GET** `/api/v2/user/me`

Get the authenticated user's profile and all their projects.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "supabase_user_id": "uuid",
  "email": "user@example.com",
  "created_at": "2024-01-10T12:00:00Z",
  "projects": [...]
}
```

---

### Project Endpoints

#### List All Projects
**GET** `/api/v2/projects`

Get all projects for the authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "projects": [
    {
      "project_id": "uuid",
      "name": "Project 1",
      "created_at": "2024-01-10T12:00:00Z",
      "updated_at": "2024-01-10T12:00:00Z",
      "workflows": [...]
    }
  ]
}
```

---

#### Create Project
**POST** `/api/v2/projects`

Create a new project.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Body:**
```json
{
  "name": "My New Project"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Project created",
  "project": {
    "project_id": "uuid",
    "name": "My New Project",
    "created_at": "2024-01-10T12:00:00Z",
    "updated_at": "2024-01-10T12:00:00Z",
    "workflows": []
  }
}
```

---

#### Get Project
**GET** `/api/v2/projects/<project_id>`

Get a specific project by ID.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "project_id": "uuid",
  "name": "My Project",
  "created_at": "2024-01-10T12:00:00Z",
  "updated_at": "2024-01-10T12:00:00Z",
  "workflows": [...]
}
```

---

#### Update Project
**PUT** `/api/v2/projects/<project_id>`

Update project metadata (currently only name).

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Body:**
```json
{
  "name": "Updated Project Name"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Project updated"
}
```

---

#### Delete Project
**DELETE** `/api/v2/projects/<project_id>`

Delete a project and all its workflows.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Project deleted"
}
```

---

### Workflow Endpoints

#### List Workflows
**GET** `/api/v2/projects/<project_id>/workflows`

Get all workflows for a project.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "workflows": [
    {
      "workflow_id": "uuid",
      "name": "Workflow 1",
      "created_at": "2024-01-10T12:00:00Z",
      "updated_at": "2024-01-10T12:00:00Z",
      "data": {
        "nodes": [],
        "edges": []
      }
    }
  ]
}
```

---

#### Create Workflow
**POST** `/api/v2/projects/<project_id>/workflows`

Create a new workflow in a project.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Body:**
```json
{
  "name": "My Workflow",
  "data": {
    "nodes": [],
    "edges": []
  }
}
```

**Note:** `data` field is optional. If not provided, defaults to `{"nodes": [], "edges": []}`.

**Response:**
```json
{
  "status": "success",
  "message": "Workflow created",
  "workflow": {
    "workflow_id": "uuid",
    "name": "My Workflow",
    "created_at": "2024-01-10T12:00:00Z",
    "updated_at": "2024-01-10T12:00:00Z",
    "data": {
      "nodes": [],
      "edges": []
    }
  }
}
```

---

#### Get Workflow
**GET** `/api/v2/projects/<project_id>/workflows/<workflow_id>`

Get a specific workflow by ID.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "workflow_id": "uuid",
  "name": "My Workflow",
  "created_at": "2024-01-10T12:00:00Z",
  "updated_at": "2024-01-10T12:00:00Z",
  "data": {
    "nodes": [...],
    "edges": [...]
  }
}
```

---

#### Update Workflow Data
**PUT** `/api/v2/projects/<project_id>/workflows/<workflow_id>`

Update workflow data (nodes, edges, config).

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Body (Update Data):**
```json
{
  "data": {
    "nodes": [
      {
        "id": "node1",
        "type": "API",
        "name": "API Block",
        "x": 100,
        "y": 200
      }
    ],
    "edges": []
  }
}
```

**Body (Update Name):**
```json
{
  "name": "Updated Workflow Name"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Workflow updated"
}
```

---

#### Delete Workflow
**DELETE** `/api/v2/projects/<project_id>/workflows/<workflow_id>`

Delete a workflow from a project.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "message": "Workflow deleted"
}
```

---

#### Execute Workflow
**POST** `/api/v2/projects/<project_id>/workflows/<workflow_id>/execute`

Execute a workflow (integration with execution engine coming soon).

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "execution_started",
  "workflow_id": "uuid",
  "message": "Execution engine integration coming soon",
  "workflow_data": {
    "nodes": [],
    "edges": []
  }
}
```

---

## Error Responses

All endpoints return error responses in this format:

```json
{
  "error": "Error message description"
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (missing required fields)
- `401` - Unauthorized (invalid or missing JWT token)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

---

## Setup Instructions

### 1. Get Supabase JWT Secret

1. Go to your Supabase project dashboard
2. Navigate to Settings -> API
3. Find "JWT Secret" under the "JWT Settings" section
4. Copy the secret

### 2. Update .env File

Add the JWT secret to `/backend/.env`:

```
SUPABASE_JWT_SECRET=your-actual-jwt-secret-here
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Start the Server

```bash
python main.py
```

---

## Frontend Integration Example

### Login and Initialize User

```javascript
// 1. User logs in via Supabase
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
});

// 2. Get the JWT token
const token = data.session.access_token;

// 3. Initialize user in MongoDB
await fetch('http://localhost:5001/api/v2/user/init', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### Create and Manage Workflows

```javascript
// Get the token from Supabase session
const { data: { session } } = await supabase.auth.getSession();
const token = session.access_token;

// Create a project
const projectRes = await fetch('http://localhost:5001/api/v2/projects', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ name: 'My Project' })
});

const { project } = await projectRes.json();

// Create a workflow
const workflowRes = await fetch(
  `http://localhost:5001/api/v2/projects/${project.project_id}/workflows`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'My Workflow',
      data: { nodes: [], edges: [] }
    })
  }
);

const { workflow } = await workflowRes.json();

// Update workflow
await fetch(
  `http://localhost:5001/api/v2/projects/${project.project_id}/workflows/${workflow.workflow_id}`,
  {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      data: {
        nodes: [{ id: 'node1', type: 'API', x: 100, y: 200 }],
        edges: []
      }
    })
  }
);
```

---

## Testing with cURL

### Initialize User
```bash
curl -X POST http://localhost:5001/api/v2/user/init \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Create Project
```bash
curl -X POST http://localhost:5001/api/v2/projects \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project"}'
```

### Get All Projects
```bash
curl -X GET http://localhost:5001/api/v2/projects \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Create Workflow
```bash
curl -X POST http://localhost:5001/api/v2/projects/PROJECT_ID/workflows \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Workflow", "data": {"nodes": [], "edges": []}}'
```
