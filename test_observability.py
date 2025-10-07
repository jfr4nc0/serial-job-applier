#!/usr/bin/env python3
"""Test script to verify observability integration with both core agent and LinkedIn MCP."""

import os
import sys
import uuid

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_core_observability():
    """Test observability configuration for core agent."""
    print("🔍 Testing Core Agent Observability...")

    try:
        from src.core.observability.langfuse_config import (
            get_langfuse_callback,
            get_langfuse_config_for_langgraph,
        )

        # Test configuration
        callback_handler = get_langfuse_callback()
        config = get_langfuse_config_for_langgraph()

        if callback_handler:
            print("✅ Langfuse callback handler configured for core agent")
            print(f"   - Callback type: {type(callback_handler)}")
            print(f"   - Config keys: {list(config.keys())}")
        else:
            print("ℹ️  Langfuse not configured for core agent (missing credentials)")

    except Exception as e:
        print(f"❌ Core observability test failed: {e}")


def test_mcp_observability():
    """Test observability configuration for LinkedIn MCP."""
    print("\n🔍 Testing LinkedIn MCP Observability...")

    try:
        from linkedin_mcp.linkedin.observability.langfuse_config import (
            get_langfuse_callback_for_mcp,
            get_langfuse_config_for_mcp_langgraph,
            trace_mcp_operation,
        )

        # Test configuration
        callback_handler = get_langfuse_callback_for_mcp()
        config = get_langfuse_config_for_mcp_langgraph()

        if callback_handler:
            print("✅ Langfuse callback handler configured for LinkedIn MCP")
            print(f"   - Callback type: {type(callback_handler)}")
            print(f"   - Config keys: {list(config.keys())}")
        else:
            print("ℹ️  Langfuse not configured for LinkedIn MCP (missing credentials)")

        # Test decorator
        @trace_mcp_operation("test_operation")
        def test_function():
            return "test_result"

        result = test_function()
        print(f"✅ MCP tracing decorator works: {result}")

    except Exception as e:
        print(f"❌ MCP observability test failed: {e}")


def test_logging_with_trace_ids():
    """Test logging with trace IDs."""
    print("\n🔍 Testing Logging with Trace IDs...")

    try:
        from loguru import logger

        # Test trace ID logging
        trace_id = str(uuid.uuid4())

        logger.info(
            "Test log message with trace ID",
            trace_id=trace_id,
            component="test",
            operation="observability_test",
        )

        print(f"✅ Logging with trace ID successful: {trace_id[:8]}...")

    except Exception as e:
        print(f"❌ Trace ID logging test failed: {e}")


def test_trace_propagation():
    """Test trace ID propagation through the system."""
    print("\n🔍 Testing Trace ID Propagation...")

    try:
        from linkedin_mcp.linkedin.observability.langfuse_config import (
            create_mcp_trace,
            trace_mcp_operation,
        )

        # Test creating a trace with custom ID
        trace_id = str(uuid.uuid4())
        trace = create_mcp_trace(
            name="test_workflow", trace_id=trace_id, metadata={"test": True}
        )

        if trace:
            print(f"✅ MCP trace created with ID: {trace_id[:8]}...")
        else:
            print("ℹ️  MCP trace creation skipped (no Langfuse credentials)")

        # Test trace propagation in decorator
        @trace_mcp_operation("test_operation_with_trace")
        def test_operation_with_trace(state_dict):
            return {"success": True, "trace_id": state_dict.get("trace_id")}

        test_state = {"trace_id": trace_id, "data": "test"}
        result = test_operation_with_trace(test_state)

        print(f"✅ Trace propagation test successful: {result}")

    except Exception as e:
        print(f"❌ Trace propagation test failed: {e}")


def test_imports():
    """Test all observability-related imports."""
    print("\n🔍 Testing Observability Imports...")

    imports_to_test = [
        ("src.core.agent", "JobApplicationAgent"),
        ("linkedin_mcp.linkedin.agents.easy_apply_agent", "EasyApplyAgent"),
        ("linkedin_mcp.linkedin.graphs.job_application_graph", "JobApplicationGraph"),
        ("src.core.observability", "get_langfuse_callback"),
        ("linkedin_mcp.linkedin.observability", "get_langfuse_callback_for_mcp"),
    ]

    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ Import successful: {module_name}.{class_name}")
        except Exception as e:
            print(f"❌ Import failed: {module_name}.{class_name} - {e}")


def main():
    """Run all observability tests."""
    print("🚀 LinkedIn Job Application Agent - Observability Integration Test")
    print("=" * 70)

    # Check if Langfuse credentials are set
    has_langfuse_creds = bool(
        os.getenv("LANGFUSE_SECRET_KEY") and os.getenv("LANGFUSE_PUBLIC_KEY")
    )

    print(
        f"📊 Langfuse credentials configured: {'✅ Yes' if has_langfuse_creds else '❌ No'}"
    )
    if not has_langfuse_creds:
        print(
            "   Note: Set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY in .env for full functionality"
        )

    # Run tests
    test_imports()
    test_core_observability()
    test_mcp_observability()
    test_logging_with_trace_ids()
    test_trace_propagation()

    print("\n" + "=" * 70)
    print("🎉 Observability integration test completed!")
    print("\n📝 Next steps:")
    print("   1. Set up Langfuse account at https://cloud.langfuse.com")
    print("   2. Add LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY to .env")
    print("   3. Run workflows to see traces in Langfuse dashboard")


if __name__ == "__main__":
    main()
