#!/usr/bin/env python3
"""
Test Moorcheh AI Integration
Tests all 7 query patterns to verify the AI assistant works correctly
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.integrations.ai_service import get_ai_service
from dotenv import load_dotenv

load_dotenv()


def test_all_query_patterns():
    """Test all AI service query patterns"""
    ai_service = get_ai_service()

    print("="*70)
    print("Testing Moorcheh AI Integration - All Query Patterns")
    print("="*70)
    print()

    # Test 1: Node Recommendations
    print("📋 Test 1: Node Recommendations")
    print("-" * 70)
    try:
        recommendations = ai_service.get_node_recommendations(
            current_node_type="stripe_payment",
            current_output_fields=["payment_id", "customer_email", "amount"],
            user_intent="send a receipt email"
        )
        print(f"✓ Got {len(recommendations)} recommendations")
        if recommendations:
            print(f"  Example: {recommendations[0]}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    print()

    # Test 2: Connection Validation
    print("🔗 Test 2: Connection Validation")
    print("-" * 70)
    try:
        validation = ai_service.validate_and_suggest_connection(
            source_node_id="stripe_payment",
            source_output_field="customer_email",
            target_node_id="sendgrid_email",
            target_input_field="recipient"
        )
        print(f"✓ Validation result: {validation}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    print()

    # Test 3: Instructions
    print("📖 Test 3: Get Instructions")
    print("-" * 70)
    try:
        instructions = ai_service.get_instructions(
            "How do I connect two nodes together?"
        )
        print(f"✓ Answer (first 200 chars): {instructions['answer'][:200]}...")
        print(f"  Confidence: {instructions['confidence']:.2f}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    print()

    # Test 4: API Schema Lookup
    print("🔍 Test 4: API Schema Lookup")
    print("-" * 70)
    try:
        schema = ai_service.get_api_schema_info(
            provider="stripe",
            endpoint="/v1/payment_intents",
            specific_question="What parameters are required?"
        )
        print(f"✓ Schema info (first 200 chars): {schema['answer'][:200]}...")
        print(f"  Confidence: {schema['confidence']:.2f}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    print()

    # Test 5: Auto-Map Fields
    print("🗺️ Test 5: Auto-Map Fields")
    print("-" * 70)
    try:
        mappings = ai_service.auto_map_fields(
            source_fields=[
                {"name": "customer_email", "type": "string"},
                {"name": "payment_amount", "type": "number"}
            ],
            target_fields=[
                {"name": "recipient", "type": "string", "required": True},
                {"name": "amount", "type": "number", "required": True}
            ]
        )
        print(f"✓ Got {len(mappings)} field mappings")
        if mappings:
            print(f"  Example: {mappings[0]}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    print()

    # Test 6: Chat
    print("💬 Test 6: Chat Assistant")
    print("-" * 70)
    try:
        chat_response = ai_service.chat(
            message="What's the best way to handle errors in my workflow?",
            chat_history=[],
            workflow_context={"currentNodes": ["stripe_payment", "sendgrid_email"]}
        )
        print(f"✓ Chat response (first 200 chars): {chat_response[:200]}...")
    except Exception as e:
        print(f"✗ Failed: {e}")
    print()

    # Test 7: Troubleshooting
    print("🔧 Test 7: Troubleshooting & Best Practices")
    print("-" * 70)
    try:
        troubleshoot = ai_service.get_best_practices_or_troubleshoot(
            current_issue="My Stripe payments are failing",
            node_types=["stripe_payment", "slack_webhook"]
        )
        print(f"✓ Troubleshooting advice (first 200 chars): {troubleshoot['answer'][:200]}...")
        print(f"  Confidence: {troubleshoot['confidence']:.2f}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    print()

    print("="*70)
    print("✅ All tests completed!")
    print("="*70)


if __name__ == "__main__":
    test_all_query_patterns()
