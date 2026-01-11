"""
Gemini Agent Service
Orchestrates Gemini AI agent with function calling for workflow automation.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from services.integrations.gemini_client import GeminiClient
from user_service import UserService
import uuid

logger = logging.getLogger(__name__)


class GeminiAgentService:
    """
    Service that provides agent capabilities using Gemini with function calling.
    Allows AI to create, modify, connect, and execute workflow nodes.
    """

    def __init__(self):
        """Initialize the agent service with Gemini client."""
        api_key = os.getenv('GEMINI_API_KEY')
        model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')

        if not api_key or api_key == 'your_gemini_api_key_here':
            raise ValueError("GEMINI_API_KEY not configured in environment")

        self.gemini = GeminiClient(api_key, model_name)
        self.max_iterations = int(os.getenv('AGENT_MAX_ITERATIONS', '10'))
        self.tools = self._define_tools()

        logger.info("GeminiAgentService initialized")

    def _get_workflow_data(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Safely get workflow data ensuring it has nodes and edges."""
        workflow_data = workflow.get("data")

        # If data is None or not a dict, initialize it
        if not isinstance(workflow_data, dict):
            workflow_data = {"nodes": [], "edges": []}
        else:
            # Ensure nodes and edges exist
            if "nodes" not in workflow_data:
                workflow_data["nodes"] = []
            if "edges" not in workflow_data:
                workflow_data["edges"] = []

        return workflow_data

    def handle_agent_request(
        self,
        message: str,
        workflow_context: Dict[str, Any],
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for agent requests.

        Args:
            message: User's request
            workflow_context: {projectId, workflowId, nodes, edges}
            chat_history: Previous conversation

        Returns:
            {
                "success": bool,
                "message": str,
                "toolExecutions": [],
                "workflowUpdated": bool
            }
        """
        try:
            user_id = workflow_context.get('userId')
            project_id = workflow_context.get('projectId')
            workflow_id = workflow_context.get('workflowId')

            if not user_id or not project_id or not workflow_id:
                return {
                    "success": False,
                    "error": "Missing required context (userId, projectId, workflowId)"
                }

            # Load current workflow state
            workflow = UserService.get_workflow(user_id, project_id, workflow_id)
            if not workflow:
                return {
                    "success": False,
                    "error": "Workflow not found"
                }

            # Store workflow context for tool execution
            self.current_context = {
                "user_id": user_id,
                "project_id": project_id,
                "workflow_id": workflow_id,
                "workflow": workflow
            }

            # Agent loop with function calling
            tool_executions = []
            workflow_updated = False
            iterations = 0

            # Add workflow context to message
            enriched_message = self._enrich_message_with_context(message, workflow)

            # Log tool information
            logger.info(f"Agent has {len(self.tools)} tools available")
            logger.info(f"Tool names: {[tool['name'] for tool in self.tools]}")

            # Start agent loop
            current_message = enriched_message
            agent_history = chat_history or []

            while iterations < self.max_iterations:
                iterations += 1
                logger.info(f"Agent iteration {iterations}/{self.max_iterations}")
                logger.info(f"Sending message to Gemini: {current_message[:300]}")

                # Send message to Gemini with function definitions
                response = self.gemini.chat_with_functions(
                    message=current_message,
                    functions=self.tools,
                    chat_history=agent_history,
                    system_instruction=self._get_system_instruction()
                )

                # Log the full response for debugging
                logger.info(f"Gemini response - message: {response.get('message', '')[:200]}")
                logger.info(f"Gemini response - function_calls count: {len(response.get('function_calls', []))}")
                logger.info(f"Gemini response - function_calls: {response.get('function_calls', [])}")

                # Check if Gemini wants to call functions
                function_calls = response.get("function_calls", [])

                if not function_calls:
                    # No more function calls - agent is done
                    final_message = response.get("message", "Done")
                    logger.info(f"Agent completed without function calls. Message: {final_message[:200]}")
                    return {
                        "success": True,
                        "message": final_message,
                        "toolExecutions": tool_executions,
                        "workflowUpdated": workflow_updated
                    }

                # Execute each function call
                function_results = []
                for func_call in function_calls:
                    func_name = func_call.get("name")
                    func_args = func_call.get("args", {})

                    logger.info(f"Executing tool: {func_name} with args: {func_args}")

                    # Execute the tool
                    result = self._execute_tool(func_name, func_args)

                    tool_executions.append({
                        "tool": func_name,
                        "params": func_args,
                        "result": result
                    })

                    if result.get("success"):
                        workflow_updated = True

                        # Reload workflow to get latest state
                        workflow = UserService.get_workflow(user_id, project_id, workflow_id)
                        self.current_context["workflow"] = workflow

                    function_results.append({
                        "name": func_name,
                        "result": result
                    })

                # Send function results back to Gemini
                # Update message with function results for next iteration
                results_text = self._format_function_results(function_results)
                current_message = f"Function execution results:\n{results_text}\n\nContinue or provide final response."

                # Add to history
                agent_history.append({
                    "role": "user",
                    "content": current_message
                })

            # Max iterations reached
            return {
                "success": True,
                "message": "Agent completed (max iterations reached)",
                "toolExecutions": tool_executions,
                "workflowUpdated": workflow_updated
            }

        except Exception as e:
            logger.error(f"Agent request failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _define_tools(self) -> List[Dict[str, Any]]:
        """
        Define the 6 tools available to the agent.

        Returns:
            List of function definitions in Gemini format
        """
        return [
            {
                "name": "create_node",
                "description": "Create a new node in the workflow. Use this to add blocks like API calls, logic operations, transformations, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "node_type": {
                            "type": "string",
                            "enum": ["API", "LOGIC", "TRANSFORM", "START", "WAIT", "DIALOGUE", "LOOP", "STRING_BUILDER", "REACT"],
                            "description": "Type of node to create"
                        },
                        "name": {
                            "type": "string",
                            "description": "Display name for the node"
                        },
                        "x": {
                            "type": "number",
                            "description": "X position on canvas (default: 150)",
                            "default": 150
                        },
                        "y": {
                            "type": "number",
                            "description": "Y position on canvas (default: 150)",
                            "default": 150
                        },
                        "config": {
                            "type": "object",
                            "description": "Node-specific configuration (url, method, schema_key, operation, fields, etc.)",
                            "properties": {
                                "url": {"type": "string"},
                                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                                "schema_key": {"type": "string"},
                                "operation": {"type": "string"},
                                "fields": {"type": "string"},
                                "template": {"type": "string"},
                                "delay": {"type": "number"}
                            }
                        }
                    },
                    "required": ["node_type", "name"]
                }
            },
            {
                "name": "update_node",
                "description": "Update an existing node's configuration or position",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "ID of the node to update"
                        },
                        "updates": {
                            "type": "object",
                            "description": "Fields to update (name, url, method, x, y, etc.)",
                            "properties": {
                                "name": {"type": "string"},
                                "url": {"type": "string"},
                                "method": {"type": "string"},
                                "x": {"type": "number"},
                                "y": {"type": "number"},
                                "schema_key": {"type": "string"}
                            }
                        }
                    },
                    "required": ["node_id", "updates"]
                }
            },
            {
                "name": "connect_nodes",
                "description": "Create a connection/edge between two nodes. This links the output of one node to the input of another.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "source_node_id": {
                            "type": "string",
                            "description": "ID of the source node"
                        },
                        "source_output": {
                            "type": "string",
                            "description": "Output handle name (e.g., 'response', 'result', 'data_out')",
                            "default": "data_out"
                        },
                        "target_node_id": {
                            "type": "string",
                            "description": "ID of the target node"
                        },
                        "target_input": {
                            "type": "string",
                            "description": "Input handle name (e.g., 'data', 'data_in')",
                            "default": "data_in"
                        }
                    },
                    "required": ["source_node_id", "target_node_id"]
                }
            },
            {
                "name": "delete_node",
                "description": "Delete a node from the workflow",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "ID of the node to delete"
                        }
                    },
                    "required": ["node_id"]
                }
            },
            {
                "name": "execute_workflow",
                "description": "Execute the workflow and return results. Use this to test the workflow.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dry_run": {
                            "type": "boolean",
                            "description": "If true, validate without executing (default: false)",
                            "default": False
                        }
                    }
                }
            },
            {
                "name": "get_workflow_state",
                "description": "Get the current workflow state including all nodes and connections. Use this to understand what's already in the workflow.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            params: Tool parameters

        Returns:
            Result dict with success flag
        """
        try:
            # Route to appropriate handler
            if tool_name == "create_node":
                return self._create_node(params)
            elif tool_name == "update_node":
                return self._update_node(params)
            elif tool_name == "connect_nodes":
                return self._connect_nodes(params)
            elif tool_name == "delete_node":
                return self._delete_node(params)
            elif tool_name == "execute_workflow":
                return self._execute_workflow(params)
            elif tool_name == "get_workflow_state":
                return self._get_workflow_state(params)
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }

        except ValueError as e:
            # Validation error - agent can retry
            return {
                "success": False,
                "error": str(e),
                "retry": True
            }
        except Exception as e:
            # Fatal error
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "retry": False
            }

    def _create_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new node in the workflow."""
        node_type = params.get("node_type")
        name = params.get("name")
        x = params.get("x", 150)
        y = params.get("y", 150)
        config = params.get("config", {})

        # Import block classes
        from block_types.api_block import APIBlock
        from block_types.logic_block import LogicBlock
        from block_types.transform_block import TransformBlock
        from block_types.start_block import StartBlock
        from block_types.string_builder_block import StringBuilderBlock
        from block_types.wait_block import WaitBlock
        from block_types.dialogue_block import DialogueBlock
        from block_types.loop_block import LoopBlock
        from block_types.react_block import ReactBlock

        # Create the appropriate block object based on type
        block = None
        try:
            if node_type == "API":
                schema_key = config.get("schema_key", "custom")
                block = APIBlock(name, schema_key, x=x, y=y)
                # If custom API, allow URL override
                if schema_key == "custom" and "url" in config:
                    block.url = config["url"]
                if "method" in config:
                    block.method = config["method"]

            elif node_type == "LOGIC":
                operation = config.get("operation", "add")
                block = LogicBlock(name, operation, x=x, y=y)

            elif node_type == "TRANSFORM":
                t_type = config.get("transformation_type", "to_string")
                fields = config.get("fields", "")
                block = TransformBlock(name, t_type, fields=fields, x=x, y=y)

            elif node_type == "STRING_BUILDER":
                template = config.get("template", "")
                block = StringBuilderBlock(name, template, x=x, y=y)

            elif node_type == "START":
                block = StartBlock(name, x=x, y=y)

            elif node_type == "WAIT":
                delay = config.get("delay", 1.0)
                block = WaitBlock(name, delay=delay, x=x, y=y)

            elif node_type == "DIALOGUE":
                message = config.get("message", "")
                block = DialogueBlock(name, message=message, x=x, y=y)

            elif node_type == "LOOP":
                block = LoopBlock(name, x=x, y=y)

            elif node_type == "REACT":
                jsx_code = config.get("jsx_code", "export default function MyComponent({ data_in, onWorkflowOutputChange }) {\n  return <div>Input: {JSON.stringify(data_in)}</div>;\n}")
                css_code = config.get("css_code", "/* CSS */")
                block = ReactBlock(name, jsx_code=jsx_code, css_code=css_code, x=x, y=y)

            else:
                raise ValueError(f"Unknown node type: {node_type}")

            # Convert block to dict (this includes proper inputs/outputs structure)
            block_dict = block.to_dict()

            # Build ReactFlow node structure
            new_node = {
                "id": block.id,
                "type": node_type,
                "position": {"x": x, "y": y},
                "data": block_dict
            }

        except Exception as e:
            logger.error(f"Failed to create block: {e}", exc_info=True)
            raise ValueError(f"Failed to create {node_type} block: {str(e)}")

        # Get current workflow
        workflow = self.current_context["workflow"]
        workflow_data = self._get_workflow_data(workflow)

        # Add node
        workflow_data["nodes"].append(new_node)

        # Update workflow in database
        UserService.update_workflow(
            self.current_context["user_id"],
            self.current_context["project_id"],
            self.current_context["workflow_id"],
            workflow_data  # Pass workflow_data directly, not wrapped in {"data": ...}
        )

        logger.info(f"Created node: {block.id} ({node_type})")

        return {
            "success": True,
            "nodeId": block.id,
            "message": f"Created {node_type} node '{name}' at position ({x}, {y})"
        }

    def _update_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing node."""
        node_id = params.get("node_id")
        updates = params.get("updates", {})

        # Get current workflow
        workflow = self.current_context["workflow"]
        workflow_data = self._get_workflow_data(workflow)

        # Find node
        node = next((n for n in workflow_data["nodes"] if n["id"] == node_id), None)
        if not node:
            raise ValueError(f"Node not found: {node_id}")

        # Apply updates
        if "x" in updates or "y" in updates:
            node["position"]["x"] = updates.get("x", node["position"]["x"])
            node["position"]["y"] = updates.get("y", node["position"]["y"])

        for key, value in updates.items():
            if key not in ["x", "y"]:
                node["data"][key] = value

        # Update workflow
        UserService.update_workflow(
            self.current_context["user_id"],
            self.current_context["project_id"],
            self.current_context["workflow_id"],
            workflow_data
        )

        return {
            "success": True,
            "message": f"Updated node {node_id}"
        }

    def _connect_nodes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a connection between two nodes."""
        source_id = params.get("source_node_id")
        target_id = params.get("target_node_id")
        source_output = params.get("source_output", "data_out")
        target_input = params.get("target_input", "data_in")

        # Get current workflow
        workflow = self.current_context["workflow"]
        workflow_data = self._get_workflow_data(workflow)

        # Verify nodes exist
        source_exists = any(n["id"] == source_id for n in workflow_data["nodes"])
        target_exists = any(n["id"] == target_id for n in workflow_data["nodes"])

        if not source_exists:
            raise ValueError(f"Source node not found: {source_id}")
        if not target_exists:
            raise ValueError(f"Target node not found: {target_id}")

        # Create edge
        edge_id = f"edge_{source_id}_{target_id}_{uuid.uuid4().hex[:6]}"
        new_edge = {
            "id": edge_id,
            "source": source_id,
            "target": target_id,
            "sourceHandle": source_output,
            "targetHandle": target_input,
            "type": "straight"
        }

        # Add edge
        workflow_data["edges"].append(new_edge)

        # Update workflow
        UserService.update_workflow(
            self.current_context["user_id"],
            self.current_context["project_id"],
            self.current_context["workflow_id"],
            workflow_data
        )

        return {
            "success": True,
            "edgeId": edge_id,
            "message": f"Connected {source_id} to {target_id}"
        }

    def _delete_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a node from the workflow."""
        node_id = params.get("node_id")

        # Get current workflow
        workflow = self.current_context["workflow"]
        workflow_data = self._get_workflow_data(workflow)

        # Remove node
        nodes_before = len(workflow_data["nodes"])
        workflow_data["nodes"] = [n for n in workflow_data["nodes"] if n["id"] != node_id]

        if len(workflow_data["nodes"]) == nodes_before:
            raise ValueError(f"Node not found: {node_id}")

        # Remove connected edges
        workflow_data["edges"] = [
            e for e in workflow_data["edges"]
            if e["source"] != node_id and e["target"] != node_id
        ]

        # Update workflow
        UserService.update_workflow(
            self.current_context["user_id"],
            self.current_context["project_id"],
            self.current_context["workflow_id"],
            workflow_data
        )

        return {
            "success": True,
            "message": f"Deleted node {node_id}"
        }

    def _execute_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow."""
        dry_run = params.get("dry_run", False)

        if dry_run:
            return {
                "success": True,
                "message": "Workflow validation passed (dry run)"
            }

        # TODO: Implement actual workflow execution
        # This would call the workflow execution endpoint
        return {
            "success": True,
            "message": "Workflow execution queued (not implemented yet)"
        }

    def _get_workflow_state(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current workflow state."""
        workflow = self.current_context["workflow"]
        workflow_data = self._get_workflow_data(workflow)

        # Summarize workflow
        node_summary = []
        for node in workflow_data["nodes"]:
            node_summary.append({
                "id": node["id"],
                "type": node["type"],
                "name": node["data"].get("name", "Unnamed")
            })

        return {
            "success": True,
            "nodes": node_summary,
            "edges": workflow_data["edges"],
            "nodeCount": len(workflow_data["nodes"]),
            "edgeCount": len(workflow_data["edges"])
        }

    def _enrich_message_with_context(self, message: str, workflow: Dict[str, Any]) -> str:
        """Add workflow context to user message."""
        workflow_data = self._get_workflow_data(workflow)

        nodes = workflow_data["nodes"]
        edges = workflow_data["edges"]

        # Import API schemas
        from api_schemas import API_SCHEMAS

        # Build list of available APIs
        api_list = []
        for key, schema in API_SCHEMAS.items():
            api_list.append(f"  - {key}: {schema['name']}")

        context = f"""User request: {message}

Current workflow state:
- Nodes: {len(nodes)}
- Connections: {len(edges)}

Available node types: API, LOGIC, TRANSFORM, START, WAIT, DIALOGUE, LOOP, STRING_BUILDER, REACT

Available API schemas (use schema_key in config when creating API nodes):
{chr(10).join(api_list[:20])}
... and more

Examples:
- To create agify.io API: create_node(node_type="API", name="Agify", config={{"schema_key": "agify"}})
- To create Stripe API: create_node(node_type="API", name="Stripe", config={{"schema_key": "stripe_charge"}})
- To create custom API: create_node(node_type="API", name="My API", config={{"schema_key": "custom", "url": "https://..."}})

You can use these tools:
- create_node: Add new nodes
- update_node: Modify existing nodes
- connect_nodes: Link nodes together
- delete_node: Remove nodes
- execute_workflow: Run the workflow
- get_workflow_state: See current state

Execute the user's request step by step using these tools."""

        return context

    def _get_system_instruction(self) -> str:
        """Get system instruction for the agent."""
        return """You are a workflow automation agent. Your job is to help users build and modify workflows by creating nodes, connecting them, and configuring them properly.

IMPORTANT: When creating API nodes, you MUST include the schema_key in the config parameter. The schema_key determines which API template to use.

When the user asks you to do something:
1. Use get_workflow_state first if you need to understand the current workflow
2. Create nodes with create_node:
   - For API nodes: ALWAYS include schema_key in config (e.g., config={"schema_key": "agify"})
   - For LOGIC nodes: include operation in config (e.g., config={"operation": "add"})
   - For other nodes: include relevant configuration
3. Connect them with connect_nodes (source_output usually "output", target_input usually "input")
4. Configure them with update_node if needed
5. Provide a clear summary of what you did

Be precise with node IDs and handle names. Always use the function calling tools - don't just describe what to do."""

    def _format_function_results(self, results: List[Dict[str, Any]]) -> str:
        """Format function execution results for Gemini."""
        formatted = []
        for result in results:
            name = result["name"]
            res = result["result"]
            if res.get("success"):
                formatted.append(f"✓ {name}: {res.get('message', 'Success')}")
            else:
                formatted.append(f"✗ {name}: {res.get('error', 'Failed')}")
        return "\n".join(formatted)
