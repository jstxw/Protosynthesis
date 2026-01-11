# NodeLink Backend

A Flask-based backend for the NodeLink visual workflow builder with Supabase authentication and MongoDB persistence.

## Architecture

- **Authentication**: Supabase Auth (JWT tokens)
- **Database**: MongoDB Atlas (nested User → Projects → Workflows)
- **API Framework**: Flask with CORS support
- **Language**: Python 3.x

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy and configure the `.env` file:

```bash
# .env is already created, just update these values:

# MongoDB - Get connection string from MongoDB Atlas
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

# Supabase - Get JWT secret from Supabase dashboard
SUPABASE_JWT_SECRET=your-jwt-secret-here
```

**Important:**
- MongoDB URI is already configured ✅
- You need to get the `SUPABASE_JWT_SECRET` from Supabase dashboard

See [SUPABASE_SETUP.md](./SUPABASE_SETUP.md) for detailed instructions on getting your JWT secret.

### 3. Start the Server

```bash
python main.py
```

Server runs on `http://localhost:5001`

You should see:
```
✓ Successfully connected to MongoDB database: nodelink
✓ MongoDB connection established
 * Running on http://0.0.0.0:5001
```

## API Endpoints

### V2 Endpoints (New - Supabase + MongoDB)

All `/api/v2/*` endpoints require JWT authentication.

**User:**
- `POST /api/v2/user/init` - Initialize user in MongoDB after signup
- `GET /api/v2/user/me` - Get current user profile

**Projects:**
- `GET /api/v2/projects` - List all projects
- `POST /api/v2/projects` - Create project
- `GET /api/v2/projects/<id>` - Get project
- `PUT /api/v2/projects/<id>` - Update project
- `DELETE /api/v2/projects/<id>` - Delete project

**Workflows:**
- `GET /api/v2/projects/<id>/workflows` - List workflows
- `POST /api/v2/projects/<id>/workflows` - Create workflow
- `GET /api/v2/projects/<id>/workflows/<id>` - Get workflow
- `PUT /api/v2/projects/<id>/workflows/<id>` - Update workflow
- `DELETE /api/v2/projects/<id>/workflows/<id>` - Delete workflow
- `POST /api/v2/projects/<id>/workflows/<id>/execute` - Execute workflow

### V1 Endpoints (Legacy - In-Memory)

**NOTE:** These endpoints are for backward compatibility and don't use authentication.

- `POST /api/execute` - Execute workflow
- `POST /api/block/add` - Add block
- `POST /api/block/remove` - Remove block
- `POST /api/block/update` - Update block
- `POST /api/connection/add` - Add connection
- `POST /api/connection/remove` - Remove connection
- `GET /api/graph` - Get graph structure
- `POST /api/project/save` - Save project (JSON)
- `POST /api/project/load` - Load project (JSON)

## Data Structure

MongoDB stores user data in a nested format:

```json
{
  "supabase_user_id": "uuid-from-supabase",
  "email": "user@example.com",
  "created_at": "ISO timestamp",
  "projects": [
    {
      "project_id": "uuid",
      "name": "Project Name",
      "created_at": "ISO timestamp",
      "updated_at": "ISO timestamp",
      "workflows": [
        {
          "workflow_id": "uuid",
          "name": "Workflow Name",
          "created_at": "ISO timestamp",
          "updated_at": "ISO timestamp",
          "data": {
            "nodes": [...],
            "edges": [...]
          }
        }
      ]
    }
  ]
}
```

## Project Structure

```
backend/
├── main.py                  # Flask app & legacy endpoints
├── api_routes.py            # New authenticated endpoints (v2)
├── auth_middleware.py       # JWT authentication decorator
├── user_service.py          # User/Project/Workflow business logic
├── database.py              # MongoDB connection handler
├── project.py              # Legacy project model
├── blocks.py               # Block system
├── block_types/            # Different block implementations
├── requirements.txt        # Python dependencies
├── .env                    # Environment configuration
├── README.md              # This file
├── API_DOCUMENTATION.md   # Detailed API docs
├── SUPABASE_SETUP.md      # Supabase configuration guide
└── MONGODB_SETUP.md       # MongoDB configuration guide
```

## Key Components

### Authentication (`auth_middleware.py`)

The `@require_auth` decorator protects routes and provides the current user:

```python
@app.route('/api/v2/projects', methods=['POST'])
@require_auth
def create_project(current_user):
    user_id = current_user['sub']  # Supabase user ID
    email = current_user['email']
    # ... create project
```

### User Service (`user_service.py`)

Handles all database operations:

```python
from user_service import UserService

# Create user
UserService.create_user(supabase_user_id, email)

# Create project
project = UserService.create_project(user_id, "Project Name")

# Create workflow
workflow = UserService.create_workflow(user_id, project_id, "Workflow Name")

# Update workflow
UserService.update_workflow(user_id, project_id, workflow_id, workflow_data)
```

### Database (`database.py`)

Singleton MongoDB connection:

```python
from database import get_collection

users_collection = get_collection('users')
```

## Frontend Integration

### Login and Get Token

```javascript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
);

// Login
const { data } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
});

const token = data.session.access_token;
```

### Make Authenticated Requests

```javascript
// Initialize user (call once after signup)
await fetch('http://localhost:5001/api/v2/user/init', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// Create project
const res = await fetch('http://localhost:5001/api/v2/projects', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ name: 'My Project' })
});

const { project } = await res.json();
```

## Documentation

- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - Complete API reference with examples
- **[SUPABASE_SETUP.md](./SUPABASE_SETUP.md)** - How to configure Supabase JWT
- **[MONGODB_SETUP.md](./MONGODB_SETUP.md)** - MongoDB Atlas setup guide

## Development

### Running in Development Mode

```bash
python main.py
```

The server will run with debug mode enabled.

### Testing Endpoints

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for cURL examples.

### Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python main.py

# Check MongoDB connection
# Look for "✓ Successfully connected to MongoDB" in console
```

## Migration Guide

If you're migrating from the old in-memory system to the new authenticated system:

1. **Frontend Changes:**
   - Add Supabase authentication
   - Update API calls to use `/api/v2/*` endpoints
   - Include JWT token in all requests

2. **Data Migration:**
   - Export old projects using `GET /api/project/save`
   - Import into new structure using `/api/v2/projects` endpoints

3. **Workflow Format:**
   - Old format: `{ "blocks": [...], "connections": [...] }`
   - New format: `{ "nodes": [...], "edges": [...] }`
   - You may need to transform the data structure

## Troubleshooting

### "Invalid token" Error

- Check that `SUPABASE_JWT_SECRET` is correct in `.env`
- Restart the server after updating `.env`
- Verify token isn't expired (default: 1 hour)

### MongoDB Connection Failed

- Check `MONGODB_URI` in `.env`
- Verify IP whitelist in MongoDB Atlas
- Ensure database user has proper permissions

### Import Errors

- Run `pip install -r requirements.txt`
- Check Python version (3.8+ required)

## Production Deployment

### Environment Variables

Set these in your production environment:

```
MONGODB_URI=your-production-mongodb-uri
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
FLASK_ENV=production
```

### Security Checklist

- [ ] Update CORS to allow only your frontend domain
- [ ] Use HTTPS
- [ ] Enable MongoDB authentication
- [ ] Restrict MongoDB network access
- [ ] Set up rate limiting
- [ ] Enable logging and monitoring
- [ ] Use secrets manager for sensitive data

## License

MIT

## Support

For issues or questions, please create an issue in the repository.
