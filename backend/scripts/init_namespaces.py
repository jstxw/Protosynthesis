#!/usr/bin/env python3
"""
Initialize Moorcheh AI Namespaces
Creates the three text namespaces needed for the workflow builder:
- workflow_api_schemas: API documentation and schemas
- workflow_node_templates: Node configuration templates
- workflow_instructions: How-to guides and best practices
"""

import sys
import os

# Add parent directory to path so we can import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.integrations.moorcheh_client import get_moorcheh_client
from dotenv import load_dotenv

load_dotenv()


NAMESPACES = [
    {
        "name": os.getenv("MOORCHEH_NS_API_SCHEMAS", "workflow_api_schemas"),
        "description": "API endpoint schemas and documentation"
    },
    {
        "name": os.getenv("MOORCHEH_NS_NODE_TEMPLATES", "workflow_node_templates"),
        "description": "Node configuration templates and best practices"
    },
    {
        "name": os.getenv("MOORCHEH_NS_INSTRUCTIONS", "workflow_instructions"),
        "description": "Instructions for adding, deleting, connecting nodes"
    }
]


def initialize_namespaces():
    """Create all required namespaces"""
    client = get_moorcheh_client()

    print("🚀 Initializing Moorcheh AI namespaces...\n")

    for ns in NAMESPACES:
        try:
            result = client.create_namespace(
                namespace_name=ns["name"],
                namespace_type="text"
            )
            print(f"✓ Created namespace: {ns['name']}")
            print(f"  Description: {ns['description']}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:  # Conflict - already exists
                print(f"→ Namespace already exists: {ns['name']}")
            else:
                print(f"✗ Failed to create {ns['name']}: {e}")
                raise
        except Exception as e:
            print(f"✗ Failed to create {ns['name']}: {e}")
            raise
        print()

    print("✅ Namespace initialization complete!")
    print("\nNext steps:")
    print("1. Run 'python scripts/ingest_knowledge_base.py' to populate namespaces")
    print("2. Test queries with 'python scripts/test_moorcheh.py'")


if __name__ == "__main__":
    import requests  # Import here to avoid circular dependencies
    initialize_namespaces()
