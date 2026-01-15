from flask import Blueprint, request, jsonify, Response
from auth_middleware import require_auth
from project import Project
import logging
import json
from datetime import datetime

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
        user_email = current_user.get('email', '')

        from user_service import UserService
        project = UserService.create_project(user_id, project_name, user_email)

        logger.info(f"User '{user_id}' created project '{project_name}' ({project.get('project_id')})")

        return jsonify({
            "status": "created",
            "project": project
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
        user_email = current_user.get('email', '')
        from user_service import UserService
        projects = UserService.get_all_projects(user_id, user_email)

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
        return jsonify({"workflows": workflows}), 200
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


# ==========================================
# Block Schema Processing
# ==========================================

@api_v2.route('/blocks/process-schema', methods=['POST'])
@require_auth
def process_block_schema(current_user):
    """
    Processes a block with a new schema_key, returning the updated block structure
    with properly configured inputs and outputs.
    """
    try:
        data = request.json
        block_data = data.get("block")
        schema_key = data.get("schema_key")

        if not block_data or not schema_key:
            return jsonify({"error": "Missing block or schema_key"}), 400

        # Import block types
        from block_types.api_block import APIBlock

        # Create a temporary APIBlock with the new schema
        temp_block = APIBlock(
            name=block_data.get("name", "API Block"),
            schema_key=schema_key,
            x=block_data.get("x", 0),
            y=block_data.get("y", 0)
        )

        # Set the block ID to match the original
        temp_block.id = block_data.get("id")

        # Return the updated block structure
        return jsonify({"block": temp_block.to_dict()}), 200

    except Exception as e:
        logger.error(f"Error processing block schema: {e}", exc_info=True)
        return jsonify({"error": "Failed to process block schema"}), 500


# ==========================================
# Missing Project Routes
# ==========================================

@api_v2.route('/projects/<project_id>', methods=['GET'])
@require_auth
def get_project_by_id(current_user, project_id):
    """Get a specific project by ID."""
    try:
        user_id = current_user.get('sub')
        from user_service import UserService
        project = UserService.get_project(user_id, project_id)

        if not project:
            return jsonify({"error": "Project not found"}), 404

        return jsonify({"project": project}), 200

    except Exception as e:
        logger.error(f"Error fetching project: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch project"}), 500


@api_v2.route('/projects/<project_id>', methods=['PUT'])
@require_auth
def update_project_by_id(current_user, project_id):
    """Update a specific project."""
    try:
        user_id = current_user.get('sub')
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        from user_service import UserService
        success = UserService.update_project(user_id, project_id, data)

        if not success:
            return jsonify({"error": "Failed to update project"}), 404

        return jsonify({"status": "updated"}), 200

    except Exception as e:
        logger.error(f"Error updating project: {e}", exc_info=True)
        return jsonify({"error": "Failed to update project"}), 500


@api_v2.route('/projects/<project_id>', methods=['DELETE'])
@require_auth
def delete_project_by_id(current_user, project_id):
    """Delete a specific project."""
    try:
        user_id = current_user.get('sub')
        from user_service import UserService
        success = UserService.delete_project(user_id, project_id)

        if not success:
            return jsonify({"error": "Failed to delete project"}), 404

        return jsonify({"status": "deleted"}), 200

    except Exception as e:
        logger.error(f"Error deleting project: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete project"}), 500


@api_v2.route('/projects/<project_id>/workflows/<workflow_id>/execute', methods=['POST'])
@require_auth
def execute_workflow_by_id(current_user, project_id, workflow_id):
    """Execute a specific workflow with streaming response."""
    try:
        user_id = current_user.get('sub')
        data = request.get_json() or {}

        # If nodes/edges not provided, fetch from database
        if not data.get('nodes') or not data.get('edges'):
            from user_service import UserService
            workflow = UserService.get_workflow(user_id, project_id, workflow_id)
            if not workflow:
                return jsonify({"error": "Workflow not found"}), 404

            data['nodes'] = workflow.get('data', {}).get('nodes', [])
            data['edges'] = workflow.get('data', {}).get('edges', [])

        data['workflow_id'] = workflow_id
        data['project_id'] = project_id

        # Use existing execution engine from main.py
        def generate():
            try:
                # Import the execution engine function
                from main import execute_graph
                from main import StartBlock
                from block_types.api_block import APIBlock
                from block_types.logic_block import LogicBlock
                from block_types.react_block import ReactBlock
                from block_types.transform_block import TransformBlock
                from block_types.start_block import StartBlock
                from block_types.string_builder_block import StringBuilderBlock
                from block_types.wait_block import WaitBlock
                from block_types.dialogue_block import DialogueBlock
                from block_types.api_key_block import ApiKeyBlock

                # Reconstruct blocks from workflow data
                # NOTE: This is a simplified version - full implementation would
                # reconstruct the block graph from the workflow data
                # For now, return an error message suggesting to use the main execute endpoint

                error_event = {
                    "status": "error",
                    "message": "Workflow execution from v2 API not fully implemented yet. Please use the workflow editor to execute.",
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(error_event)}\n\n"

            except Exception as e:
                error_event = {
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield f"data: {json.dumps(error_event)}\n\n"

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        logger.error(f"Error executing workflow: {e}", exc_info=True)
        return jsonify({"error": "Failed to execute workflow"}), 500
