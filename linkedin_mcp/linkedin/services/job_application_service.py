from typing import Dict, List

from linkedin_mcp.linkedin.agents.easy_apply_agent import EasyApplyAgent
from linkedin_mcp.linkedin.graphs.job_application_graph import JobApplicationGraph
from linkedin_mcp.linkedin.interfaces.services import IJobApplicationService
from linkedin_mcp.linkedin.model.types import (
    ApplicationRequest,
    ApplicationResult,
    CVAnalysis,
)
from linkedin_mcp.linkedin.services.browser_manager_service import (
    BrowserManagerService as BrowserManager,
)
from linkedin_mcp.linkedin.services.linkedin_auth_service import LinkedInAuthService


class JobApplicationService(IJobApplicationService):
    """Service responsible for orchestrating complete LinkedIn job application workflow."""

    def __init__(self):
        # Create concrete implementations
        self.browser_manager = BrowserManager()
        self.job_application_agent = EasyApplyAgent()

        # Inject dependencies into the graph
        self.application_graph = JobApplicationGraph(
            job_application_agent=self.job_application_agent,
            browser_manager=self.browser_manager,
        )
        self.auth_service = LinkedInAuthService()

    def apply_to_jobs(
        self,
        applications: List[ApplicationRequest],
        cv_analysis: CVAnalysis,
        user_credentials: Dict[str, str],
    ) -> List[ApplicationResult]:
        """
        Apply to multiple jobs using LinkedIn's easy apply with AI-powered form handling.

        Args:
            applications: List of application requests with job_id and monthly_salary
            cv_analysis: Structured CV analysis data for AI form filling
            user_credentials: User authentication credentials (email, password)

        Returns:
            List of application results with id_job, success status, and optional error message
        """
        # Extract credentials
        email = user_credentials.get("email")
        password = user_credentials.get("password")

        if not email or not password:
            raise ValueError("Email and password are required in user_credentials")

        try:
            # Step 1: Initialize browser (use injected dependency)
            self.browser_manager.start_browser()

            # Step 2: Authenticate with LinkedIn
            auth_result = self.auth_service.authenticate(
                email, password, self.browser_manager
            )

            if not auth_result["authenticated"]:
                raise Exception(
                    f"Authentication failed: {auth_result.get('error', 'Unknown error')}"
                )

            # Step 3: Execute job application workflow with AI form handling
            raw_results = self.application_graph.execute(
                applications, cv_analysis, self.browser_manager
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
            if self.browser_manager:
                self.browser_manager.close_browser()
