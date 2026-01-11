"""
Moorcheh Ingestion Service
Handles uploading documents to Moorcheh AI namespaces
"""

import os
import json
from typing import List, Dict, Any
from .moorcheh_client import get_moorcheh_client
from dotenv import load_dotenv

load_dotenv()


class MoorchehIngestionService:
    """Service for ingesting knowledge base documents into Moorcheh"""

    def __init__(self):
        self.client = get_moorcheh_client()
        self.ns_api_schemas = os.getenv("MOORCHEH_NS_API_SCHEMAS", "workflow_api_schemas")
        self.ns_node_templates = os.getenv("MOORCHEH_NS_NODE_TEMPLATES", "workflow_node_templates")
        self.ns_instructions = os.getenv("MOORCHEH_NS_INSTRUCTIONS", "workflow_instructions")

    def ingest_api_schemas(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ingest API schema documents

        Args:
            documents: List of API schema document objects

        Returns:
            Response with upload_id and status
        """
        try:
            response = self.client.upload_documents(
                namespace_name=self.ns_api_schemas,
                documents=documents
            )
            print(f"✓ Ingested {len(documents)} API schemas to {self.ns_api_schemas}")
            return {"success": True, "upload_id": response.get("upload_id"), "count": len(documents)}
        except Exception as error:
            print(f"✗ API schema ingestion failed: {error}")
            return {"success": False, "error": str(error)}

    def ingest_node_templates(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ingest node template documents

        Args:
            documents: List of node template document objects

        Returns:
            Response with upload_id and status
        """
        try:
            response = self.client.upload_documents(
                namespace_name=self.ns_node_templates,
                documents=documents
            )
            print(f"✓ Ingested {len(documents)} node templates to {self.ns_node_templates}")
            return {"success": True, "upload_id": response.get("upload_id"), "count": len(documents)}
        except Exception as error:
            print(f"✗ Node template ingestion failed: {error}")
            return {"success": False, "error": str(error)}

    def ingest_instructions(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ingest instruction documents

        Args:
            documents: List of instruction document objects

        Returns:
            Response with upload_id and status
        """
        try:
            response = self.client.upload_documents(
                namespace_name=self.ns_instructions,
                documents=documents
            )
            print(f"✓ Ingested {len(documents)} instructions to {self.ns_instructions}")
            return {"success": True, "upload_id": response.get("upload_id"), "count": len(documents)}
        except Exception as error:
            print(f"✗ Instruction ingestion failed: {error}")
            return {"success": False, "error": str(error)}

    def ingest_from_file(self, file_path: str, namespace: str) -> Dict[str, Any]:
        """
        Ingest documents from a JSON file

        Args:
            file_path: Path to JSON file containing documents
            namespace: Target namespace name

        Returns:
            Response with upload_id and status
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)

            response = self.client.upload_documents(
                namespace_name=namespace,
                documents=documents
            )

            print(f"✓ Ingested {len(documents)} documents from {file_path} to {namespace}")
            return {"success": True, "upload_id": response.get("upload_id"), "count": len(documents)}
        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            print(f"✗ {error_msg}")
            return {"success": False, "error": error_msg}
        except json.JSONDecodeError as error:
            error_msg = f"Invalid JSON in file: {error}"
            print(f"✗ {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as error:
            error_msg = f"Ingestion failed: {error}"
            print(f"✗ {error_msg}")
            return {"success": False, "error": error_msg}

    def ingest_all_knowledge_base(self, knowledge_base_path: str) -> Dict[str, Any]:
        """
        Ingest all knowledge base files from directory

        Args:
            knowledge_base_path: Path to knowledge-base directory

        Returns:
            Summary of ingestion results
        """
        results = {
            "api_schemas": None,
            "node_templates": None,
            "instructions": None
        }

        # Ingest API schemas
        api_schemas_file = os.path.join(knowledge_base_path, "api-schemas.json")
        if os.path.exists(api_schemas_file):
            results["api_schemas"] = self.ingest_from_file(api_schemas_file, self.ns_api_schemas)
        else:
            print(f"⚠ API schemas file not found: {api_schemas_file}")

        # Ingest node templates
        node_templates_file = os.path.join(knowledge_base_path, "node-templates.json")
        if os.path.exists(node_templates_file):
            results["node_templates"] = self.ingest_from_file(node_templates_file, self.ns_node_templates)
        else:
            print(f"⚠ Node templates file not found: {node_templates_file}")

        # Ingest instructions
        instructions_file = os.path.join(knowledge_base_path, "instructions.json")
        if os.path.exists(instructions_file):
            results["instructions"] = self.ingest_from_file(instructions_file, self.ns_instructions)
        else:
            print(f"⚠ Instructions file not found: {instructions_file}")

        # Check if all succeeded
        all_success = all(
            result and result.get("success")
            for result in results.values()
            if result is not None
        )

        total_docs = sum(
            result.get("count", 0)
            for result in results.values()
            if result and result.get("success")
        )

        print(f"\n{'='*60}")
        if all_success:
            print(f"✅ Knowledge base ingestion complete! Total documents: {total_docs}")
        else:
            print(f"⚠ Knowledge base ingestion completed with some errors")
        print(f"{'='*60}\n")

        return {
            "success": all_success,
            "results": results,
            "total_documents": total_docs
        }


# Singleton instance
_ingestion_service = None

def get_ingestion_service() -> MoorchehIngestionService:
    """Get or create singleton ingestion service instance"""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = MoorchehIngestionService()
    return _ingestion_service
