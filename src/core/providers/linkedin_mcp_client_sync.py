import asyncio
from typing import List

from src.core.providers.linkedin_mcp_client import LinkedInMCPClient
from src.types import ApplicationRequest, ApplicationResult, CVAnalysis, JobResult


class LinkedInMCPClientSync:
    """
    Synchronous wrapper for the LinkedInMCPClient.
    Handles async/await internally for easier integration.
    """

    def __init__(self, server_host: str = None, server_port: int = None):
        self.server_host = server_host
        self.server_port = server_port

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
            async with LinkedInMCPClient(self.server_host, self.server_port) as client:
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
            async with LinkedInMCPClient(self.server_host, self.server_port) as client:
                return await client.easy_apply_for_jobs(
                    applications, cv_analysis, email, password
                )

        return asyncio.run(_apply())
