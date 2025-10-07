import uuid
from typing import Any, Dict, List

from langgraph.graph import END, StateGraph
from loguru import logger

from src.core.model.application_request import ApplicationRequest
from src.core.model.job_application_agent_state import JobApplicationAgentState
from src.core.model.job_result import JobResult
from src.core.model.job_search_request import JobSearchRequest
from src.core.observability.langfuse_config import get_langfuse_config_for_langgraph
from src.core.providers.linkedin_mcp_client_sync import LinkedInMCPClientSync
from src.core.providers.llm_client import get_llm_client
from src.core.tools.tools import analyze_cv_structure, read_pdf_cv
from src.core.utils.logging_config import get_core_agent_logger


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
        workflow.add_node("search_jobs_node", self.search_jobs_node)
        workflow.add_node("filter_jobs_node", self.filter_jobs_node)
        workflow.add_node("apply_to_jobs_node", self.apply_to_jobs_node)

        # Define the workflow flow
        workflow.set_entry_point("search_jobs_node")
        workflow.add_edge("search_jobs_node", "filter_jobs_node")
        workflow.add_edge("filter_jobs_node", "apply_to_jobs_node")
        workflow.add_edge("apply_to_jobs_node", END)

        # Compile the graph - Langfuse observability is now handled during invoke
        # Use bound logger for setup messages
        setup_logger = logger.bind(trace_id="setup")
        setup_logger.info("LangGraph compiled - observability handled during invoke")
        return workflow.compile()

    def search_jobs_node(self, state: JobApplicationAgentState) -> Dict[str, Any]:
        """Search for jobs using all provided search criteria via MCP protocol."""
        trace_id = state.get("trace_id", str(uuid.uuid4()))
        agent_logger = get_core_agent_logger(trace_id)

        all_jobs = []
        current_index = 0

        try:
            agent_logger.info(
                "Starting job search", searches_count=len(state["job_searches"])
            )
            mcp_client = LinkedInMCPClientSync(self.server_host, self.server_port)

            for search_request in state["job_searches"]:
                try:
                    # Call LinkedIn MCP search_jobs tool with trace_id
                    agent_logger.info(
                        "Searching jobs",
                        job_title=search_request["job_title"],
                        location=search_request["location"],
                    )
                    jobs = mcp_client.search_jobs(
                        job_title=search_request["job_title"],
                        location=search_request["location"],
                        easy_apply=True,  # Always filter for easy apply
                        email=state["user_credentials"]["email"],
                        password=state["user_credentials"]["password"],
                        limit=search_request["limit"],
                        trace_id=trace_id,  # Pass trace_id to MCP
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
        trace_id = state.get("trace_id", str(uuid.uuid4()))
        agent_logger = get_core_agent_logger(trace_id)

        try:
            agent_logger.info(
                "Starting job applications", jobs_count=len(state["filtered_jobs"])
            )
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

            # Call LinkedIn MCP easy_apply_for_jobs tool with trace_id
            mcp_client = LinkedInMCPClientSync(self.server_host, self.server_port)
            application_results = mcp_client.easy_apply_for_jobs(
                applications=applications,
                cv_analysis=state["cv_analysis"],
                email=state["user_credentials"]["email"],
                password=state["user_credentials"]["password"],
                trace_id=trace_id,  # Pass trace_id to MCP
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
        # Generate single trace_id for this entire agent run
        trace_id = str(uuid.uuid4())

        # Configure logging with this trace_id
        from src.core.utils.logging_config import configure_core_agent_logging

        configure_core_agent_logging(default_trace_id=trace_id)

        # Get logger for this run
        agent_logger = get_core_agent_logger(trace_id)
        agent_logger.info(
            "Starting core agent run",
            job_searches_count=len(job_searches),
            cv_file_path=cv_file_path,
        )

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
            trace_id=trace_id,  # Add trace_id to state
        )

        # Execute the workflow with Langfuse observability
        from src.core.observability.langfuse_config import get_langfuse_callback

        callback_handler = get_langfuse_callback()

        # Prepare config for the invoke call
        invoke_config = {"configurable": {"trace_id": trace_id}} if trace_id else {}

        # Add callback handler if available (pass directly as callbacks param if supported)
        if callback_handler:
            try:
                final_state = self.graph.invoke(
                    initial_state, config=invoke_config, callbacks=[callback_handler]
                )
            except TypeError:
                # Fallback: try passing in config
                invoke_config["callbacks"] = [callback_handler]
                final_state = self.graph.invoke(initial_state, config=invoke_config)
        else:
            final_state = self.graph.invoke(initial_state, config=invoke_config)

        agent_logger.info(
            "Core agent run completed",
            total_jobs_found=final_state.get("total_jobs_found", 0),
            total_jobs_applied=final_state.get("total_jobs_applied", 0),
        )

        return final_state
