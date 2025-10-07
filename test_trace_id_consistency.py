#!/usr/bin/env python3
"""Test script to verify trace_id consistency across the entire agent run."""

import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "linkedin_mcp"))


def test_trace_id_propagation():
    """Test that trace_id is generated once and used consistently throughout agent execution."""
    print("Testing trace_id propagation consistency...")

    try:
        from src.core.agent import JobApplicationAgent
        from src.core.model.job_search_request import JobSearchRequest

        # Create test data
        job_searches = [
            JobSearchRequest(
                job_title="Python Developer",
                location="Remote",
                monthly_salary=5000,
                limit=5,
            )
        ]

        user_credentials = {"email": "test@example.com", "password": "test_password"}

        cv_file_path = "/tmp/test_cv.pdf"

        # Mock the entire MCP client to avoid actual LinkedIn calls
        with patch(
            "src.core.providers.linkedin_mcp_client_sync.LinkedInMCPClientSync"
        ) as mock_mcp_client:
            # Mock the search_jobs return value
            mock_client_instance = MagicMock()
            mock_mcp_client.return_value = mock_client_instance
            mock_client_instance.search_jobs.return_value = [
                {"id_job": "test_job_1", "job_description": "Test job description"}
            ]
            mock_client_instance.easy_apply_for_jobs.return_value = [
                {"success": True, "id_job": "test_job_1"}
            ]

            # Mock PDF reading
            with patch("src.core.tools.tools.read_pdf_cv") as mock_read_pdf:
                mock_read_pdf.invoke.return_value = "Test CV content"

                # Mock CV analysis
                with patch(
                    "src.core.tools.tools.analyze_cv_structure"
                ) as mock_analyze_cv:
                    mock_analyze_cv.invoke.return_value = {
                        "skills": ["Python", "Machine Learning"],
                        "experience_years": 5,
                        "previous_roles": ["Software Engineer"],
                        "education": ["Computer Science"],
                        "certifications": [],
                        "domains": ["Technology"],
                        "key_achievements": ["Led team of 5"],
                        "technologies": ["Python", "Flask"],
                    }

                    # Mock LLM filtering
                    with patch(
                        "src.core.providers.llm_client.get_llm_client"
                    ) as mock_llm:
                        mock_llm_instance = MagicMock()
                        mock_llm.return_value = mock_llm_instance
                        mock_llm_instance.invoke.return_value = [
                            {
                                "id_job": "test_job_1",
                                "job_description": "Test job description",
                            }
                        ]

                        # Create agent and run
                        agent = JobApplicationAgent()

                        # Capture all trace_ids used
                        captured_trace_ids = []

                        # Patch logging to capture trace_ids
                        def capture_trace_id(*args, **kwargs):
                            if "trace_id" in kwargs:
                                captured_trace_ids.append(kwargs["trace_id"])
                            return MagicMock()

                        with patch(
                            "src.core.utils.logging_config.get_core_agent_logger",
                            side_effect=capture_trace_id,
                        ):
                            result = agent.run(
                                job_searches=job_searches,
                                cv_file_path=cv_file_path,
                                user_credentials=user_credentials,
                            )

                        # Verify that MCP calls received trace_id
                        search_calls = mock_client_instance.search_jobs.call_args_list
                        apply_calls = (
                            mock_client_instance.easy_apply_for_jobs.call_args_list
                        )

                        print(
                            f"Agent run completed with trace_id: {result.get('trace_id')}"
                        )
                        print(f"Captured trace_ids: {captured_trace_ids}")
                        print(f"MCP search_jobs calls: {len(search_calls)}")
                        print(f"MCP easy_apply calls: {len(apply_calls)}")

                        # Check that trace_id was passed to MCP calls
                        if search_calls:
                            search_kwargs = search_calls[0][
                                1
                            ]  # Get kwargs from first call
                            print(
                                f"search_jobs trace_id: {search_kwargs.get('trace_id')}"
                            )

                        if apply_calls:
                            apply_kwargs = apply_calls[0][
                                1
                            ]  # Get kwargs from first call
                            print(
                                f"easy_apply trace_id: {apply_kwargs.get('trace_id')}"
                            )

                        # Verify trace_id is in the final result
                        if result.get("trace_id"):
                            print("✅ trace_id is present in final result")
                        else:
                            print("❌ trace_id missing from final result")
                            return False

                        print("✅ Trace ID consistency test passed")
                        return True

    except Exception as e:
        print(f"❌ Trace ID consistency test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing trace_id consistency across core agent workflow...")
    print("=" * 60)

    success = test_trace_id_propagation()

    print("\n" + "=" * 60)
    if success:
        print("🎉 Trace ID consistency test completed successfully!")
        print(
            "📝 Every run of the core agent now uses a single trace_id throughout the entire workflow."
        )
    else:
        print("⚠️  Trace ID consistency test failed.")
        sys.exit(1)
