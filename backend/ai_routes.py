"""
AI Assistant API Routes
Provides endpoints for intelligent workflow assistance using Moorcheh AI
"""

from flask import Blueprint, jsonify, request
from auth_middleware import require_auth
from services.integrations.ai_service import get_ai_service

# Create Blueprint for AI routes
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# Get AI service instance
ai_service = get_ai_service()


@ai_bp.route('/recommend-nodes', methods=['POST'])
@require_auth
def recommend_nodes(current_user):
    """
    Get node recommendations based on current workflow state

    Request body:
    {
        "currentNodeType": "stripe_payment",
        "outputFields": ["payment_id", "customer_email", "amount"],
        "userIntent": "send a receipt email" (optional)
    }
    """
    try:
        data = request.json
        current_node_type = data.get('currentNodeType')
        output_fields = data.get('outputFields', [])
        user_intent = data.get('userIntent')

        if not current_node_type:
            return jsonify({"error": "currentNodeType is required"}), 400

        suggestions = ai_service.get_node_recommendations(
            current_node_type=current_node_type,
            current_output_fields=output_fields,
            user_intent=user_intent
        )

        return jsonify({
            "success": True,
            "suggestions": suggestions
        }), 200

    except Exception as e:
        print(f"Error in recommend_nodes: {e}")
        return jsonify({"error": str(e)}), 500


@ai_bp.route('/validate-connection', methods=['POST'])
@require_auth
def validate_connection(current_user):
    """
    Validate a connection between two nodes

    Request body:
    {
        "sourceNodeId": "node_1",
        "sourceOutputField": "customer_email",
        "targetNodeId": "node_2",
        "targetInputField": "recipient"
    }
    """
    try:
        data = request.json
        source_node_id = data.get('sourceNodeId')
        source_output_field = data.get('sourceOutputField')
        target_node_id = data.get('targetNodeId')
        target_input_field = data.get('targetInputField')

        if not all([source_node_id, source_output_field, target_node_id, target_input_field]):
            return jsonify({"error": "All fields are required"}), 400

        validation = ai_service.validate_and_suggest_connection(
            source_node_id=source_node_id,
            source_output_field=source_output_field,
            target_node_id=target_node_id,
            target_input_field=target_input_field
        )

        return jsonify({
            "success": True,
            "validation": validation
        }), 200

    except Exception as e:
        print(f"Error in validate_connection: {e}")
        return jsonify({"error": str(e)}), 500


@ai_bp.route('/instructions', methods=['POST'])
@require_auth
def get_instructions(current_user):
    """
    Get instructions for workflow tasks

    Request body:
    {
        "question": "How do I connect two nodes together?"
    }
    """
    try:
        data = request.json
        question = data.get('question')

        if not question:
            return jsonify({"error": "question is required"}), 400

        result = ai_service.get_instructions(question)

        return jsonify({
            "success": True,
            "answer": result["answer"],
            "sources": result["sources"],
            "confidence": result["confidence"]
        }), 200

    except Exception as e:
        print(f"Error in get_instructions: {e}")
        return jsonify({"error": str(e)}), 500


@ai_bp.route('/api-schema', methods=['POST'])
@require_auth
def get_api_schema(current_user):
    """
    Get API schema information

    Request body:
    {
        "provider": "stripe",
        "endpoint": "/v1/payment_intents" (optional),
        "question": "What parameters are required?" (optional)
    }
    """
    try:
        data = request.json
        provider = data.get('provider')
        endpoint = data.get('endpoint')
        question = data.get('question')

        if not provider:
            return jsonify({"error": "provider is required"}), 400

        result = ai_service.get_api_schema_info(
            provider=provider,
            endpoint=endpoint,
            specific_question=question
        )

        return jsonify({
            "success": True,
            "answer": result["answer"],
            "sources": result["sources"],
            "confidence": result["confidence"]
        }), 200

    except Exception as e:
        print(f"Error in get_api_schema: {e}")
        return jsonify({"error": str(e)}), 500


@ai_bp.route('/auto-map', methods=['POST'])
@require_auth
def auto_map_fields(current_user):
    """
    Auto-map fields between nodes using AI

    Request body:
    {
        "sourceFields": [
            {"name": "customer_email", "type": "string"},
            {"name": "payment_amount", "type": "number"}
        ],
        "targetFields": [
            {"name": "recipient", "type": "string", "required": true},
            {"name": "amount", "type": "number", "required": true}
        ]
    }
    """
    try:
        data = request.json
        source_fields = data.get('sourceFields', [])
        target_fields = data.get('targetFields', [])

        if not source_fields or not target_fields:
            return jsonify({"error": "sourceFields and targetFields are required"}), 400

        mappings = ai_service.auto_map_fields(
            source_fields=source_fields,
            target_fields=target_fields
        )

        return jsonify({
            "success": True,
            "mappings": mappings
        }), 200

    except Exception as e:
        print(f"Error in auto_map_fields: {e}")
        return jsonify({"error": str(e)}), 500


@ai_bp.route('/chat', methods=['POST'])
@require_auth
def chat(current_user):
    """
    Chat with AI assistant

    Request body:
    {
        "message": "How do I add a webhook?",
        "chatHistory": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ] (optional),
        "workflowContext": {
            "currentNodes": ["stripe_payment", "slack_webhook"],
            "selectedNode": "stripe_payment"
        } (optional)
    }
    """
    try:
        data = request.json
        message = data.get('message')
        chat_history = data.get('chatHistory', [])
        workflow_context = data.get('workflowContext')

        if not message:
            return jsonify({"error": "message is required"}), 400

        response = ai_service.chat(
            message=message,
            chat_history=chat_history,
            workflow_context=workflow_context
        )

        return jsonify({
            "success": True,
            "response": response
        }), 200

    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({"error": str(e)}), 500


@ai_bp.route('/troubleshoot', methods=['POST'])
@require_auth
def troubleshoot(current_user):
    """
    Get troubleshooting help and best practices

    Request body:
    {
        "workflowDescription": "Payment processing workflow" (optional),
        "currentIssue": "Stripe payments failing" (optional),
        "nodeTypes": ["stripe_payment", "slack_webhook"] (optional)
    }
    """
    try:
        data = request.json
        workflow_description = data.get('workflowDescription')
        current_issue = data.get('currentIssue')
        node_types = data.get('nodeTypes', [])

        result = ai_service.get_best_practices_or_troubleshoot(
            workflow_description=workflow_description,
            current_issue=current_issue,
            node_types=node_types
        )

        return jsonify({
            "success": True,
            "answer": result["answer"],
            "sources": result["sources"],
            "confidence": result["confidence"]
        }), 200

    except Exception as e:
        print(f"Error in troubleshoot: {e}")
        return jsonify({"error": str(e)}), 500


# Health check for AI service
@ai_bp.route('/health', methods=['GET'])
def health_check():
    """Check if AI service is operational"""
    try:
        # Try a simple query to verify Moorcheh connection
        result = ai_service.get_instructions("test")
        return jsonify({
            "status": "healthy",
            "message": "AI service is operational"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503
