from typing import List

from fastmcp import FastMCP

from mcp.linkedin.services import (
    ApplicationResult,
    JobApplicationService,
    JobResult,
    JobSearchService,
)
from src.core.types import ApplicationRequest, CVAnalysis

mcp = FastMCP("LinkedIn Job Applier")

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
) -> List[JobResult]:
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
    applications: List[ApplicationRequest],
    cv_analysis: CVAnalysis,
    email: str,
    password: str,
) -> List[ApplicationResult]:
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
    return job_application_service.easy_apply_for_jobs(
        applications, cv_analysis, email, password
    )


if __name__ == "__main__":
    mcp.run()
