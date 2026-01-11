"""
Gemini API Client
Wrapper for Google's Generative AI SDK with function calling support.
"""

import google.generativeai as genai
import logging
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Client for interacting with Google's Gemini API.
    Supports function calling for agent-like behavior.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize the Gemini client.

        Args:
            api_key: Google AI Studio API key
            model_name: Gemini model to use (default: gemini-2.0-flash-exp)
        """
        self.api_key = api_key
        self.model_name = model_name

        # Configure the SDK
        genai.configure(api_key=api_key)

        # Initialize the model
        try:
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"Initialized Gemini client with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise

    def chat_with_functions(
        self,
        message: str,
        functions: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat message with function definitions.

        Args:
            message: User message
            functions: List of function definitions in Gemini format
            chat_history: Previous conversation history [{role: str, content: str}]
            system_instruction: Optional system instruction

        Returns:
            {
                "message": str,  # Response text from Gemini
                "function_calls": [  # List of function calls (if any)
                    {
                        "name": str,
                        "args": dict
                    }
                ],
                "finish_reason": str
            }
        """
        try:
            # Convert function definitions to Gemini's Tool format
            tools = self._convert_functions_to_tools(functions)

            # Build conversation history
            history = []
            if chat_history:
                for msg in chat_history:
                    role = "user" if msg.get("role") == "user" else "model"
                    history.append({
                        "role": role,
                        "parts": [{"text": msg.get("content", "")}]
                    })

            # Create model with system instruction if provided
            model_to_use = self.model
            if system_instruction:
                model_to_use = genai.GenerativeModel(
                    self.model_name,
                    system_instruction=system_instruction
                )

            # Start chat session with tools
            chat = model_to_use.start_chat(
                history=history,
                enable_automatic_function_calling=False  # We handle function calls manually
            )

            # Send message with tools
            response = chat.send_message(
                message,
                tools=tools if tools else None
            )

            # Parse response
            result = self._parse_response(response)

            logger.info(f"Gemini response: {result['finish_reason']}, "
                       f"function_calls: {len(result.get('function_calls', []))}")

            return result

        except Exception as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            raise

    def _convert_functions_to_tools(self, functions: List[Dict[str, Any]]) -> List[Any]:
        """
        Convert function definitions to Gemini Tool format.

        Args:
            functions: List of function definitions

        Returns:
            List of Gemini Tool objects
        """
        if not functions:
            return []

        # Gemini expects tools in FunctionDeclaration format
        try:
            tools = []
            for func in functions:
                params = func.get("parameters", {})

                # Convert parameters dict to Schema object
                schema = genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        key: self._convert_property_to_schema(value)
                        for key, value in params.get("properties", {}).items()
                    },
                    required=params.get("required", [])
                )

                # Convert to Gemini's FunctionDeclaration
                function_declaration = genai.protos.FunctionDeclaration(
                    name=func["name"],
                    description=func.get("description", ""),
                    parameters=schema
                )
                tools.append(function_declaration)

            # Wrap in Tool object
            return [genai.protos.Tool(function_declarations=tools)]

        except Exception as e:
            logger.error(f"Error converting functions to tools: {e}", exc_info=True)
            return []

    def _convert_property_to_schema(self, prop: Dict[str, Any]) -> Any:
        """Convert a property definition to Gemini Schema."""
        prop_type = prop.get("type", "string")

        # Map type strings to Gemini types
        type_map = {
            "string": genai.protos.Type.STRING,
            "number": genai.protos.Type.NUMBER,
            "integer": genai.protos.Type.INTEGER,
            "boolean": genai.protos.Type.BOOLEAN,
            "object": genai.protos.Type.OBJECT,
            "array": genai.protos.Type.ARRAY
        }

        gemini_type = type_map.get(prop_type, genai.protos.Type.STRING)

        schema_params = {
            "type": gemini_type,
            "description": prop.get("description", "")
        }

        # Handle enum
        if "enum" in prop:
            schema_params["enum"] = prop["enum"]

        # Handle nested object properties
        if prop_type == "object" and "properties" in prop:
            schema_params["properties"] = {
                key: self._convert_property_to_schema(value)
                for key, value in prop["properties"].items()
            }

        # Handle array items
        if prop_type == "array" and "items" in prop:
            schema_params["items"] = self._convert_property_to_schema(prop["items"])

        return genai.protos.Schema(**schema_params)

    def _convert_to_dict(self, obj: Any) -> Any:
        """
        Recursively convert Gemini proto objects (like MapComposite) to plain Python dicts.

        Args:
            obj: Object to convert

        Returns:
            Plain Python dict/list/primitive
        """
        # Handle None
        if obj is None:
            return None

        # Handle dict-like objects (MapComposite, etc.)
        if hasattr(obj, 'items'):
            return {key: self._convert_to_dict(value) for key, value in obj.items()}

        # Handle list-like objects
        if isinstance(obj, (list, tuple)):
            return [self._convert_to_dict(item) for item in obj]

        # Handle primitives (str, int, float, bool)
        if isinstance(obj, (str, int, float, bool)):
            return obj

        # Try to convert to dict if it has __dict__
        if hasattr(obj, '__dict__'):
            return {key: self._convert_to_dict(value)
                    for key, value in obj.__dict__.items()
                    if not key.startswith('_')}

        # Fallback: try to convert to string
        return str(obj)

    def _parse_response(self, response) -> Dict[str, Any]:
        """
        Parse Gemini response and extract text and function calls.

        Args:
            response: Gemini GenerateContentResponse

        Returns:
            Parsed response dict
        """
        result = {
            "message": "",
            "function_calls": [],
            "finish_reason": None
        }

        try:
            # Get finish reason
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    result["finish_reason"] = str(candidate.finish_reason)

            # Extract text and function calls
            for part in response.parts:
                # Check for text
                if hasattr(part, 'text') and part.text:
                    result["message"] += part.text

                # Check for function call
                if hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    # Convert args to plain dict (handles MapComposite and other proto types)
                    args = {}
                    if hasattr(fc, 'args'):
                        args = self._convert_to_dict(fc.args)

                    function_call = {
                        "name": fc.name,
                        "args": args
                    }
                    result["function_calls"].append(function_call)

            return result

        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return {
                "message": "Error parsing response",
                "function_calls": [],
                "finish_reason": "ERROR"
            }

    def send_function_response(
        self,
        chat_session,
        function_name: str,
        function_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send function execution result back to Gemini.

        Args:
            chat_session: Active chat session
            function_name: Name of the executed function
            function_response: Result from function execution

        Returns:
            Parsed response dict
        """
        try:
            # Build function response part
            response_part = genai.protos.Part(
                function_response=genai.protos.FunctionResponse(
                    name=function_name,
                    response={"result": function_response}
                )
            )

            # Send to Gemini
            response = chat_session.send_message(response_part)

            return self._parse_response(response)

        except Exception as e:
            logger.error(f"Error sending function response: {e}")
            raise

    def simple_chat(self, message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Simple chat without function calling.

        Args:
            message: User message
            chat_history: Previous conversation history

        Returns:
            Response text
        """
        try:
            history = []
            if chat_history:
                for msg in chat_history:
                    role = "user" if msg.get("role") == "user" else "model"
                    history.append({
                        "role": role,
                        "parts": [{"text": msg.get("content", "")}]
                    })

            chat = self.model.start_chat(history=history)
            response = chat.send_message(message)

            return response.text

        except Exception as e:
            logger.error(f"Simple chat error: {e}")
            raise
