"""
LinkedIn MCP Server - Main entry point
Uses standard TCP implementation for MCP protocol
"""

import os

from fastmcp import FastMCP

from linkedin_mcp.linkedin.model.types import (
    ApplicationRequest,
    ApplicationResult,
    CVAnalysis,
    JobResult,
)
from linkedin_mcp.linkedin.services.job_application_service import JobApplicationService
from linkedin_mcp.linkedin.services.job_search_service import JobSearchService
from linkedin_mcp.linkedin.utils.logging_config import (
    configure_mcp_logging,
    log_mcp_server_startup,
    log_mcp_tool_registration,
)

# Configure logging for LinkedIn MCP server
configure_mcp_logging()

mcp = FastMCP("LinkedIn Job Applier")

# Log server startup
log_mcp_server_startup(
    {
        "name": "LinkedIn Job Applier",
        "version": "1.16.0",
        "transport": "stdio",
        "fastmcp_version": "2.12.4",
        "mcp_sdk_version": "1.16.0",
    }
)

# Initialize services
job_search_service = JobSearchService()
job_application_service = JobApplicationService()


@mcp.tool
def search_jobs(
    job_title: str,
    location: str,
    easy_apply: bool,
    email: str,
    password: str,
    limit: int = 50,
) -> list[JobResult]:
    """
    Search for jobs on LinkedIn based on title, location, and easy apply filter.
    Handles authentication automatically and paginates through results.

    Args:
        job_title: The job title to search for
        location: The location to search in
        easy_apply: Whether to filter for easy apply jobs only
        email: LinkedIn email for authentication
        password: LinkedIn password for authentication
        limit: Maximum number of jobs to collect (default: 50)

    Returns:
        List of jobs with id_job and job_description
    """
    return job_search_service.search_jobs(
        job_title, location, easy_apply, email, password, limit
    )


@mcp.tool
def easy_apply_for_jobs(
    applications: list[ApplicationRequest],
    cv_analysis: CVAnalysis,
    email: str,
    password: str,
) -> list[ApplicationResult]:
    """
    Apply to multiple jobs using LinkedIn's easy apply feature with AI-powered form handling.
    Handles authentication automatically and uses CV analysis to answer form questions intelligently.

    Args:
        applications: List of application requests with job_id and monthly_salary
        cv_analysis: Structured CV analysis data for AI form filling
        email: LinkedIn email for authentication
        password: LinkedIn password for authentication

    Returns:
        List of application results with id_job, success status, and optional error message
    """
    return job_application_service.apply_to_jobs(
        applications, cv_analysis, {"email": email, "password": password}
    )


# Log registered tools
log_mcp_tool_registration(
    [
        {"name": "search_jobs", "description": "Search LinkedIn jobs with filters"},
        {
            "name": "easy_apply_for_jobs",
            "description": "Apply to jobs using Easy Apply with AI form handling",
        },
    ]
)


if __name__ == "__main__":
    # For FastMCP, stdio is the standard MCP transport
    # TCP/HTTP servers are typically for development/testing
    print("Starting LinkedIn MCP Server with stdio transport")
    mcp.run()
