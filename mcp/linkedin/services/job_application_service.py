from typing import List, Optional, TypedDict

from mcp.linkedin.services.browser_manager import BrowserManager
from mcp.linkedin.services.job_application_graph import JobApplicationGraph
from mcp.linkedin.services.linkedin_auth_service import LinkedInAuthService
from src.core.types import ApplicationRequest, CVAnalysis


class ApplicationResult(TypedDict):
    id_job: int
    success: bool
    error: Optional[str]


class JobApplicationService:
    """Service responsible for orchestrating complete LinkedIn job application workflow."""

    def __init__(self):
        self.application_graph = JobApplicationGraph()
        self.auth_service = LinkedInAuthService()

    def easy_apply_for_jobs(
        self,
        applications: List[ApplicationRequest],
        cv_analysis: CVAnalysis,
        email: str,
        password: str,
    ) -> List[ApplicationResult]:
        """
        Apply to multiple jobs using LinkedIn's easy apply with AI-powered form handling.

        Args:
            applications: List of application requests with job_id and monthly_salary
            cv_analysis: Structured CV analysis data for AI form filling
            email: LinkedIn email for authentication
            password: LinkedIn password for authentication

        Returns:
            List of application results with id_job, success status, and optional error message
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

            # Step 3: Execute job application workflow with AI form handling
            raw_results = self.application_graph.execute(
                applications, cv_analysis, browser_manager
            )

            # Step 4: Convert to ApplicationResult format
            return [
                ApplicationResult(
                    id_job=result["job_id"],
                    success=result["success"],
                    error=result.get("error"),
                )
                for result in raw_results
            ]

        except Exception as e:
            # Return error results for all jobs
            return [
                ApplicationResult(
                    id_job=application["job_id"],
                    success=False,
                    error=f"Application workflow failed: {str(e)}",
                )
                for application in applications
            ]

        finally:
            # Step 5: Cleanup browser resources
            if browser_manager:
                browser_manager.close_browser()
