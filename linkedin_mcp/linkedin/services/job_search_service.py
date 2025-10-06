from typing import List

from linkedin_mcp.linkedin.graphs.job_search_graph import JobSearchGraph
from linkedin_mcp.linkedin.services.browser_manager_service import (
    BrowserManagerService as BrowserManager,
)
from linkedin_mcp.linkedin.services.linkedin_auth_service import LinkedInAuthService
from linkedin_mcp.types import JobResult


class JobSearchService:
    """Service responsible for orchestrating complete LinkedIn job search workflow."""

    def __init__(self):
        self.search_graph = JobSearchGraph()
        self.auth_service = LinkedInAuthService()

    def search_jobs(
        self,
        job_title: str,
        location: str,
        easy_apply: bool,
        email: str,
        password: str,
        limit: int = 50,
    ) -> List[JobResult]:
        """
        Search for jobs on LinkedIn - handles authentication and search workflow.

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
        browser_manager = None

        try:
            # Step 1: Initialize browser
            browser_manager = BrowserManager()
            browser_manager.start_browser()

            # Step 2: Authenticate with LinkedIn
            auth_result = self.auth_service.authenticate(
                email, password, browser_manager
            )

            if not auth_result["authenticated"]:
                raise Exception(
                    f"Authentication failed: {auth_result.get('error', 'Unknown error')}"
                )

            # Step 3: Execute job search workflow
            raw_results = self.search_graph.execute(
                job_title, location, easy_apply, browser_manager, limit
            )

            # Step 4: Convert to JobResult format
            return [
                JobResult(id_job=job["id"], job_description=job["description"])
                for job in raw_results
            ]

        except Exception as e:
            # Log error or handle as needed
            raise Exception(f"Job search failed: {str(e)}")

        finally:
            # Step 5: Cleanup browser resources
            if browser_manager:
                browser_manager.close_browser()
