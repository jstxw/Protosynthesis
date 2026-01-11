"""
Moorcheh AI Client - Python wrapper for Moorcheh REST API
Handles namespace management, document upload, search, and RAG queries
"""

import os
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class MoorchehClient:
    """Client for interacting with Moorcheh AI platform"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MOORCHEH_API_KEY")
        if not self.api_key:
            raise ValueError("MOORCHEH_API_KEY must be set in environment or passed to constructor")

        self.base_url = "https://api.moorcheh.ai/v1"
        self.headers = {
            "x-api-key": self.api_key,  # Moorcheh uses lowercase x-api-key
            "Content-Type": "application/json"
        }

    # ==================== Namespace Operations ====================

    def create_namespace(self, namespace_name: str, namespace_type: str = "text") -> Dict[str, Any]:
        """
        Create a new namespace

        Args:
            namespace_name: Name of the namespace
            namespace_type: Type of namespace ('text' or 'image')

        Returns:
            Response from API with namespace details
        """
        url = f"{self.base_url}/namespaces"
        payload = {
            "namespace_name": namespace_name,
            "type": namespace_type
        }

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def list_namespaces(self) -> List[Dict[str, Any]]:
        """List all namespaces"""
        url = f"{self.base_url}/namespaces"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get("namespaces", [])

    def delete_namespace(self, namespace_name: str) -> Dict[str, Any]:
        """Delete a namespace"""
        url = f"{self.base_url}/namespaces/{namespace_name}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    # ==================== Document Operations ====================

    def upload_documents(
        self,
        namespace_name: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Upload documents to a namespace

        Args:
            namespace_name: Name of the namespace
            documents: List of document objects with 'id', 'text', and optional 'metadata'

        Returns:
            Response with upload_id and status
        """
        url = f"{self.base_url}/upload"
        payload = {
            "namespace": namespace_name,
            "documents": documents,
            "type": "text"
        }

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def delete_documents(
        self,
        namespace_name: str,
        document_ids: List[str]
    ) -> Dict[str, Any]:
        """Delete documents from a namespace"""
        url = f"{self.base_url}/namespaces/{namespace_name}/documents"
        payload = {"document_ids": document_ids}

        response = requests.delete(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    # ==================== Search Operations ====================

    def search(
        self,
        namespace_name: str,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Semantic search across documents in a namespace

        Args:
            namespace_name: Name of the namespace to search
            query: Search query text
            top_k: Number of results to return (default 5)
            filters: Optional metadata filters

        Returns:
            Search results with matches and scores
        """
        url = f"{self.base_url}/search"
        payload = {
            "namespaces": [namespace_name],  # FIXED: plural and array format
            "query": query,
            "type": "text",
            "top_k": top_k
        }

        if filters:
            payload["filters"] = filters

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    # ==================== RAG Operations ====================

    def get_answer(
        self,
        namespace_name: str,
        query: str,
        ai_model: Optional[str] = None,
        top_k: int = 5,
        header_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Get AI-generated answer using RAG (Retrieval Augmented Generation)

        Args:
            namespace_name: Name of the namespace to query
            query: User question/query
            ai_model: AI model to use (default: claude-sonnet-4)
            top_k: Number of documents to retrieve
            header_prompt: System prompt to guide AI response
            chat_history: Previous chat messages for context

        Returns:
            Response with 'answer' text and 'sources' array
        """
        url = f"{self.base_url}/answer"

        payload = {
            "namespace": namespace_name,
            "query": query,
            "type": "text",
            "top_k": top_k
        }

        if ai_model:
            payload["aiModel"] = ai_model  # FIXED: camelCase
        else:
            payload["aiModel"] = os.getenv("MOORCHEH_AI_MODEL", "anthropic.claude-sonnet-4-20250514-v1:0")

        if header_prompt:
            payload["headerPrompt"] = header_prompt  # FIXED: camelCase

        if chat_history:
            payload["chatHistory"] = chat_history  # FIXED: camelCase

        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()


# Singleton instance
_client_instance = None

def get_moorcheh_client() -> MoorchehClient:
    """Get or create singleton Moorcheh client instance"""
    global _client_instance
    if _client_instance is None:
        _client_instance = MoorchehClient()
    return _client_instance
