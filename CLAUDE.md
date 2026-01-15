# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Protosynthesis is a visual API workflow automation platform - a no-code tool for building complex API workflows using a drag-and-drop node-based interface. Users create workflows by connecting "blocks" (nodes) that represent API calls, data transformations, logic operations, and UI components.

**Key Architecture:**
- **Frontend**: Next.js 16 + React 19 + TypeScript with ReactFlow for the visual canvas
- **Backend**: Flask (Python) with topological sort execution engine
- **Database**: MongoDB Atlas with nested document structure (Users -> Projects -> Workflows)
- **Auth**: Supabase JWT (supports both ES256 and HS256)
- **Real-time**: Streaming execution updates (non-WebSocket, uses HTTP streaming)

## Development Commands

### Frontend
```bash
cd frontend
npm install              # Install dependencies
npm run dev             # Start dev server (http://localhost:3000)
npm run build           # Build for production
npm run lint            # Run ESLint
```

### Backend
```bash
cd backend
python -m venv venv                    # Create virtual environment
source venv/bin/activate               # Activate (macOS/Linux)
# venv\Scripts\activate                # Activate (Windows)
pip install -r requirements.txt        # Install dependencies
python main.py                         # Start Flask server (http://localhost:5001)
```

**Default Ports:**
- Frontend: `localhost:3000`
- Backend: `localhost:5001` (configurable via `PORT` env var)

## Core Architecture Concepts

### 1. Block System (Backend)

The block system is the execution engine's foundation. All blocks inherit from `blocks.py::Block`:

- **Block Base Class** (`blocks.py`): Defines abstract interface with inputs/outputs, connectors, and execute() method
- **Connector Class**: Represents edges between blocks, handles data transfer with optional modifiers
- **Port System**: Blocks register inputs/outputs with metadata (data_type, required, validation rules)
- **Block Factory Pattern**: Block types in `block_types/` implement specific behaviors (APIBlock, LogicBlock, TransformBlock, etc.)

**Key Block Types:**
- `StartBlock`: Workflow entry point
- `APIBlock`: HTTP request executor with 23+ pre-configured API schemas (Stripe, OpenAI, Slack, etc.)
- `TransformBlock`: Data manipulation (JSON parsing, key extraction, type conversion)
- `LogicBlock`: Arithmetic and boolean operations
- `ReactBlock`: Renders React components in browser (Monaco editor integration)
- `StringBuilderBlock`: Template engine for dynamic string generation
- `WaitBlock`: Delays execution
- `DialogueBlock`: User prompts/messages
- `ApiKeyBlock`: Secure credential storage

### 2. Execution Engine (main.py)

The execution engine uses **topological sorting** to execute workflows:

1. **Discovery Phase**: BFS traversal from StartBlock to find all reachable blocks
2. **Dependency Graph**: Build DAG with in-degree tracking for each block
3. **Execution Phase**: Kahn's algorithm for topological sort
   - Blocks with in-degree 0 are ready to execute
   - Each block calls `fetch_inputs()` to pull data from connected upstream blocks
   - Execute block logic via `execute()` method
   - Decrement downstream blocks' in-degrees
   - Stream progress events as JSON lines

**Streaming Protocol:**
```json
{"type": "start", "block_id": "...", "block_type": "...", "inputs": {...}}
{"type": "progress", "block_id": "...", "outputs": {...}}
{"type": "error", "block_id": "...", "error": "..."}
{"type": "complete"}
```

### 3. Data Model (MongoDB)

**Nested Document Structure:**
```
User {
  supabase_user_id: string (indexed)
  email: string (indexed)
  created_at: ISO timestamp
  projects: [
    {
      project_id: UUID
      name: string
      created_at: ISO timestamp
      updated_at: ISO timestamp
      workflows: [
        {
          workflow_id: UUID
          name: string
          created_at: ISO timestamp
          updated_at: ISO timestamp
          data: {
            nodes: [{id, type, position, data}, ...]
            edges: [{id, source, target, sourceHandle, targetHandle}, ...]
          }
        }
      ]
    }
  ]
}
```

**Important:** Projects and workflows are embedded documents, NOT separate collections. Use `user_service.py` for all CRUD operations to ensure proper nested updates.

### 4. Frontend State Management (store.js)

**Zustand Store** manages all application state:
- `nodes`, `edges`: ReactFlow graph data
- `currentProjectId`, `currentWorkflowId`: Active workflow context
- `executionLogs`, `isExecuting`, `activeBlockId`: Execution state
- `selectedNodeId`, `hoveredNodeId`: UI selection state
- `apiSchemas`: API configuration library (fetched from `/api/schemas`)

**Auto-save System:**
- Triggered by `scheduleAutoSave()` after node/edge changes
- 2-second debounce to batch updates
- Saves to `/api/v2/projects/{projectId}/workflows/{workflowId}` via `apiClient`

**Port Normalization:**
The store normalizes inputs/outputs between object format `{key: value}` and array format `[{key, value, data_type}]`. Array format is canonical for ReactFlow rendering.

### 5. Authentication Flow

**Supabase JWT with dual algorithm support:**
1. Frontend: User logs in via Supabase Auth, receives JWT
2. Frontend: Sends JWT in `Authorization: Bearer <token>` header
3. Backend: `auth_middleware.py::require_auth` decorator validates token
   - **ES256**: Fetches public key from Supabase JWKS endpoint (`/auth/v1/.well-known/jwks.json`)
   - **HS256**: Uses `SUPABASE_JWT_SECRET` env var
4. Backend: Extracts `sub` (user ID) and `email` from decoded payload
5. Backend: Passes `current_user` dict to route handlers

**Lazy User Initialization:** If a user doesn't exist in MongoDB when they first create a project, `UserService` will auto-create them using their Supabase ID and email.

## API Routes

### V2 Authenticated Routes (api_routes.py)

All routes require `Authorization: Bearer <token>` header:

**Projects:**
- `POST /api/v2/projects` - Create project
- `GET /api/v2/projects` - List all projects
- `GET /api/v2/projects/<id>` - Get project
- `PUT /api/v2/projects/<id>` - Update project
- `DELETE /api/v2/projects/<id>` - Delete project

**Workflows:**
- `POST /api/v2/projects/<pid>/workflows` - Create workflow
- `GET /api/v2/projects/<pid>/workflows` - List workflows
- `GET /api/v2/projects/<pid>/workflows/<wid>` - Get workflow
- `PUT /api/v2/projects/<pid>/workflows/<wid>` - Update workflow (auto-save target)
- `DELETE /api/v2/projects/<pid>/workflows/<wid>` - Delete workflow
- `POST /api/v2/projects/<pid>/workflows/<wid>/execute` - Execute workflow (streaming)

**Blocks:**
- `POST /api/v2/blocks/process-schema` - Process API block schema changes (returns updated block structure)

**Utility:**
- `GET /api/schemas` - Get all API schemas (no auth required)

### AI Routes

- `POST /api/ai/recommend` - Get AI recommendations for next workflow steps
- `POST /api/agent/chat` - Gemini conversational agent

## Working with Blocks

### Adding a New Block Type

1. Create `backend/block_types/my_block.py`:
```python
from blocks import Block

class MyBlock(Block):
    def __init__(self, name, x=0, y=0, **params):
        super().__init__(name, "MY_BLOCK", x, y)

        # Register inputs/outputs
        self.register_input("input_key", data_type="string", default_value="")
        self.register_output("output_key", data_type="string")

        # Block-specific config
        self.my_param = params.get('my_param', 'default')

    def execute(self):
        # Core logic - read from self.inputs, write to self.outputs
        input_value = self.inputs.get("input_key")
        self.outputs["output_key"] = process(input_value)

    def to_dict(self):
        # Serialize block state for frontend
        base = super().to_dict()
        base["my_param"] = self.my_param
        return base
```

2. Import in `main.py` and add to block factory map
3. Add frontend initialization in `store.js::initializeBlockData()` switch case
4. Update `CustomNode.js` rendering if special UI needed

### Modifying API Schemas

API schemas are defined in `backend/api_schemas.py`. Each schema specifies:
- URL template with `{placeholders}`
- HTTP method
- Input sections (params, headers, body, path)
- Output keys
- Field metadata (required, validation, placeholder, description)

When a user selects an API schema in the frontend, it calls `/api/v2/blocks/process-schema` which instantiates a temporary APIBlock to generate the full port structure.

## Important Patterns

### Data Flow Between Blocks

1. User creates edge in ReactFlow canvas
2. Frontend calls `store.onConnect()` -> saves edge to state
3. On execution, backend reconstructs block graph from nodes/edges data
4. Topological sort ensures upstream blocks execute before downstream
5. Each block calls `fetch_inputs()` which reads from upstream `connector.source_block.outputs`
6. Block processes inputs and writes to `self.outputs`
7. Downstream blocks fetch these outputs via connectors

### Template System

Templates are pre-configured workflows in `TEMPLATES_GUIDE.md`. They're loaded by:
1. Frontend sends template selection to backend
2. Backend returns workflow data with nodes/edges in ReactFlow format
3. Frontend calls `loadWorkflowFromV2()` to populate canvas

Template data structure matches the workflow `data` field (nodes array + edges array).

### React Block (Monaco Editor Integration)

The ReactBlock is special:
- Only ONE allowed per workflow (enforced in `store.js::addBlock`)
- Frontend always selects React block in editor when it exists (`onSelectionChange` logic)
- User writes JSX code in Monaco editor
- On execution, backend doesn't render React (that's frontend-only)
- Code is persisted in block's `jsx_code` and `css_code` fields

## Common Gotchas

1. **Port Format Confusion**: Backend uses dict format `{key: value}` but frontend ReactFlow needs array format `[{key, value, data_type}]`. Use `normalizePortsToArray()` helper.

2. **MongoDB Nested Updates**: Never do top-level updates on Users collection. Always use `user_service.py` methods which properly handle nested document paths like `projects.$.workflows.$.data`.

3. **Input Constraints**: Each input port can only have ONE incoming edge. Frontend enforces this in `store.js::onConnect()` by filtering out existing edges to the same targetHandle.

4. **Execution from Storage**: The execution endpoint doesn't reconstruct Python Block objects from stored workflow data yet (see `api_routes.py::execute_workflow_by_id`). Current execution flow requires blocks to be in-memory.

5. **CORS Configuration**: Backend uses `CORS_ORIGINS` env var (comma-separated). Defaults to `http://localhost:3000` if not set.

6. **Authentication Headers**: Frontend uses `apiClient` from `services/api.ts` which automatically injects Supabase JWT from AuthContext.

## Environment Variables

**Backend (.env):**
```
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=nodelink
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_JWT_SECRET=your-secret
SUPABASE_SERVICE_KEY=service-role-key
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
DEBUG=False
PORT=5001
HOST=127.0.0.1
```

**Frontend (.env.local):**
```
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=anon-public-key
NEXT_PUBLIC_API_URL=http://localhost:5001
```

## Testing Workflows

1. Ensure backend is running with MongoDB connected
2. Log in via frontend (creates Supabase session)
3. Create project from dashboard
4. Add blocks to canvas from control panel
5. Connect blocks by dragging from output port to input port
6. Configure each block (click settings icon)
7. Click "Run" button in TopBar
8. Watch ExecutionLog panel for streaming updates

## File Organization

**Backend Critical Files:**
- `main.py` - Flask app, execution engine, route registration
- `blocks.py` - Base Block and Connector classes
- `block_types/` - Individual block implementations
- `api_schemas.py` - 23+ API integration definitions
- `auth_middleware.py` - JWT verification decorator
- `user_service.py` - MongoDB CRUD operations
- `database.py` - MongoDB connection singleton
- `api_routes.py` - V2 authenticated REST API
- `ai_routes.py` - AI recommendation endpoints

**Frontend Critical Files:**
- `app/workflow/page.js` - Main workflow editor page
- `components/FlowCanvas.js` - ReactFlow wrapper
- `components/CustomNode.js` - Node rendering logic
- `components/ControlPanel.js` - Block palette sidebar
- `components/ExecutionLog.jsx` - Real-time execution logs
- `components/ReactIDE.js` - Monaco code editor
- `helpers/store.js` - Zustand state store (1180 lines - the brain)
- `services/api.ts` - Axios client with auth injection
- `contexts/AuthContext.tsx` - Supabase auth provider

## Database Indexes

The system creates indexes on:
- `users.supabase_user_id` (unique)
- `users.email` (unique, sparse)

If you add new query patterns, update `database.py::_create_indexes()`.
