from flask import Blueprint, request, jsonify
from auth_middleware import require_auth
from project import Project
import logging

logger = logging.getLogger(__name__)

api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')

@api_v2.route('/projects', methods=['POST'])
@require_auth
def create_project(current_user):
    """Creates a new project associated with the authenticated user."""
    try:
        user_id = current_user.get('sub')
        if not user_id:
            return jsonify({"error": "User ID not found in token"}), 401

        data = request.json
        project_name = data.get("name", "New Project")
        
        from user_service import UserService
        project = UserService.create_project(user_id, project_name)

        logger.info(f"User '{user_id}' created project '{project_name}' ({project.get('project_id')})")

        return jsonify({
            "status": "created",
            "project_id": str(project.get('project_id')),
            "project_name": project.get('name')
        }), 201

    except Exception as e:
        # Check if user_id is defined before using it in logger
        uid = current_user.get('sub') if 'current_user' in locals() else 'unknown'
        logger.error(f"Error creating project for user '{uid}': {e}", exc_info=True)
        return jsonify({"error": "Failed to create project on server"}), 500

@api_v2.route('/projects', methods=['GET'])
@require_auth
def get_projects(current_user):
    """Lists all projects for the authenticated user."""
    try:
        user_id = current_user.get('sub')
        from user_service import UserService
        projects = UserService.get_all_projects(user_id)

        # Transform for frontend if needed, or return as is
        # UserService returns list of project dicts

        return jsonify({"projects": projects}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to list projects: {str(e)}"}), 500

@api_v2.route('/projects/<project_id>/workflows', methods=['POST'])
@require_auth
def create_workflow(current_user, project_id):
    """Creates a new workflow within a project."""
    try:
        user_id = current_user.get('sub')
        data = request.json
        workflow_name = data.get("name", "New Workflow")

        from user_service import UserService
        workflow = UserService.create_workflow(user_id, project_id, workflow_name)

        return jsonify({
            "status": "created",
            "workflow_id": workflow.get('workflow_id'),
            "workflow": workflow
        }), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        logger.error(f"Error creating workflow: {e}", exc_info=True)
        return jsonify({"error": "Failed to create workflow"}), 500

@api_v2.route('/projects/<project_id>/workflows', methods=['GET'])
@require_auth
def list_workflows(current_user, project_id):
    """Lists all workflows in a project."""
    try:
        user_id = current_user.get('sub')
        from user_service import UserService
        workflows = UserService.get_all_workflows(user_id, project_id)
        return jsonify(workflows), 200
    except Exception as e:
        logger.error(f"Error listing workflows: {e}", exc_info=True)
        return jsonify({"error": "Failed to list workflows"}), 500

@api_v2.route('/projects/<project_id>/workflows/<workflow_id>', methods=['GET'])
@require_auth
def get_workflow(current_user, project_id, workflow_id):
    """Gets a specific workflow."""
    try:
        user_id = current_user.get('sub')
        from user_service import UserService
        workflow = UserService.get_workflow(user_id, project_id, workflow_id)

        if not workflow:
            return jsonify({"error": "Workflow not found"}), 404

        return jsonify(workflow), 200
    except Exception as e:
        logger.error(f"Error getting workflow: {e}", exc_info=True)
        return jsonify({"error": "Failed to get workflow"}), 500

@api_v2.route('/projects/<project_id>/workflows/<workflow_id>', methods=['PUT'])
@require_auth
def update_workflow(current_user, project_id, workflow_id):
    """Updates a workflow's data (nodes, edges)."""
    try:
        user_id = current_user.get('sub')
        data = request.json
        workflow_data = data.get("data") # Expects { nodes: [], edges: [] }

        if workflow_data is None:
             return jsonify({"error": "Missing 'data' field"}), 400

        from user_service import UserService
        success = UserService.update_workflow(user_id, project_id, workflow_id, workflow_data)

        if success:
            return jsonify({"status": "updated"}), 200
        else:
            return jsonify({"error": "Workflow not found or update failed"}), 404
    except Exception as e:
        logger.error(f"Error updating workflow: {e}", exc_info=True)
        return jsonify({"error": "Failed to update workflow"}), 500

@api_v2.route('/projects/<project_id>/workflows/<workflow_id>', methods=['DELETE'])
@require_auth
def delete_workflow(current_user, project_id, workflow_id):
    """Deletes a workflow."""
    try:
        user_id = current_user.get('sub')
        from user_service import UserService
        success = UserService.delete_workflow(user_id, project_id, workflow_id)

        if success:
            return jsonify({"status": "deleted"}), 200
        else:
            return jsonify({"error": "Workflow not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting workflow: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete workflow"}), 500
