"""
Agent Routes
Flask Blueprint for Gemini agent endpoints.
"""

from flask import Blueprint, request, jsonify
from auth_middleware import require_auth
from services.integrations.gemini_agent_service import GeminiAgentService
import logging

logger = logging.getLogger(__name__)

agent_bp = Blueprint('agent', __name__, url_prefix='/api/ai/agent')


@agent_bp.route('/chat', methods=['POST'])
@require_auth
def agent_chat(current_user):
    """
    Main agent chat endpoint.

    Request body:
    {
        "message": "Create a Stripe payment node",
        "chatHistory": [{role: "user", content: "..."}],
        "workflowContext": {
            "projectId": "uuid",
            "workflowId": "uuid",
            "nodes": [...],
            "edges": [...]
        }
    }

    Response:
    {
        "success": true,
        "message": "I've created a Stripe payment node",
        "toolExecutions": [
            {
                "tool": "create_node",
                "params": {...},
                "result": {...}
            }
        ],
        "workflowUpdated": true
    }
    """
    try:
        user_id = current_user.get('sub')
        if not user_id:
            return jsonify({"error": "User ID not found in token"}), 401

        data = request.json
        message = data.get("message")
        chat_history = data.get("chatHistory", [])
        workflow_context = data.get("workflowContext", {})

        if not message:
            return jsonify({"error": "Message is required"}), 400

        if not workflow_context.get("projectId") or not workflow_context.get("workflowId"):
            return jsonify({"error": "Workflow context (projectId, workflowId) is required"}), 400

        # Add user_id to context
        workflow_context["userId"] = user_id

        # Initialize agent service
        agent_service = GeminiAgentService()

        # Handle agent request
        result = agent_service.handle_agent_request(
            message=message,
            workflow_context=workflow_context,
            chat_history=chat_history
        )

        logger.info(f"Agent request completed: {result.get('success')}, "
                   f"tools_executed: {len(result.get('toolExecutions', []))}")

        return jsonify(result), 200 if result.get("success") else 500

    except ValueError as e:
        # Configuration error (e.g., missing API key)
        logger.error(f"Agent configuration error: {e}")
        return jsonify({
            "success": False,
            "error": "Agent service not configured properly. Please check GEMINI_API_KEY."
        }), 500
    except Exception as e:
        logger.error(f"Agent chat error: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Agent request failed: {str(e)}"
        }), 500


@agent_bp.route('/health', methods=['GET'])
def agent_health():
    """
    Health check endpoint for the agent service.

    Returns:
    {
        "status": "ok",
        "geminiConfigured": true
    }
    """
    try:
        import os
        api_key = os.getenv('GEMINI_API_KEY')
        configured = api_key and api_key != 'your_gemini_api_key_here'

        return jsonify({
            "status": "ok" if configured else "not_configured",
            "geminiConfigured": configured
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500
