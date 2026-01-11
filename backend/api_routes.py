from flask import Blueprint, request, jsonify
from auth_middleware import require_auth, get_user_id_from_token
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
        
        # Create a new project instance
        new_project = Project(project_name)
        
        # Save it to the database, associated with the user
        # We assume `save_to_db` is updated to take a user_id
        project_id = new_project.save_to_db(user_id=user_id)
        
        logger.info(f"User '{user_id}' created project '{project_name}' ({project_id})")
        
        return jsonify({
            "status": "created",
            "project_id": str(project_id), # Ensure project_id is a string
            "project_name": new_project.name
        }), 201

    except Exception as e:
        logger.error(f"Error creating project for user '{user_id}': {e}", exc_info=True)
        return jsonify({"error": "Failed to create project on server"}), 500

@api_v2.route('/projects', methods=['GET'])
@require_auth
def get_projects(current_user):
    """Lists all projects for the authenticated user."""
    try:
        user_id = current_user.get('sub')
        # We assume `list_all_projects` is updated to filter by user_id
        projects = Project.list_all_projects(user_id=user_id)
        return jsonify({"projects": projects})
    except Exception as e:
        logger.error(f"Error listing projects for user '{user_id}': {e}", exc_info=True)
        return jsonify({"error": "Failed to list projects"}), 500