# API Node Editor

A visual node-based editor for connecting APIs together, inspired by Blender's shader nodes. Build complex API workflows by dragging, dropping, and connecting blocks.

## Features

- **Visual Node Editor**: Drag-and-drop interface for creating API workflows
- **Multiple Block Types**:
  - **Start/End**: Flow control blocks
  - **API Block**: Make HTTP requests (GET, POST, PUT, PATCH, DELETE)
  - **Transformer**: Transform data between blocks (JSON, string manipulation, field extraction)
  - **Merge**: Combine multiple inputs into one output
  - **Conditional**: Branch based on conditions
  - **React Bridge**: Send/receive data to React frontend with live updates
  - **Variable**: Store and retrieve values
  - **Loop**: Iterate over arrays

- **Execution Modes**: Choose between DFS (Depth-First) or BFS (Breadth-First) execution
- **Live Updates**: WebSocket-based real-time updates during execution
- **React Integration**: Special blocks for sending API outputs to React components

## Architecture

The backend is fully implemented with a clean separation between the block system core and the Flask REST API.

```
backend/
├── blocks.py        # ✅ Block system (nodes, ports, connections, executor)
├── main.py          # ✅ Flask app with REST API and WebSocket handlers
├── example.py       # ✅ Example usage and demonstrations
├── requirements.txt # ✅ Python dependencies
└── README.md        # ✅ Backend documentation

frontend/
├── src/
│   ├── components/
│   │   ├── NodeEditor.tsx         # Main visual editor
│   │   ├── BlockPalette.tsx       # Block selection panel
│   │   ├── BlockConfigPanel.tsx   # Block configuration
│   │   ├── ExecutionPanel.tsx     # Execution controls
│   │   ├── ReactIntegrationPanel.tsx # React variable viewer
│   │   └── nodes/
│   │       └── CustomNode.tsx     # Custom node component
│   ├── services/
│   │   └── api.ts                 # API and WebSocket service
│   ├── store/
│   │   └── useStore.ts            # Zustand state management
│   └── App.tsx
└── package.json
```

## Getting Started

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

The server will start at `http://localhost:5000`

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

The frontend will start at `http://localhost:3000`

## API Endpoints

### Graph Management
- `GET /api/graphs` - List all graphs
- `POST /api/graphs/<graph_id>` - Create a graph
- `GET /api/graphs/<graph_id>` - Get graph details
- `DELETE /api/graphs/<graph_id>` - Delete a graph

### Block Management
- `GET /api/graphs/<graph_id>/blocks` - List blocks
- `POST /api/graphs/<graph_id>/blocks` - Add a block
- `PUT /api/graphs/<graph_id>/blocks/<block_id>` - Update a block
- `DELETE /api/graphs/<graph_id>/blocks/<block_id>` - Delete a block

### Connections
- `GET /api/graphs/<graph_id>/connections` - List connections
- `POST /api/graphs/<graph_id>/connections` - Create a connection
- `DELETE /api/graphs/<graph_id>/connections/<connection_id>` - Delete a connection

### Execution
- `POST /api/graphs/<graph_id>/execute` - Execute the graph
  - Body: `{ "mode": "dfs" | "bfs", "inputs": {...} }`

### React Integration
- `GET /api/graphs/<graph_id>/react/outputs` - Get React block outputs
- `POST /api/graphs/<graph_id>/react/input` - Send input to a React block

## WebSocket Events

### Client → Server
- `join_graph` - Join a graph room for updates
- `leave_graph` - Leave a graph room
- `execute_graph` - Execute graph with live updates
- `react_input` - Send input from React to a block

### Server → Client
- `execution_progress` - Progress update during execution
- `execution_complete` - Execution completed
- `execution_error` - Execution error
- `react_update` - React variable updated
- `block_added/updated/deleted` - Block changes
- `connection_added/deleted` - Connection changes

## Usage Example

### Creating a Simple API Chain

1. Add a **Start** block
2. Add an **API Block** and configure:
   - URL: `https://jsonplaceholder.typicode.com/posts/1`
   - Method: `GET`
3. Add a **Transformer** block:
   - Type: `extract_field`
   - Code: `title`
4. Add a **React Bridge** block:
   - Variable name: `postTitle`
5. Add an **End** block
6. Connect: Start → API → Transformer → React Bridge → End
7. Click **Execute Graph**

The post title will be available in your React components via `useReactOutput('postTitle')`.

### Using React Outputs in Components

```tsx
import { useReactOutput, useSendReactInput } from './components/ReactIntegrationPanel';

function MyComponent() {
  const postTitle = useReactOutput('postTitle');
  const sendInput = useSendReactInput();
  
  return (
    <div>
      <h1>{postTitle || 'Loading...'}</h1>
      <button onClick={() => sendInput('block-id', 'new value')}>
        Send Input
      </button>
    </div>
  );
}
```

## Block Configuration

### API Block
- **url**: The API endpoint URL
- **method**: HTTP method (GET, POST, PUT, PATCH, DELETE)
- **headers**: HTTP headers as JSON object
- **auth_type**: Authentication type (none, bearer, basic, api_key)

### Transformer Block
- **transform_type**: Type of transformation
  - `custom`: Python expression with `input` variable
  - `to_json`: Convert to JSON string
  - `from_json`: Parse JSON string
  - `to_string`: Convert to string
  - `extract_field`: Extract nested field (e.g., `data.items[0].name`)
  - `template`: Template string with `{input}` placeholder
- **transform_code**: Code/expression for the transformation

### Merge Block
- **merge_type**: How to merge inputs
  - `object`: Merge dictionaries
  - `array`: Collect into array
  - `concat`: Concatenate as strings

### Conditional Block
- **condition_type**: Condition to evaluate
  - `equals`, `not_equals`, `greater_than`, `less_than`, `contains`, `truthy`

## License

MIT

