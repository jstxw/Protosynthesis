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
        from user_service import UserService
        projects = UserService.get_all_projects(user_id)

        # Transform for frontend if needed, or return as is
        # UserService returns list of project dicts

        return jsonify({"projects": projects}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to list projects: {str(e)}"}), 500


# ==========================================
# PART 2: Workflow CRUD Endpoints
# ==========================================

@api_v2.route('/projects/<project_id>/workflows', methods=['GET'])
@require_auth
def get_workflows(current_user, project_id):
    """Lists all workflows in a project."""
    try:
        user_id = current_user.get('sub')
        from user_service import UserService
        workflows = UserService.get_all_workflows(user_id, project_id)

        return jsonify({"workflows": workflows}), 200
    except Exception as e:
        logger.error(f"Error fetching workflows for project '{project_id}': {e}", exc_info=True)
        return jsonify({"error": f"Failed to fetch workflows: {str(e)}"}), 500


@api_v2.route('/projects/<project_id>/workflows', methods=['POST'])
@require_auth
def create_workflow(current_user, project_id):
    """Creates a new workflow in a project."""
    try:
        user_id = current_user.get('sub')
        data = request.json
        workflow_name = data.get("name", "New Workflow")
        workflow_data = data.get("data", {"nodes": [], "edges": []})

        from user_service import UserService
        workflow = UserService.create_workflow(user_id, project_id, workflow_name, workflow_data)

        logger.info(f"User '{user_id}' created workflow '{workflow_name}' in project '{project_id}'")

        return jsonify({
            "status": "created",
            "workflow": workflow
        }), 201
    except Exception as e:
        logger.error(f"Error creating workflow in project '{project_id}': {e}", exc_info=True)
        return jsonify({"error": "Failed to create workflow"}), 500


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
        logger.error(f"Error fetching workflow '{workflow_id}': {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch workflow"}), 500


@api_v2.route('/projects/<project_id>/workflows/<workflow_id>', methods=['PUT'])
@require_auth
def update_workflow(current_user, project_id, workflow_id):
    """Updates a workflow (nodes/edges/metadata)."""
    try:
        user_id = current_user.get('sub')
        data = request.json

        from user_service import UserService
        workflow = UserService.update_workflow(user_id, project_id, workflow_id, data)

        if not workflow:
            return jsonify({"error": "Workflow not found"}), 404

        logger.info(f"User '{user_id}' updated workflow '{workflow_id}'")

        return jsonify({
            "status": "updated",
            "workflow": workflow
        }), 200
    except Exception as e:
        logger.error(f"Error updating workflow '{workflow_id}': {e}", exc_info=True)
        return jsonify({"error": "Failed to update workflow"}), 500


@api_v2.route('/projects/<project_id>/workflows/<workflow_id>', methods=['DELETE'])
@require_auth
def delete_workflow(current_user, project_id, workflow_id):
    """Deletes a workflow."""
    try:
        user_id = current_user.get('sub')
        from user_service import UserService
        success = UserService.delete_workflow(user_id, project_id, workflow_id)

        if not success:
            return jsonify({"error": "Workflow not found"}), 404

        logger.info(f"User '{user_id}' deleted workflow '{workflow_id}'")

        return jsonify({"status": "deleted"}), 200
    except Exception as e:
        logger.error(f"Error deleting workflow '{workflow_id}': {e}", exc_info=True)
        return jsonify({"error": "Failed to delete workflow"}), 500


@api_v2.route('/projects/<project_id>/workflows/<workflow_id>/execute', methods=['POST'])
@require_auth
def execute_workflow(current_user, project_id, workflow_id):
    """Executes a workflow and returns results."""
    try:
        user_id = current_user.get('sub')
        from user_service import UserService

        # Get workflow from database
        workflow = UserService.get_workflow(user_id, project_id, workflow_id)
        if not workflow:
            return jsonify({"error": "Workflow not found"}), 404

        # Convert workflow data to Block objects and execute
        from main import execute_graph
        from block_types.api_block import APIBlock
        from block_types.logic_block import LogicBlock
        from block_types.react_block import ReactBlock
        from block_types.transform_block import TransformBlock
        from block_types.start_block import StartBlock
        from block_types.string_builder_block import StringBuilderBlock
        from block_types.wait_block import WaitBlock
        from block_types.dialogue_block import DialogueBlock
        from block_types.loop_block import LoopBlock

        # Build blocks map from workflow data
        blocks_map = {}
        workflow_data = workflow.get('data', {})
        nodes = workflow_data.get('nodes', [])
        edges = workflow_data.get('edges', [])

        # Create Block instances
        for node in nodes:
            node_type = node.get('type')
            node_id = node.get('id')
            node_data = node.get('data', {})

            if node_type == 'API':
                block = APIBlock(
                    node_data.get('name', 'API Block'),
                    node_data.get('schema_key', 'custom'),
                    x=node.get('position', {}).get('x', 0),
                    y=node.get('position', {}).get('y', 0)
                )
                block.id = node_id
            elif node_type == 'LOGIC':
                block = LogicBlock(
                    node_data.get('name', 'Logic Block'),
                    node_data.get('operation', 'add'),
                    x=node.get('position', {}).get('x', 0),
                    y=node.get('position', {}).get('y', 0)
                )
                block.id = node_id
            elif node_type == 'START':
                block = StartBlock(
                    node_data.get('name', 'Start'),
                    x=node.get('position', {}).get('x', 0),
                    y=node.get('position', {}).get('y', 0)
                )
                block.id = node_id
            # Add more block types as needed
            else:
                continue

            blocks_map[node_id] = block

        # Connect blocks based on edges
        for edge in edges:
            source_id = edge.get('source')
            target_id = edge.get('target')
            source_handle = edge.get('sourceHandle')
            target_handle = edge.get('targetHandle')

            if source_id in blocks_map and target_id in blocks_map:
                source_block = blocks_map[source_id]
                target_block = blocks_map[target_id]
                try:
                    source_block.connect(source_handle, target_block, target_handle)
                except Exception as e:
                    logger.warning(f"Failed to connect {source_id} to {target_id}: {e}")

        # Find start blocks
        start_blocks = [block for block in blocks_map.values() if isinstance(block, StartBlock)]

        if not start_blocks:
            return jsonify({"error": "No Start block found in workflow"}), 400

        # Execute workflow and collect results
        execution_results = []
        for event_json in execute_graph(start_blocks, blocks_map):
            import json
            event = json.loads(event_json)
            execution_results.append(event)

        logger.info(f"User '{user_id}' executed workflow '{workflow_id}'")

        return jsonify({
            "status": "executed",
            "results": execution_results
        }), 200
    except Exception as e:
        logger.error(f"Error executing workflow '{workflow_id}': {e}", exc_info=True)
        return jsonify({"error": f"Workflow execution failed: {str(e)}"}), 500
