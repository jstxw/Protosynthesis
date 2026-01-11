#!/usr/bin/env python3
"""
Ingest Knowledge Base into Moorcheh AI
Uploads all knowledge base documents to their respective namespaces
"""

import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.integrations.moorcheh_ingestion_service import get_ingestion_service
from dotenv import load_dotenv

load_dotenv()


def main():
    """Main ingestion function"""
    print("🚀 Starting knowledge base ingestion to Moorcheh AI...\n")

    # Get knowledge base path
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    knowledge_base_path = os.path.join(backend_dir, "knowledge-base")

    print(f"📁 Knowledge base path: {knowledge_base_path}\n")

    # Verify directory exists
    if not os.path.exists(knowledge_base_path):
        print(f"✗ Knowledge base directory not found: {knowledge_base_path}")
        print("Please run this script from the backend directory")
        sys.exit(1)

    # Get ingestion service
    ingestion_service = get_ingestion_service()

    # Ingest all files
    results = ingestion_service.ingest_all_knowledge_base(knowledge_base_path)

    # Wait for indexing to complete
    if results["success"]:
        print("⏳ Waiting for Moorcheh to index documents (this may take a few seconds)...")
        time.sleep(5)
        print("✅ Indexing should be complete - your AI assistant is ready!\n")

        print("Next steps:")
        print("1. Test queries with: python scripts/test_moorcheh.py")
        print("2. Start your Flask server to use AI features")
        print("3. Try asking questions in the frontend AI Assistant panel")
    else:
        print("⚠ Some errors occurred during ingestion. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
