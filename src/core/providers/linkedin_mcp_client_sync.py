import asyncio
from typing import Any, Dict, List, Union

from src.core.model import ApplicationRequest, ApplicationResult, CVAnalysis, JobResult
from src.core.providers.linkedin_mcp_client import LinkedInMCPClient


class LinkedInMCPClientSync:
    """
    Synchronous wrapper for the LinkedInMCPClient.
    Handles async/await internally for easier integration.
    """

    def __init__(self, server_host: str = None, server_port: int = None):
        # For MCP, we use stdio transport with server command
        # server_host and server_port are kept for backward compatibility but not used
        self.client = LinkedInMCPClient()

    def search_jobs(
        self,
        job_title: str,
        location: str,
        easy_apply: bool,
        email: str,
        password: str,
        limit: int = 50,
        trace_id: str = None,
    ) -> List[JobResult]:
        """Synchronous wrapper for search_jobs."""

        async def _search():
            async with self.client as client:
                return await client.search_jobs(
                    job_title, location, easy_apply, email, password, limit, trace_id
                )

        return asyncio.run(_search())

    def easy_apply_for_jobs(
        self,
        applications: List[ApplicationRequest],
        cv_analysis: Union[CVAnalysis, Dict[str, Any]],
        email: str,
        password: str,
        trace_id: str = None,
    ) -> List[ApplicationResult]:
        """Synchronous wrapper for easy_apply_for_jobs."""

        async def _apply():
            async with self.client as client:
                return await client.easy_apply_for_jobs(
                    applications, cv_analysis, email, password, trace_id
                )

        return asyncio.run(_apply())
