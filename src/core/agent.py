from typing import Any, Dict, List

from langgraph.graph import END, StateGraph

from src.providers import LinkedInMCPClientSync, get_llm_client
from src.tools import analyze_cv_structure, read_pdf_cv
from src.types import (
    ApplicationRequest,
    JobApplicationAgentState,
    JobResult,
    JobSearchRequest,
)


class JobApplicationAgent:
    """
    LangGraph agent that orchestrates the complete job application workflow:
    1. Read and analyze CV
    2. Search for jobs using multiple search criteria
    3. Filter jobs based on CV alignment
    4. Apply to filtered jobs
    """

    def __init__(self, server_host: str = None, server_port: int = None):
        self.server_host = server_host
        self.server_port = server_port
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for job application automation."""
        workflow = StateGraph(JobApplicationAgentState)

        # Add nodes
        workflow.add_node("read_cv_node", self.read_cv_node)
        workflow.add_node("search_jobs_node", self.search_jobs_node)
        workflow.add_node("filter_jobs_node", self.filter_jobs_node)
        workflow.add_node("apply_to_jobs_node", self.apply_to_jobs_node)

        # Define the workflow flow
        workflow.set_entry_point("read_cv_node")
        workflow.add_edge("read_cv_node", "search_jobs_node")
        workflow.add_edge("search_jobs_node", "filter_jobs_node")
        workflow.add_edge("filter_jobs_node", "apply_to_jobs_node")
        workflow.add_edge("apply_to_jobs_node", END)

        return workflow.compile()

    def read_cv_node(self, state: JobApplicationAgentState) -> Dict[str, Any]:
        """Read and analyze the CV file."""
        try:
            # Extract text from PDF
            cv_content = read_pdf_cv(state["cv_file_path"])

            # Analyze CV structure with AI
            cv_analysis = analyze_cv_structure(cv_content)

            return {
                **state,
                "cv_content": cv_content,
                "cv_analysis": cv_analysis,
                "current_status": "CV analyzed successfully",
            }

        except Exception as e:
            error_msg = f"Failed to read/analyze CV: {str(e)}"
            return {
                **state,
                "errors": state.get("errors", []) + [error_msg],
                "current_status": "CV analysis failed",
            }

    def search_jobs_node(self, state: JobApplicationAgentState) -> Dict[str, Any]:
        """Search for jobs using all provided search criteria via MCP protocol."""
        all_jobs = []
        current_index = 0

        try:
            mcp_client = LinkedInMCPClientSync(self.server_host, self.server_port)

            for search_request in state["job_searches"]:
                try:
                    # Call LinkedIn MCP search_jobs tool
                    jobs = mcp_client.search_jobs(
                        job_title=search_request["job_title"],
                        location=search_request["location"],
                        easy_apply=True,  # Always filter for easy apply
                        email=state["user_credentials"]["email"],
                        password=state["user_credentials"]["password"],
                        limit=search_request["limit"],
                    )

                    all_jobs.extend(jobs)
                    current_index += 1

                except Exception as e:
                    error_msg = f"Failed to search jobs for '{search_request['job_title']}' in '{search_request['location']}': {str(e)}"
                    state["errors"] = state.get("errors", []) + [error_msg]

            return {
                **state,
                "current_search_index": current_index,
                "all_found_jobs": all_jobs,
                "total_jobs_found": len(all_jobs),
                "current_status": f"Found {len(all_jobs)} jobs across {current_index} searches",
            }

        except Exception as e:
            error_msg = f"Job search failed: {str(e)}"
            return {
                **state,
                "errors": state.get("errors", []) + [error_msg],
                "current_status": "Job search failed",
            }

    def filter_jobs_node(self, state: JobApplicationAgentState) -> Dict[str, Any]:
        """Filter jobs based on CV alignment using AI analysis."""
        try:
            from langchain_core.prompts import ChatPromptTemplate

            # Initialize the LLM model for job filtering
            model = get_llm_client()

            # Create filtering prompt
            filter_prompt = ChatPromptTemplate.from_template(
                """
            Analyze if this job description aligns with the candidate's CV profile.

            Candidate Profile:
            - Skills: {skills}
            - Experience Years: {experience_years}
            - Previous Roles: {previous_roles}
            - Technologies: {technologies}
            - Domains: {domains}

            Job Description:
            {job_description}

            Respond with ONLY "YES" if the job aligns well with the candidate's profile, or "NO" if it doesn't.
            Consider:
            1. Skill overlap (at least 30% match)
            2. Experience level appropriateness
            3. Technology stack compatibility
            4. Domain/industry relevance
            """
            )

            filtered_jobs = []
            cv_analysis = state["cv_analysis"]

            for job in state["all_found_jobs"]:
                try:
                    # Get AI filtering decision
                    chain = filter_prompt | model
                    response = chain.invoke(
                        {
                            "skills": ", ".join(cv_analysis["skills"]),
                            "experience_years": cv_analysis["experience_years"],
                            "previous_roles": ", ".join(cv_analysis["previous_roles"]),
                            "technologies": ", ".join(cv_analysis["technologies"]),
                            "domains": ", ".join(cv_analysis["domains"]),
                            "job_description": job["job_description"][
                                :2000
                            ],  # Limit description length
                        }
                    )

                    # Extract decision from response
                    decision = (
                        response.content.strip().upper()
                        if hasattr(response, "content")
                        else str(response).strip().upper()
                    )

                    if "YES" in decision:
                        filtered_jobs.append(job)

                except Exception as e:
                    # If AI filtering fails, include job by default to be safe
                    filtered_jobs.append(job)
                    error_msg = f"Filtering failed for job {job['id_job']}, including by default: {str(e)}"
                    state["errors"] = state.get("errors", []) + [error_msg]

            return {
                **state,
                "filtered_jobs": filtered_jobs,
                "current_status": f"Filtered to {len(filtered_jobs)} relevant jobs from {len(state['all_found_jobs'])} total",
            }

        except Exception as e:
            # If filtering fails completely, use all jobs
            error_msg = f"Job filtering failed, using all jobs: {str(e)}"
            return {
                **state,
                "filtered_jobs": state["all_found_jobs"],
                "errors": state.get("errors", []) + [error_msg],
                "current_status": "Job filtering failed, proceeding with all jobs",
            }

    def apply_to_jobs_node(self, state: JobApplicationAgentState) -> Dict[str, Any]:
        """Apply to filtered jobs using the LinkedIn MCP easy apply tool."""
        try:
            # Prepare application requests with salary from original search criteria
            applications = []
            for job in state["filtered_jobs"]:
                # Find the salary from the original search request
                # For simplicity, use the first search's salary (could be enhanced)
                monthly_salary = state["job_searches"][0]["monthly_salary"]

                applications.append(
                    ApplicationRequest(
                        job_id=job["id_job"], monthly_salary=monthly_salary
                    )
                )

            if not applications:
                return {
                    **state,
                    "application_results": [],
                    "total_jobs_applied": 0,
                    "current_status": "No jobs to apply to",
                }

            # Call LinkedIn MCP easy_apply_for_jobs tool
            mcp_client = LinkedInMCPClientSync(self.server_host, self.server_port)
            application_results = mcp_client.easy_apply_for_jobs(
                applications=applications,
                cv_analysis=state["cv_analysis"],
                email=state["user_credentials"]["email"],
                password=state["user_credentials"]["password"],
            )

            successful_applications = sum(
                1 for result in application_results if result["success"]
            )

            return {
                **state,
                "application_results": application_results,
                "total_jobs_applied": successful_applications,
                "current_status": f"Applied to {successful_applications}/{len(applications)} jobs successfully",
            }

        except Exception as e:
            error_msg = f"Job application failed: {str(e)}"
            return {
                **state,
                "application_results": [],
                "total_jobs_applied": 0,
                "errors": state.get("errors", []) + [error_msg],
                "current_status": "Job application failed",
            }

    def run(
        self,
        job_searches: List[JobSearchRequest],
        cv_file_path: str,
        user_credentials: Dict[str, str],
    ) -> JobApplicationAgentState:
        """
        Execute the complete job application workflow.

        Args:
            job_searches: List of job search criteria
            cv_file_path: Path to the CV PDF file
            user_credentials: LinkedIn credentials {email, password}

        Returns:
            Final agent state with all results
        """
        initial_state = JobApplicationAgentState(
            job_searches=job_searches,
            cv_file_path=cv_file_path,
            cv_content="",
            user_credentials=user_credentials,
            current_search_index=0,
            all_found_jobs=[],
            filtered_jobs=[],
            application_results=[],
            cv_analysis={
                "skills": [],
                "experience_years": 0,
                "previous_roles": [],
                "education": [],
                "certifications": [],
                "domains": [],
                "key_achievements": [],
                "technologies": [],
            },
            conversation_history=[],
            errors=[],
            total_jobs_found=0,
            total_jobs_applied=0,
            current_status="Starting job application workflow",
        )

        # Execute the workflow
        final_state = self.graph.invoke(initial_state)
        return final_state
