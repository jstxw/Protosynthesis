# Protosynthesis — Project Presentation

---

## 1. Summary

**Protosynthesis** is a full-stack, no-code visual API workflow automation platform. Users drag-and-drop blocks onto an interactive canvas, connect them with wires, and execute complex multi-step API pipelines — all without writing a single line of code.

The platform connects **23+ real-world services** (Stripe, Slack, OpenAI, Discord, Twilio, MongoDB, Google Sheets, and more) and provides **real-time streaming execution feedback**, an **AI assistant** for workflow recommendations, and a built-in **React IDE** for custom UI components.

**Tech Stack:**
- **Frontend:** Next.js 16, React 19, TypeScript, ReactFlow, Zustand, Monaco Editor, Supabase Auth
- **Backend:** Flask (Python), JWT Authentication, Flask-SocketIO
- **Data:** MongoDB Atlas, Supabase Auth
- **AI:** Moorcheh AI (RAG), Google Gemini (conversational agent)

---

## 2. Motivation

Building API integrations is tedious. Developers spend hours reading docs, writing boilerplate HTTP requests, handling auth headers, parsing JSON responses, and chaining outputs between services. Non-technical users are completely locked out.

**Protosynthesis eliminates this friction:**
- **Visual workflow design** replaces manual coding — no cURL, no Postman, no scripts
- **Pre-configured schemas** for 23+ APIs mean users don't need to read API docs
- **Drag-and-drop** lets non-technical users build automations like "When Stripe payment succeeds → notify Slack → log to Google Sheets"
- **AI recommendations** suggest the next best block to add, reducing decision fatigue
- **Real-time execution streaming** gives instant visibility into what's happening at each step

The goal: **democratize API automation** and make it feel as intuitive as building a flowchart.

---

## 3. Demo Flow

A typical user session looks like this:

1. **Sign Up / Login** → Supabase handles authentication, JWT token issued
2. **Dashboard** → Create a new project or open an existing one
3. **Workflow Editor** → The core experience:
   - Drag a **Start Block** from the left panel onto the canvas
   - Add an **API Block**, select "OpenAI Chat" from the schema dropdown
   - Configure the prompt input (e.g., "Generate a marketing tagline")
   - Add a **Slack Block**, connect OpenAI's output → Slack's message input
   - Add a **Google Sheets Block** to log the result
4. **Test Individual Blocks** → Click "Test" on the API block to verify the response
5. **Execute Workflow** → Click "Run" — watch blocks light up sequentially as they execute
6. **Execution Log** → Real-time streaming output shows each block's inputs/outputs
7. **Save** → Auto-saved to MongoDB Atlas, accessible from any device

---

## 4. Deep Dive: The Execution Engine

### Feature Overview

The **execution engine** is the heart of Protosynthesis. When a user clicks "Run," the backend must take a visual graph of connected blocks and execute them in the correct order, streaming real-time progress back to the frontend.

This is a non-trivial problem: blocks have data dependencies (Block B needs Block A's output), the graph can branch and merge, and execution must handle errors gracefully without crashing the entire pipeline.

### Where the Code Lives

| Component | File | Lines |
|-----------|------|-------|
| **Execution orchestrator** | `backend/main.py` → `execute_graph()` | L126–243 |
| **Variable resolution** | `backend/main.py` → `resolve_variables()` | L72–123 |
| **Workflow endpoint** | `backend/main.py` → `execute_workflow()` | L257–353 |
| **Block reconstruction** | `backend/main.py` → `execute_workflow()` | L280–340 |
| **Base Block class** | `backend/blocks.py` → `Block` (ABC) | L23–169 |
| **Connector (data pipes)** | `backend/blocks.py` → `Connector` | L6–21 |
| **Frontend trigger** | `frontend/helpers/store.js` → `executeWorkflowV2()` | L930–1045 |

### How It Works

The execution engine uses a **3-phase approach**:

#### Phase 1: BFS Discovery
Starting from all `StartBlock` nodes, the engine performs a **Breadth-First Search** to discover every reachable block in the graph. This ensures isolated/disconnected blocks are ignored.

```python
reachable_blocks = set()
queue = collections.deque(start_blocks)
while queue:
    block = queue.popleft()
    if block in reachable_blocks:
        continue
    reachable_blocks.add(block)
    for connectors in block.output_connectors.values():
        for connector in connectors:
            queue.append(connector.target_block)
```

#### Phase 2: Topological Sort (Dependency Resolution)
The engine builds an **in-degree map** — counting how many upstream dependencies each block has. Blocks with 0 dependencies go first (they're "ready"). As each block completes, the engine decrements its downstream neighbors' in-degree counts. When a neighbor hits 0, it becomes ready.

This is **Kahn's algorithm** for topological sorting on a directed acyclic graph (DAG).

```python
in_degree = {b.id: 0 for b in reachable_blocks}
for block in reachable_blocks:
    for connectors in block.output_connectors.values():
        for connector in connectors:
            if connector.target_block.id in block_map:
                in_degree[connector.target_block.id] += 1

ready_queue = deque([b_id for b_id, deg in in_degree.items() if deg == 0])
```

#### Phase 3: Streaming Execution
As each block executes, the engine:
1. **Fetches inputs** from upstream blocks via `Connector.transfer()`
2. **Resolves template variables** (`{{NodeName.field}}` → actual value)
3. **Executes the block** (e.g., makes an HTTP request for an API block)
4. **Yields a JSON event** via Server-Sent Events (SSE) back to the frontend

The frontend parses these SSE events and **animates each node in real-time** — blocks light up green on success, red on failure.

```python
yield json.dumps({
    "type": "progress",
    "block_id": current_block.id,
    "name": current_block.name,
    "outputs": current_block.outputs,
}) + "\n"
```

### The Challenge: Variable Resolution Across the Graph

The hardest part was **template variable substitution**. Users can reference any upstream block's output inside any downstream block's input — for example, typing `{{OpenAI Chat API.response}}` inside a Slack message body.

The challenge:
- Variables can reference blocks by **ID** or by **human-readable name** (which may contain spaces and hyphens)
- Variables can be nested inside **JSON strings, arrays, or deeply nested objects**
- Resolution must happen **after** inputs are fetched but **before** the block executes
- The context must grow incrementally — each block's outputs become available for the next block

The solution was a **recursive resolver** (`resolve_variables()`) that walks any data structure (string, dict, list) and replaces `{{identifier.field}}` patterns using a dual-index context (`by_id` and `by_name`):

```python
execution_context = {
    'by_id': {},    # node_id → outputs
    'by_name': {}   # node_name → outputs
}

# After each block executes:
execution_context['by_id'][block.id] = outputs
execution_context['by_name'][block.name] = outputs
```

This allows users to write intuitive references like `{{Stripe Payment.amount}}` instead of cryptic UUIDs.

---

## 5. Impact

### What Makes This Project Significant

- **23+ API integrations** with pre-built schemas — users connect services in minutes, not hours
- **Real-time streaming execution** — unlike batch tools, users see every step as it happens
- **AI-powered workflow building** — Moorcheh RAG provides intelligent next-step suggestions
- **Full persistence layer** — multi-user support with JWT-authenticated CRUD via MongoDB
- **Production-grade architecture** — clean separation of concerns across 3 layers (presentation, business logic, data)

### Architecture Highlights

| Metric | Value |
|--------|-------|
| Frontend components | 12+ interactive components |
| Backend routes | 15+ authenticated API endpoints |
| Block types | 11 specialized block implementations |
| API integrations | 23+ pre-configured services |
| State management | 1,459-line Zustand store with auto-save |
| Execution model | BFS + Kahn's topological sort + SSE streaming |
| Auth model | Supabase JWT (ES256 / HS256 dual support) |
| Workflow templates | 8 ready-to-use templates |

### Key Files Reference

| Layer | File | Purpose |
|-------|------|---------|
| **Frontend** | `frontend/components/FlowCanvas.js` | ReactFlow canvas + drag-drop |
| **Frontend** | `frontend/components/CustomNode.js` | Block rendering + port system |
| **Frontend** | `frontend/components/ControlPanel.js` | Block palette sidebar |
| **Frontend** | `frontend/components/ReactIDE.js` | In-browser Monaco code editor |
| **Frontend** | `frontend/helpers/store.js` | Zustand state (nodes, edges, execution) |
| **Frontend** | `frontend/contexts/AuthContext.tsx` | Supabase auth management |
| **Backend** | `backend/main.py` | Execution engine + Flask app |
| **Backend** | `backend/blocks.py` | Abstract Block base class |
| **Backend** | `backend/block_types/api_block.py` | API call execution logic |
| **Backend** | `backend/api_routes.py` | RESTful v2 API endpoints |
| **Backend** | `backend/api_schemas.py` | 23+ API integration definitions |
| **Backend** | `backend/auth_middleware.py` | JWT verification middleware |
| **Backend** | `backend/user_service.py` | User/project/workflow CRUD |
| **Backend** | `backend/services/integrations/ai_service.py` | AI recommendation service |
