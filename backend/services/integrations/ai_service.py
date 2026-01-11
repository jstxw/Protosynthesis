"""
AI Service for Workflow Builder
Provides intelligent node recommendations, connection validation,
field mapping, troubleshooting, and conversational assistance
using Moorcheh AI's RAG capabilities
"""

import os
import json
from typing import List, Dict, Any, Optional
from .moorcheh_client import get_moorcheh_client
from dotenv import load_dotenv

load_dotenv()


class AIService:
    """Service for AI-powered workflow assistance"""

    def __init__(self):
        self.client = get_moorcheh_client()
        self.ai_model = os.getenv("MOORCHEH_AI_MODEL", "anthropic.claude-sonnet-4-20250514-v1:0")
        self.ns_api_schemas = os.getenv("MOORCHEH_NS_API_SCHEMAS", "workflow_api_schemas")
        self.ns_node_templates = os.getenv("MOORCHEH_NS_NODE_TEMPLATES", "workflow_node_templates")
        self.ns_instructions = os.getenv("MOORCHEH_NS_INSTRUCTIONS", "workflow_instructions")

    # ============================================================
    # QUERY PATTERN 1: Node Recommendations
    # Use case: User asks "What node should I use after Stripe payment?"
    # ============================================================
    def get_node_recommendations(
        self,
        current_node_type: str,
        current_output_fields: List[str],
        user_intent: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recommend nodes that work well after the current node

        Args:
            current_node_type: Type of the current node (e.g., "stripe_payment")
            current_output_fields: Available output fields from current node
            user_intent: Optional description of what user wants to do

        Returns:
            List of node suggestions with reasons and compatibility scores
        """
        query = f"""
        Recommend API nodes that work well after {current_node_type}.
        Available output fields from current node: {', '.join(current_output_fields)}.
        {f"User wants to: {user_intent}" if user_intent else ""}

        What nodes should connect next and why? Consider:
        1. Data compatibility - which nodes accept these output types
        2. Common workflow patterns - what typically follows this operation
        3. Best practices - recommended next steps for this API

        Provide 3-5 specific node recommendations.
        """

        try:
            response = self.client.get_answer(
                namespace_name=self.ns_node_templates,
                query=query,
                ai_model=self.ai_model,
                top_k=5,
                header_prompt="""You are a workflow assistant helping users build API integrations.
                Recommend compatible nodes based on data flow and common patterns.
                Format each suggestion with: node name, why it's a good fit, and compatibility score (0-1).
                Return as JSON array with format:
                [{"nodeId": "string", "name": "string", "reason": "string", "compatibilityScore": number}]
                Only return the JSON array, no other text."""
            )

            # Try to parse as JSON first
            try:
                suggestions = json.loads(response.get("answer", "[]"))
                if isinstance(suggestions, list):
                    return suggestions
            except json.JSONDecodeError:
                pass

            # Fallback: use sources
            sources = response.get("sources", [])
            return [
                {
                    "nodeId": source.get("id", ""),
                    "name": source.get("id", "").replace("node_", "").replace("_", " ").title(),
                    "reason": source.get("text", "")[:200],
                    "compatibilityScore": source.get("score", 0.5)
                }
                for source in sources[:5]
            ]

        except Exception as error:
            print(f"Error getting node recommendations: {error}")
            return []

    # ============================================================
    # QUERY PATTERN 2: Connection Validation & Suggestions
    # Use case: User tries to connect two nodes
    # ============================================================
    def validate_and_suggest_connection(
        self,
        source_node_id: str,
        source_output_field: str,
        target_node_id: str,
        target_input_field: str
    ) -> Dict[str, Any]:
        """
        Validate a proposed connection and suggest improvements

        Args:
            source_node_id: ID of source node
            source_output_field: Output field being connected
            target_node_id: ID of target node
            target_input_field: Input field receiving data

        Returns:
            Dict with isValid, suggestions, and transformations needed
        """
        query = f"""
        Validate this node connection:
        Source: {source_node_id}.{source_output_field} → Target: {target_node_id}.{target_input_field}

        Answer these questions:
        1. Is this a valid data flow connection?
        2. What data transformations might be needed (if any)?
        3. What are best practices for this connection type?
        4. Any potential issues or warnings?
        """

        try:
            response = self.client.get_answer(
                namespace_name=self.ns_instructions,
                query=query,
                ai_model=self.ai_model,
                top_k=3,
                header_prompt="""You are a workflow validation assistant.
                Determine if the proposed connection is valid.
                Suggest any necessary transformations.
                Return JSON with format:
                {"isValid": boolean, "suggestions": [string], "transformationsNeeded": [string]}
                Only return the JSON, no other text."""
            )

            # Try to parse as JSON
            try:
                result = json.loads(response.get("answer", "{}"))
                return result
            except json.JSONDecodeError:
                # Fallback to text response
                answer = response.get("answer", "")
                return {
                    "isValid": "valid" in answer.lower() or "yes" in answer.lower(),
                    "suggestions": [answer],
                    "transformationsNeeded": []
                }

        except Exception as error:
            print(f"Error validating connection: {error}")
            return {
                "isValid": True,
                "suggestions": [],
                "transformationsNeeded": []
            }

    # ============================================================
    # QUERY PATTERN 3: How-To Instructions
    # Use case: User asks "How do I add a webhook trigger?"
    # ============================================================
    def get_instructions(self, user_question: str) -> Dict[str, Any]:
        """
        Get step-by-step instructions for workflow tasks

        Args:
            user_question: User's question about how to do something

        Returns:
            Dict with answer text, sources, and confidence score
        """
        try:
            response = self.client.get_answer(
                namespace_name=self.ns_instructions,
                query=user_question,
                ai_model=self.ai_model,
                top_k=5,
                header_prompt="""You are a helpful workflow builder assistant.
                Provide clear, step-by-step instructions.
                Reference specific UI elements and keyboard shortcuts.
                Warn about common mistakes.
                Keep responses concise but complete.
                Format with numbered steps when appropriate."""
            )

            sources = response.get("sources", [])
            confidence = max([s.get("score", 0) for s in sources]) if sources else 0

            return {
                "answer": response.get("answer", ""),
                "sources": sources,
                "confidence": confidence
            }

        except Exception as error:
            print(f"Error getting instructions: {error}")
            return {
                "answer": "I encountered an error retrieving instructions. Please try rephrasing your question.",
                "sources": [],
                "confidence": 0
            }

    # ============================================================
    # QUERY PATTERN 4: API Schema Lookup
    # Use case: User configures a Stripe node and needs schema info
    # ============================================================
    def get_api_schema_info(
        self,
        provider: str,
        endpoint: Optional[str] = None,
        specific_question: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get API schema information and documentation

        Args:
            provider: API provider name (e.g., "stripe", "openai")
            endpoint: Optional specific endpoint
            specific_question: Optional specific question about the API

        Returns:
            Dict with answer, sources, and confidence
        """
        query = specific_question or f"{provider} API {endpoint or ''} documentation, parameters, authentication, response format, best practices"

        try:
            response = self.client.get_answer(
                namespace_name=self.ns_api_schemas,
                query=query,
                ai_model=self.ai_model,
                top_k=3,
                header_prompt="""You are an API documentation assistant.
                Provide accurate schema information including required fields, types, and authentication.
                Include example values where helpful.
                Mention rate limits and best practices.
                Keep technical details precise."""
            )

            sources = response.get("sources", [])
            confidence = max([s.get("score", 0) for s in sources]) if sources else 0

            return {
                "answer": response.get("answer", ""),
                "sources": sources,
                "confidence": confidence
            }

        except Exception as error:
            print(f"Error getting API schema info: {error}")
            return {
                "answer": "I encountered an error retrieving API information. Please check the API documentation directly.",
                "sources": [],
                "confidence": 0
            }

    # ============================================================
    # QUERY PATTERN 5: Best Practices & Troubleshooting
    # Use case: User asks "Why isn't my workflow working?"
    # ============================================================
    def get_best_practices_or_troubleshoot(
        self,
        workflow_description: Optional[str] = None,
        current_issue: Optional[str] = None,
        node_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get best practices guidance or troubleshooting help

        Args:
            workflow_description: Description of the workflow
            current_issue: Specific issue user is facing
            node_types: List of node types in the workflow

        Returns:
            Dict with answer, sources, and confidence
        """
        query = current_issue or f"Best practices for workflow with: {', '.join(node_types or [])}"

        try:
            # Search across multiple namespaces for comprehensive help
            instructions_response = self.client.search(
                namespace_name=self.ns_instructions,
                query=query,
                top_k=3
            )

            templates_response = self.client.search(
                namespace_name=self.ns_node_templates,
                query=query,
                top_k=2
            )

            # Combine results
            all_sources = (
                instructions_response.get("matches", []) +
                templates_response.get("matches", [])
            )

            # Get AI answer
            response = self.client.get_answer(
                namespace_name=self.ns_instructions,
                query=query,
                ai_model=self.ai_model,
                top_k=5,
                header_prompt="""You are an expert workflow troubleshooter.
                Analyze the issue and provide specific solutions.
                Reference best practices and common patterns.
                Suggest preventive measures for the future.
                Be practical and actionable."""
            )

            confidence = max([s.get("score", 0) for s in all_sources]) if all_sources else 0

            return {
                "answer": response.get("answer", ""),
                "sources": all_sources,
                "confidence": confidence
            }

        except Exception as error:
            print(f"Error getting best practices: {error}")
            return {
                "answer": "I encountered an error. Please provide more details about your workflow issue.",
                "sources": [],
                "confidence": 0
            }

    # ============================================================
    # QUERY PATTERN 6: Auto-Map Fields with AI
    # Use case: User clicks "Auto-Map" in field mapper
    # ============================================================
    def auto_map_fields(
        self,
        source_fields: List[Dict[str, str]],
        target_fields: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Automatically map source fields to target fields using AI

        Args:
            source_fields: List of dicts with 'name' and 'type'
            target_fields: List of dicts with 'name', 'type', and 'required'

        Returns:
            List of field mappings with confidence scores
        """
        query = f"""
        Map these source fields to target fields:
        Source: {json.dumps(source_fields)}
        Target: {json.dumps(target_fields)}

        Consider:
        1. Semantic similarity (customer_email → recipient)
        2. Type compatibility (number → number, string → string)
        3. Common API conventions

        Provide mappings for all target fields, especially required ones.
        """

        try:
            response = self.client.get_answer(
                namespace_name=self.ns_api_schemas,
                query=query,
                ai_model=self.ai_model,
                top_k=5,
                header_prompt="""You are a field mapping assistant.
                Match source fields to target fields based on:
                1. Semantic similarity (customer_email → recipient)
                2. Type compatibility (number → number, string → string)
                3. Common API conventions

                Return JSON array of mappings:
                [{"sourceField": "string", "targetField": "string", "confidence": number, "transformSuggestion": "string or null"}]

                Suggest transformations when types don't match exactly.
                Only return the JSON array, no other text."""
            )

            # Try to parse as JSON
            try:
                mappings = json.loads(response.get("answer", "[]"))
                if isinstance(mappings, list):
                    return mappings
            except json.JSONDecodeError:
                pass

            # Fallback to basic type matching
            mappings = []
            for target in target_fields:
                if not target.get("required"):
                    continue

                # Find best match from source fields
                best_match = None
                best_score = 0

                for source in source_fields:
                    score = 0
                    # Exact name match
                    if source["name"].lower() == target["name"].lower():
                        score = 1.0
                    # Partial name match
                    elif source["name"].lower() in target["name"].lower() or target["name"].lower() in source["name"].lower():
                        score = 0.7
                    # Type match bonus
                    if source["type"] == target["type"]:
                        score += 0.2

                    if score > best_score:
                        best_score = score
                        best_match = source

                if best_match:
                    mappings.append({
                        "sourceField": best_match["name"],
                        "targetField": target["name"],
                        "confidence": best_score,
                        "transformSuggestion": None if best_match["type"] == target["type"] else f"to_{target['type']}"
                    })

            return mappings

        except Exception as error:
            print(f"Error auto-mapping fields: {error}")
            return []

    # ============================================================
    # QUERY PATTERN 7: Conversational Assistant with History
    # Use case: Multi-turn conversation in assistant panel
    # ============================================================
    def chat(
        self,
        message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        workflow_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Chat with AI assistant about workflows

        Args:
            message: User's message
            chat_history: Previous chat messages with 'role' and 'content'
            workflow_context: Current workflow state (nodes, selected node, etc.)

        Returns:
            AI assistant's response
        """
        # Determine which namespace to query based on message content
        namespace = self.ns_instructions  # Default

        message_lower = message.lower()
        if any(keyword in message_lower for keyword in ["api", "schema", "endpoint", "authentication", "auth"]):
            namespace = self.ns_api_schemas
        elif any(keyword in message_lower for keyword in ["node", "template", "add", "connect"]):
            namespace = self.ns_node_templates

        # Build context prefix
        context_prefix = ""
        if workflow_context:
            current_nodes = workflow_context.get("currentNodes", [])
            selected_node = workflow_context.get("selectedNode")

            if current_nodes:
                context_prefix = f"Current workflow has nodes: {', '.join(current_nodes)}. "
            if selected_node:
                context_prefix += f"Selected node: {selected_node}. "

        full_query = f"{context_prefix}\n\nUser question: {message}"

        try:
            response = self.client.get_answer(
                namespace_name=namespace,
                query=full_query,
                ai_model=self.ai_model,
                top_k=5,
                chat_history=chat_history or [],
                header_prompt="""You are a helpful workflow builder assistant.
                Help users create, modify, and troubleshoot API workflows.
                Be concise but thorough. Reference specific nodes and features.
                If you're unsure, say so and suggest where to find more info.
                Provide actionable advice."""
            )

            return response.get("answer", "I'm not sure how to help with that. Can you rephrase your question?")

        except Exception as error:
            print(f"Error in chat: {error}")
            return "I encountered an error. Please try asking your question differently."


# Singleton instance
_ai_service = None

def get_ai_service() -> AIService:
    """Get or create singleton AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
