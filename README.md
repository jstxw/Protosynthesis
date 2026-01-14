# Protosynthesis

<div align="center">

**Visual API Workflow Automation Platform**

A powerful no-code platform for building, designing, and executing complex API workflows through an intuitive drag-and-drop interface.

</div>

---

![Screenshot 0](Protosynthesis/media/image_0.png)

![Screenshot 1](Protosynthesis/media/image_1.png)

![Screenshot 2](Protosynthesis/media/image_2.png)

## Overview

**Protosynthesis** is a full-stack visual workflow builder that enables users to create sophisticated API automation pipelines without writing code. Connect 23+ services (Stripe, Slack, OpenAI, MongoDB, Google Sheets, and more) through an interactive node-based interface with real-time execution feedback and AI-powered recommendations.

### Key Capabilities

- **Visual Workflow Design**: Drag-and-drop node editor powered by ReactFlow
- **Real-Time Execution**: Stream execution progress with WebSocket-based updates
- **23+ API Integrations**: Pre-configured blocks for popular services
- **AI Assistant**: Intelligent recommendations for workflow optimization
- **Code Editor**: Embedded Monaco editor for custom React components
- **Template Library**: 8 pre-built workflows for common use cases
- **Secure Authentication**: Supabase-powered JWT authentication
- **Cloud Storage**: MongoDB Atlas for workflow persistence

---

## Features

### Workflow Editor
- **Interactive Canvas**: Build workflows by connecting blocks with visual edges
- **Custom Nodes**: 11+ specialized block types (API, Transform, Logic, React UI, etc.)
- **Port-Based Connections**: Type-safe input/output port system
- **Execution Visualization**: Real-time status updates for each block
- **Auto-Save**: Automatic workflow persistence to cloud

### Execution Engine
- **Topological Sort**: Intelligent dependency resolution with DAG validation
- **Streaming Updates**: Real-time progress events via WebSocket
- **Error Handling**: Block-level exception catching with detailed logs
- **Data Flow**: Automatic input resolution from upstream outputs

### AI Integration
- **Node Recommendations**: AI-powered suggestions for next workflow steps
- **Connection Validation**: Smart compatibility checking between blocks
- **Conversational Assistant**: Gemini AI for workflow guidance

### Developer Features
- **React IDE**: In-browser code editor with syntax highlighting
- **API Schema Library**: 23+ pre-configured API definitions
- **Template System**: Quick-start templates for common patterns
- **Export/Import**: Save and share workflow configurations

---

## Tech Stack

### Frontend
```
Framework:       Next.js 16.1.1 + React 19.2.3 + TypeScript
State:           Zustand 5.0.9 (with immer middleware)
Visualization:   ReactFlow 11.11.4
Code Editor:     Monaco Editor 4.7.0
Styling:         Tailwind CSS 4.0
HTTP Client:     Axios 1.13.2
Authentication:  Supabase 2.90.1
Icons:           Lucide React 0.562.0
```

### Backend
```
Framework:       Flask 3.0.0 (Python)
Real-Time:       Flask-SocketIO 5.3.5
Database:        MongoDB Atlas (pymongo)
Authentication:  JWT (ES256/HS256 via Supabase)
HTTP Client:     Requests 2.31.0
CORS:            Flask-CORS 4.0.0
AI Services:     Moorcheh AI, Google Gemini
WebSocket:       Python-socketio 5.10.0 + Python-engineio 4.8.0
```

### Architecture
```
┌──────────────────────────────────────────┐
│   Frontend (Next.js/React/TypeScript)    │
│   • ReactFlow Canvas                     │
│   • Zustand State Store                  │
│   • Monaco Code Editor                   │
│   • Real-time Execution Logs             │
└────────────┬─────────────────────────────┘
             │ HTTP/WebSocket (JWT Auth)
┌────────────▼─────────────────────────────┐
│      Backend (Flask/Python)              │
│   • RESTful API Routes                   │
│   • Topological Sort Execution Engine    │
│   • Block Factory Pattern                │
│   • JWT Authentication Middleware        │
└────────────┬─────────────────────────────┘
             │ Authenticated Queries
┌────────────▼─────────────────────────────┐
│      Data Layer (MongoDB Atlas)          │
│   • Users Collection                     │
│   • Projects (nested workflows)          │
│   • Nodes & Edges Storage                │
└──────────────────────────────────────────┘
```

---

## Getting Started

### Prerequisites

- **Node.js** 18+ and npm/yarn
- **Python** 3.8+
- **MongoDB Atlas** account (free tier available)
- **Supabase** account for authentication
- API keys for desired integrations (Stripe, OpenAI, etc.)

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/protosynthesis.git
cd protosynthesis
```

#### 2. Frontend Setup
```bash
cd frontend
npm install

# Create .env.local file
cat > .env.local << EOF
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:5000
EOF

# Start development server
npm run dev
```

#### 3. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
MONGODB_URI=your_mongodb_connection_string
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key
SUPABASE_JWT_SECRET=your_jwt_secret
FLASK_SECRET_KEY=your_flask_secret_key
AI_SERVICE_API_KEY=your_ai_service_key
EOF

# Start Flask server
python main.py
```

#### 4. Access the Application
```
Frontend: http://localhost:3000
Backend:  http://localhost:5000
```

### Quick Start

1. **Sign Up**: Create an account at `/signup`
2. **Create Project**: Navigate to `/dashboard` and create a new project
3. **Build Workflow**:
   - Drag blocks from the left control panel onto the canvas
   - Connect blocks by dragging from output ports to input ports
   - Configure each block by clicking the settings icon
4. **Execute**: Click the "Run" button to execute your workflow
5. **View Results**: Check the execution log panel for real-time updates

---

## API Integrations

### 23+ Pre-Configured Services

#### Payments
- **Stripe** - Payment processing, invoices, subscriptions
- **PayPal** - Alternative payment gateway

#### Communication
- **Slack** - Webhook notifications and messaging
- **Discord** - Server webhooks and bot integration
- **Twilio** - SMS and voice messaging
- **Telegram Bot** - Automated bot responses

#### AI Services
- **OpenAI** - GPT models for text generation
- **Anthropic Claude** - Advanced language model
- **Google Gemini** - Multimodal AI capabilities
- **Hugging Face** - ML model inference
- **Stability AI** - Image generation (DALL-E alternative)
- **ElevenLabs** - Text-to-speech synthesis

#### Databases & Storage
- **MongoDB Atlas** - NoSQL document database
- **Airtable** - Spreadsheet-database hybrid
- **Google Sheets** - Spreadsheet automation

#### Productivity
- **Notion API** - Knowledge base integration
- **Todoist** - Task management
- **Google Calendar** - Event scheduling

#### Utilities
- **Google Maps** - Geocoding and location services
- **Custom API** - Generic HTTP request builder
- **Data APIs** - Cat Facts, Agify.io, and more

---

## Block Types

### Core Blocks

| Block Type | Description | Use Case |
|------------|-------------|----------|
| **StartBlock** | Workflow entry point | Initialize workflow execution |
| **APIBlock** | HTTP request executor | Call external APIs with custom config |
| **ReactBlock** | UI component renderer | Display React components in browser |
| **TransformBlock** | Data manipulation | JSON parsing, key extraction, formatting |
| **LogicBlock** | Arithmetic/boolean ops | Calculations, conditionals, comparisons |
| **StringBuilderBlock** | Template engine | Build strings from dynamic inputs |
| **WaitBlock** | Delay execution | Add pauses between operations |
| **DialogueBlock** | User messages | Display notifications or prompts |
| **ApiKeyBlock** | Credential manager | Securely store API keys |

---

## Project Structure

```
Protosynthesis/
├── frontend/
│   ├── app/
│   │   ├── dashboard/              # Project management UI
│   │   ├── workflow/               # Visual workflow editor
│   │   ├── login/                  # Authentication pages
│   │   ├── signup/
│   │   └── layout.js               # Root layout with providers
│   ├── components/
│   │   ├── FlowCanvas.js           # ReactFlow editor wrapper
│   │   ├── ControlPanel.js         # Block palette sidebar
│   │   ├── CustomNode.js           # Node rendering logic
│   │   ├── ReactIDE.js             # Monaco code editor
│   │   ├── ExecutionLog.jsx        # Real-time execution logs
│   │   ├── TopBar.js               # Navigation controls
│   │   └── Assistant/              # AI recommendation panel
│   ├── services/
│   │   ├── projects.ts             # Project/workflow API client
│   │   └── api.ts                  # Axios instance configuration
│   ├── helpers/
│   │   └── store.js                # Zustand state management
│   ├── contexts/
│   │   └── AuthContext.tsx         # Authentication context
│   └── package.json
│
├── backend/
│   ├── main.py                     # Flask app + execution engine
│   ├── blocks.py                   # Base block abstract class
│   ├── project.py                  # Project data model
│   ├── user_service.py             # CRUD operations for users/projects
│   ├── auth_middleware.py          # JWT verification decorator
│   ├── api_routes.py               # RESTful API v2 endpoints
│   ├── ai_routes.py                # AI recommendation endpoints
│   ├── api_schemas.py              # 23 API integration definitions
│   ├── database.py                 # MongoDB singleton connection
│   ├── block_types/                # Block implementations
│   │   ├── api_block.py
│   │   ├── react_block.py
│   │   ├── transform_block.py
│   │   ├── logic_block.py
│   │   ├── wait_block.py
│   │   ├── dialogue_block.py
│   │   ├── api_key_block.py
│   │   ├── string_builder_block.py
│   │   └── start_block.py
│   ├── routes/
│   │   └── agent_routes.py         # Gemini AI conversational agent
│   ├── services/
│   │   └── integrations/
│   │       └── ai_service.py       # Moorcheh AI client
│   └── requirements.txt
│
├── TEMPLATES_GUIDE.md              # Pre-built workflow templates
├── .gitignore
└── README.md
```

---

## Workflow Templates

### 8 Ready-to-Use Templates

1. **AI Content Generator**
   - Claude AI → Slack + Display
   - Generate content with AI and distribute

2. **Payment → Notification**
   - Stripe → Slack + Discord
   - Alert teams on successful payments

3. **AI Assistant via SMS**
   - Telegram → Gemini → Twilio SMS → Display
   - Conversational AI responding to text messages

4. **Task Automation Hub**
   - Todoist → Google Calendar → Discord
   - Sync tasks across productivity tools

5. **Data Collection Pipeline**
   - Cat Fact API → MongoDB → Hugging Face → Google Sheets
   - Collect, process, and store data

6. **AI Image Generator**
   - Stability AI → Slack + Display
   - Text-to-image generation workflow

7. **Voice Content Creator**
   - OpenAI → ElevenLabs TTS → Slack
   - Convert text to speech with AI

8. **Multi-Payment Processor**
   - Stripe + PayPal → Airtable → Slack + Notion
   - Process payments from multiple sources

</div>
