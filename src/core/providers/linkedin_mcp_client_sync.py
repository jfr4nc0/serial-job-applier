import asyncio
from typing import List

from src.core.model import ApplicationRequest, ApplicationResult, CVAnalysis, JobResult
from src.core.providers.linkedin_mcp_client import LinkedInMCPClient


class LinkedInMCPClientSync:
    """
    Synchronous wrapper for the LinkedInMCPClient.
    Handles async/await internally for easier integration.
    """

    def __init__(self, server_host: str = None, server_port: int = None):
        # For backward compatibility, convert host/port to command
        # In a real implementation, you might want to keep TCP support
        # For now, we'll use stdio with a default command
        server_command = "python -m linkedin_mcp.linkedin.linkedin_server"
        self.client = LinkedInMCPClient(server_command=server_command)

    def search_jobs(
        self,
        job_title: str,
        location: str,
        easy_apply: bool,
        email: str,
        password: str,
        limit: int = 50,
    ) -> List[JobResult]:
        """Synchronous wrapper for search_jobs."""

        async def _search():
            async with self.client as client:
                return await client.search_jobs(
                    job_title, location, easy_apply, email, password, limit
                )

        return asyncio.run(_search())

    def easy_apply_for_jobs(
        self,
        applications: List[ApplicationRequest],
        cv_analysis: CVAnalysis,
        email: str,
        password: str,
    ) -> List[ApplicationResult]:
        """Synchronous wrapper for easy_apply_for_jobs."""

        async def _apply():
            async with self.client as client:
                return await client.easy_apply_for_jobs(
                    applications, cv_analysis, email, password
                )

        return asyncio.run(_apply())
