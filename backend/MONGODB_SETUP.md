# MongoDB Setup Guide

This guide will help you connect your NodeLink backend to MongoDB Atlas.

## Step 1: Create a MongoDB Atlas Account

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up for a free account
3. Create a new cluster (select the free tier)

## Step 2: Get Your Connection String

1. In MongoDB Atlas, click "Connect" on your cluster
2. Choose "Connect your application"
3. Select "Python" as the driver and version 3.12 or later
4. Copy the connection string (it looks like: `mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/`)

## Step 3: Configure Your Environment

1. Open the `.env` file in the `backend` directory
2. Replace the placeholder MongoDB URI with your actual connection string:

```
MONGODB_URI=mongodb+srv://your-username:your-password@your-cluster.mongodb.net/nodelink?retryWrites=true&w=majority
MONGODB_DB_NAME=nodelink
```

**Important:** Replace the following in your connection string:
- `<username>` - Your MongoDB database username
- `<password>` - Your MongoDB database password
- `<cluster>` - Your cluster address (e.g., cluster0.abc123.mongodb.net)

## Step 4: Install Dependencies

```bash
cd /Users/jstwx07/Desktop/projects/NodeLink_2/deltahacks-12/backend
pip install -r requirements.txt
```

## Step 5: Start the Server

```bash
python main.py
```

You should see a message: "✓ Successfully connected to MongoDB database: nodelink"

## API Endpoints for MongoDB

### Save Current Project to Database
```
POST /api/project/db/save
```

### Load Project from Database
```
GET /api/project/db/load/<project_id>
```

### List All Projects
```
GET /api/project/db/list
```

### Create New Project
```
POST /api/project/db/create
Body: { "name": "My Project" }
```

### Delete Project
```
DELETE /api/project/db/delete/<project_id>
```

## Testing the Connection

You can test the MongoDB connection by making a request to create a new project:

```bash
curl -X POST http://localhost:5001/api/project/db/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project"}'
```

## Troubleshooting

### Connection Issues

1. **Network Access**: Make sure your IP address is whitelisted in MongoDB Atlas
   - Go to Network Access in Atlas
   - Click "Add IP Address"
   - Add your current IP or use `0.0.0.0/0` for testing (not recommended for production)

2. **Database User**: Make sure you created a database user in Atlas
   - Go to Database Access
   - Add a new database user with read/write permissions

3. **Connection String**: Double-check your connection string format
   - Make sure you replaced `<username>` and `<password>`
   - Password should be URL-encoded if it contains special characters

### Still Running in In-Memory Mode?

If you see "Running in in-memory mode only" when starting the server:
- Check your `.env` file exists in the backend directory
- Verify the `MONGODB_URI` is set correctly
- Check the console for specific error messages

## Security Notes

- Never commit your `.env` file to git (it's already in `.gitignore`)
- Use strong passwords for your MongoDB users
- In production, restrict network access to specific IP addresses
- Consider using MongoDB's IP whitelist feature
