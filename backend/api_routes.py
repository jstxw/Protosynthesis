"""
New API routes following the Supabase + MongoDB architecture.
All routes are protected with JWT authentication.

Structure: User -> Projects -> Workflows
"""
from flask import Blueprint, jsonify, request
from auth_middleware import require_auth
from user_service import UserService

# Create a Blueprint for the new API routes
api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')

# ==========================================
# USER ENDPOINTS
# ==========================================

@api_v2.route('/user/init', methods=['POST'])
@require_auth
def init_user(current_user):
    """
    Initialize user in MongoDB after Supabase signup.
    Call this after a user signs up to create their MongoDB document.
    """
    try:
        print(f"\n🚀 USER INIT ENDPOINT")
        print(f"Current user data: {current_user}")

        user_id = current_user['sub']
        email = current_user.get('email', '')

        print(f"Creating user in MongoDB...")
        print(f"  - User ID: {user_id}")
        print(f"  - Email: {email}")

        user = UserService.create_user(user_id, email)

        print(f"✅ User created successfully!")
        print(f"User document: {user}\n")

        return jsonify({
            "status": "success",
            "message": "User initialized",
            "user": {
                "supabase_user_id": user["supabase_user_id"],
                "email": user["email"]
            }
        }), 201

    except Exception as e:
        print(f"❌ Error creating user: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@api_v2.route('/user/me', methods=['GET'])
@require_auth
def get_current_user(current_user):
    """
    Get current user's profile and all their projects.
    """
    try:
        user_id = current_user['sub']
        user = UserService.get_user(user_id)

        if not user:
            return jsonify({"error": "User not found in database"}), 404

        # Remove MongoDB _id field
        user.pop('_id', None)

        return jsonify(user), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================================
# PROJECT ENDPOINTS
# ==========================================

@api_v2.route('/projects', methods=['GET'])
@require_auth
def list_projects(current_user):
    """
    Get all projects for the authenticated user.
    """
    try:
        user_id = current_user['sub']
        projects = UserService.get_all_projects(user_id)

        return jsonify({"projects": projects}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v2.route('/projects', methods=['POST'])
@require_auth
def create_project(current_user):
    """
    Create a new project.
    Body: { "name": "Project Name" }
    """
    try:
        user_id = current_user['sub']
        data = request.json

        if not data or 'name' not in data:
            return jsonify({"error": "Project name is required"}), 400

        project = UserService.create_project(user_id, data['name'])

        return jsonify({
            "status": "success",
            "message": "Project created",
            "project": project
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v2.route('/projects/<project_id>', methods=['GET'])
@require_auth
def get_project(current_user, project_id):
    """
    Get a specific project by ID.
    """
    try:
        user_id = current_user['sub']
        project = UserService.get_project(user_id, project_id)

        if not project:
            return jsonify({"error": "Project not found"}), 404

        return jsonify(project), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v2.route('/projects/<project_id>', methods=['PUT'])
@require_auth
def update_project(current_user, project_id):
    """
    Update project metadata (name).
    Body: { "name": "New Name" }
    """
    try:
        user_id = current_user['sub']
        data = request.json

        if not data:
            return jsonify({"error": "No update data provided"}), 400

        success = UserService.update_project(user_id, project_id, data)

        if not success:
            return jsonify({"error": "Project not found or update failed"}), 404

        return jsonify({
            "status": "success",
            "message": "Project updated"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v2.route('/projects/<project_id>', methods=['DELETE'])
@require_auth
def delete_project(current_user, project_id):
    """
    Delete a project and all its workflows.
    """
    try:
        user_id = current_user['sub']
        success = UserService.delete_project(user_id, project_id)

        if not success:
            return jsonify({"error": "Project not found"}), 404

        return jsonify({
            "status": "success",
            "message": "Project deleted"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================================
# WORKFLOW ENDPOINTS
# ==========================================

@api_v2.route('/projects/<project_id>/workflows', methods=['GET'])
@require_auth
def list_workflows(current_user, project_id):
    """
    Get all workflows for a project.
    """
    try:
        user_id = current_user['sub']
        workflows = UserService.get_all_workflows(user_id, project_id)

        return jsonify({"workflows": workflows}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v2.route('/projects/<project_id>/workflows', methods=['POST'])
@require_auth
def create_workflow(current_user, project_id):
    """
    Create a new workflow in a project.
    Body: { "name": "Workflow Name", "data": { ... } }
    """
    try:
        user_id = current_user['sub']
        data = request.json

        if not data or 'name' not in data:
            return jsonify({"error": "Workflow name is required"}), 400

        workflow_data = data.get('data', {"nodes": [], "edges": []})
        workflow = UserService.create_workflow(
            user_id,
            project_id,
            data['name'],
            workflow_data
        )

        return jsonify({
            "status": "success",
            "message": "Workflow created",
            "workflow": workflow
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v2.route('/projects/<project_id>/workflows/<workflow_id>', methods=['GET'])
@require_auth
def get_workflow(current_user, project_id, workflow_id):
    """
    Get a specific workflow by ID.
    """
    try:
        user_id = current_user['sub']
        workflow = UserService.get_workflow(user_id, project_id, workflow_id)

        if not workflow:
            return jsonify({"error": "Workflow not found"}), 404

        return jsonify(workflow), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v2.route('/projects/<project_id>/workflows/<workflow_id>', methods=['PUT'])
@require_auth
def update_workflow(current_user, project_id, workflow_id):
    """
    Update workflow data (nodes, edges, config).
    Body: { "data": { "nodes": [...], "edges": [...] } }
    Or update name: { "name": "New Name" }
    """
    try:
        user_id = current_user['sub']
        data = request.json

        if not data:
            return jsonify({"error": "No update data provided"}), 400

        # Check if updating data or metadata
        if 'data' in data:
            success = UserService.update_workflow(
                user_id,
                project_id,
                workflow_id,
                data['data']
            )
        elif 'name' in data:
            success = UserService.update_workflow_metadata(
                user_id,
                project_id,
                workflow_id,
                data['name']
            )
        else:
            return jsonify({"error": "Must provide 'data' or 'name' field"}), 400

        if not success:
            return jsonify({"error": "Workflow not found or update failed"}), 404

        return jsonify({
            "status": "success",
            "message": "Workflow updated"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_v2.route('/projects/<project_id>/workflows/<workflow_id>', methods=['DELETE'])
@require_auth
def delete_workflow(current_user, project_id, workflow_id):
    """
    Delete a workflow from a project.
    """
    try:
        user_id = current_user['sub']
        success = UserService.delete_workflow(user_id, project_id, workflow_id)

        if not success:
            return jsonify({"error": "Workflow not found"}), 404

        return jsonify({
            "status": "success",
            "message": "Workflow deleted"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================================
# WORKFLOW EXECUTION ENDPOINT
# ==========================================

@api_v2.route('/projects/<project_id>/workflows/<workflow_id>/execute', methods=['POST'])
@require_auth
def execute_workflow(current_user, project_id, workflow_id):
    """
    Execute a workflow (integrate with existing execution engine).
    This will load the workflow data and run it through the execution engine.
    """
    try:
        user_id = current_user['sub']
        workflow = UserService.get_workflow(user_id, project_id, workflow_id)

        if not workflow:
            return jsonify({"error": "Workflow not found"}), 404

        # TODO: Integrate with existing execution engine
        # For now, return the workflow data
        return jsonify({
            "status": "execution_started",
            "workflow_id": workflow_id,
            "message": "Execution engine integration coming soon",
            "workflow_data": workflow.get('data', {})
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
