import asyncio
import os
from typing import Any, Dict, List, Union

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from src.core.model import ApplicationRequest, ApplicationResult, CVAnalysis, JobResult

# Load environment variables
load_dotenv()


class LinkedInMCPClient:
    """
    Official FastMCP client for communicating with the LinkedIn MCP server.
    Uses FastMCP's StdioTransport for protocol communication over stdio.
    The client manages the LinkedIn MCP server lifecycle as a subprocess.
    """

    def __init__(self, keep_alive: bool = True):
        # Prepare environment variables needed by the LinkedIn server
        env = {
            "LINKEDIN_EMAIL": os.getenv("LINKEDIN_EMAIL"),
            "LINKEDIN_PASSWORD": os.getenv("LINKEDIN_PASSWORD"),
            "LINKEDIN_MCP_LOG_LEVEL": os.getenv("LINKEDIN_MCP_LOG_LEVEL", "INFO"),
            "LINKEDIN_MCP_LOG_FILE": os.getenv("LINKEDIN_MCP_LOG_FILE"),
        }

        # Filter out None values
        env = {k: v for k, v in env.items() if v is not None}

        command_parts = [
            "poetry",
            "run",
            "python",
            "-m",
            "linkedin_mcp.linkedin.linkedin_server",
        ]
        command = command_parts[0] if command_parts else "python"
        args = command_parts[1:] if len(command_parts) > 1 else []

        self.transport = StdioTransport(
            command=command, args=args, env=env, keep_alive=keep_alive
        )

        self.client = Client(self.transport)

    async def __aenter__(self):
        # FastMCP client handles the connection automatically
        await self.client.__aenter__()
        return self

    async def list_tools(self):
        """
        Discover available tools on the LinkedIn MCP server.

        Returns:
            List of available tools with their metadata
        """
        return await self.client.list_tools()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool using the FastMCP Client.

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Tool arguments

        Returns:
            Tool result data

        Raises:
            Exception: If the MCP call fails
        """
        try:
            # Call the tool using FastMCP Client with manual error checking
            result = await self.client.call_tool(
                tool_name, arguments, raise_on_error=False
            )

            # Check if the tool execution failed
            if result.is_error:
                error_content = (
                    result.content[0].text if result.content else "Unknown error"
                )
                raise Exception(f"Tool '{tool_name}' execution failed: {error_content}")

            # FastMCP returns structured data directly
            return result.data

        except Exception as e:
            raise Exception(f"FastMCP tool call failed for '{tool_name}': {str(e)}")

    async def search_jobs(
        self,
        job_title: str,
        location: str,
        easy_apply: bool,
        email: str,
        password: str,
        limit: int = 50,
        trace_id: str = None,
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

        # Add trace_id if provided
        if trace_id:
            arguments["trace_id"] = trace_id

        result = await self._call_tool("search_jobs", arguments)

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
        trace_id: str = None,
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

        # Add trace_id if provided
        if trace_id:
            arguments["trace_id"] = trace_id

        result = await self._call_tool("easy_apply_for_jobs", arguments)

        # Convert result to ApplicationResult format
        return [
            ApplicationResult(
                id_job=app_result["id_job"],
                success=app_result["success"],
                error=app_result.get("error"),
            )
            for app_result in result
        ]
