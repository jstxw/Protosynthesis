"""
Debug script to test Moorcheh API with minimal payload
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.integrations.moorcheh_client import MoorchehClient

def test_minimal_query():
    """Test with the simplest possible query"""
    client = MoorchehClient()

    print("=" * 60)
    print("Testing Minimal Query")
    print("=" * 60)

    try:
        result = client.get_answer(
            namespace_name="workflow_instructions",
            query="How do I add a node?",
            top_k=5
        )
        print("✓ SUCCESS!")
        print(f"Answer: {result.get('answer', 'No answer')[:200]}...")
    except Exception as e:
        print(f"✗ FAILED: {e}")

if __name__ == "__main__":
    test_minimal_query()
