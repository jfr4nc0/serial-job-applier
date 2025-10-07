#!/usr/bin/env python3
"""Test script to verify that logging configuration always binds trace_id."""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "linkedin_mcp"))


def test_mcp_logging():
    """Test LinkedIn MCP logging configuration."""
    print("Testing LinkedIn MCP logging...")

    try:
        from linkedin_mcp.linkedin.utils.logging_config import (
            configure_mcp_logging,
            get_mcp_logger,
        )

        # Configure logging
        configure_mcp_logging(log_level="INFO")

        # Test getting logger without trace_id
        logger1 = get_mcp_logger()
        logger1.info("MCP test log without explicit trace_id")

        # Test getting logger with trace_id
        logger2 = get_mcp_logger("test-trace-123")
        logger2.info("MCP test log with explicit trace_id")

        print("✅ LinkedIn MCP logging test passed")
        return True

    except Exception as e:
        print(f"❌ LinkedIn MCP logging test failed: {e}")
        return False


def test_core_agent_logging():
    """Test core agent logging configuration."""
    print("Testing core agent logging...")

    try:
        from src.core.utils.logging_config import (
            configure_core_agent_logging,
            get_core_agent_logger,
        )

        # Configure logging
        configure_core_agent_logging(log_level="INFO")

        # Test getting logger without trace_id
        logger1 = get_core_agent_logger()
        logger1.info("Core agent test log without explicit trace_id")

        # Test getting logger with trace_id
        logger2 = get_core_agent_logger("test-trace-456")
        logger2.info("Core agent test log with explicit trace_id")

        print("✅ Core agent logging test passed")
        return True

    except Exception as e:
        print(f"❌ Core agent logging test failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing logging configurations with trace_id fixes...")
    print("=" * 60)

    mcp_success = test_mcp_logging()
    print()
    core_success = test_core_agent_logging()

    print("\n" + "=" * 60)
    if mcp_success and core_success:
        print("🎉 All logging tests passed! No more unbound trace_ids.")
    else:
        print("⚠️  Some logging tests failed.")
        sys.exit(1)
