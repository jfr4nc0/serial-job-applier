import asyncio
import os
from typing import Any, Dict, List

from mcp import ClientSession
from mcp.client.tcp import tcp_client

from src.types import ApplicationRequest, ApplicationResult, CVAnalysis, JobResult


class LinkedInMCPClient:
    """
    Official MCP client for communicating with the LinkedIn MCP server.
    Uses the proper MCP SDK for protocol communication over TCP.
    """

    def __init__(self, server_host: str = None, server_port: int = None):
        self.server_host = server_host or os.getenv(
            "MCP_SERVER_HOST", "linkedin-mcp-server"
        )
        self.server_port = server_port or int(os.getenv("MCP_SERVER_PORT", "3000"))

    async def __aenter__(self):
        # Create TCP client and session
        self.tcp_client = tcp_client(host=self.server_host, port=self.server_port)
        self.read_stream, self.write_stream = await self.tcp_client.__aenter__()

        # Initialize session
        self.session = ClientSession(self.read_stream, self.write_stream)
        await self.session.__aenter__()

        # Initialize the server
        await self.session.initialize()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, "session"):
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
        if hasattr(self, "tcp_client"):
            await self.tcp_client.__aexit__(exc_type, exc_val, exc_tb)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
        if hasattr(self, "stdio_client"):
            await self.stdio_client.__aexit__(exc_type, exc_val, exc_tb)

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool using the official MCP SDK.

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Tool arguments

        Returns:
            Tool result data

        Raises:
            Exception: If the MCP call fails
        """
        try:
            if not self.session:
                raise Exception("MCP session not initialized")

            # Call the tool using MCP SDK
            result = await self.session.call_tool(tool_name, arguments)

            # Extract content from MCP result
            if hasattr(result, "content") and result.content:
                # Handle different content types
                if len(result.content) == 1 and hasattr(result.content[0], "text"):
                    return result.content[0].text
                else:
                    # Return the raw content for complex responses
                    return result.content
            else:
                raise Exception(f"No content returned from tool '{tool_name}'")

        except Exception as e:
            raise Exception(f"MCP tool call failed for '{tool_name}': {str(e)}")

    async def search_jobs(
        self,
        job_title: str,
        location: str,
        easy_apply: bool,
        email: str,
        password: str,
        limit: int = 50,
    ) -> List[JobResult]:
        """
        Search for jobs on LinkedIn via MCP protocol.

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
        arguments = {
            "job_title": job_title,
            "location": location,
            "easy_apply": easy_apply,
            "email": email,
            "password": password,
            "limit": limit,
        }

        result = await self._call_tool("search_jobs", arguments)

        # Parse JSON result if it's a string
        if isinstance(result, str):
            import json

            result = json.loads(result)

        # Convert result to JobResult format
        return [
            JobResult(id_job=job["id_job"], job_description=job["job_description"])
            for job in result
        ]

    async def easy_apply_for_jobs(
        self,
        applications: List[ApplicationRequest],
        cv_analysis: CVAnalysis,
        email: str,
        password: str,
    ) -> List[ApplicationResult]:
        """
        Apply to multiple jobs using LinkedIn's easy apply via MCP protocol.

        Args:
            applications: List of application requests with job_id and monthly_salary
            cv_analysis: Structured CV analysis data for AI form filling
            email: LinkedIn email for authentication
            password: LinkedIn password for authentication

        Returns:
            List of application results with id_job, success status, and optional error message
        """
        # Convert TypedDict to regular dict for JSON serialization
        applications_dict = [
            {"job_id": app["job_id"], "monthly_salary": app["monthly_salary"]}
            for app in applications
        ]

        cv_analysis_dict = {
            "skills": cv_analysis["skills"],
            "experience_years": cv_analysis["experience_years"],
            "previous_roles": cv_analysis["previous_roles"],
            "education": cv_analysis["education"],
            "certifications": cv_analysis["certifications"],
            "domains": cv_analysis["domains"],
            "key_achievements": cv_analysis["key_achievements"],
            "technologies": cv_analysis["technologies"],
        }

        arguments = {
            "applications": applications_dict,
            "cv_analysis": cv_analysis_dict,
            "email": email,
            "password": password,
        }

        result = await self._call_tool("easy_apply_for_jobs", arguments)

        # Parse JSON result if it's a string
        if isinstance(result, str):
            import json

            result = json.loads(result)

        # Convert result to ApplicationResult format
        return [
            ApplicationResult(
                id_job=app_result["id_job"],
                success=app_result["success"],
                error=app_result.get("error"),
            )
            for app_result in result
        ]
