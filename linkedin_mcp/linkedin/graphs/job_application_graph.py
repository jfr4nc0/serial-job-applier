from typing import Any, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from linkedin_mcp.linkedin.interfaces.agents import IJobApplicationAgent
from linkedin_mcp.linkedin.interfaces.services import IBrowserManager
from linkedin_mcp.linkedin.model.types import ApplicationRequest, CVAnalysis


class JobApplicationState(TypedDict):
    applications: List[ApplicationRequest]
    cv_analysis: CVAnalysis
    browser_manager: IBrowserManager
    current_application_index: int
    application_results: List[dict]
    current_application: Optional[ApplicationRequest]
    job_application_agent: IJobApplicationAgent
    errors: List[str]


class JobApplicationGraph:
    """LangGraph workflow for LinkedIn job application RPA."""

    def __init__(
        self,
        job_application_agent: IJobApplicationAgent,
        browser_manager: IBrowserManager,
    ):
        self.job_application_agent = job_application_agent
        self.browser_manager = browser_manager
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create the job application workflow graph."""
        workflow = StateGraph(JobApplicationState)

        # Add nodes for job application workflow
        workflow.add_node("initialize_agent", self._initialize_agent)
        workflow.add_node("select_next_application", self._select_next_application)
        workflow.add_node("process_application", self._process_application)
        workflow.add_node("record_result", self._record_result)

        # Define the simplified flow
        workflow.set_entry_point("initialize_agent")
        workflow.add_edge("initialize_agent", "select_next_application")

        # Conditional edge to check if there are more applications
        workflow.add_conditional_edges(
            "select_next_application",
            self._has_more_applications,
            {"continue": "process_application", "finish": END},
        )

        workflow.add_edge("process_application", "record_result")
        workflow.add_edge("record_result", "select_next_application")

        return workflow.compile()

    def _initialize_agent(self, state: JobApplicationState) -> JobApplicationState:
        """Initialize the job application agent."""
        return {
            **state,
            "job_application_agent": self.job_application_agent,
            "browser_manager": self.browser_manager,
            "current_application_index": 0,
        }

    def _select_next_application(
        self, state: JobApplicationState
    ) -> JobApplicationState:
        """Select the next application to process."""
        if state["current_application_index"] < len(state["applications"]):
            current_application = state["applications"][
                state["current_application_index"]
            ]
            return {**state, "current_application": current_application}
        else:
            return state

    def _process_application(self, state: JobApplicationState) -> JobApplicationState:
        """Process a single job application using the EasyApply agent."""
        try:
            current_app = state["current_application"]
            result = state["job_application_agent"].apply_to_job(
                job_id=current_app["job_id"],
                application_request=current_app,
                cv_analysis=state["cv_analysis"],
                browser_manager=state["browser_manager"],
            )

            return {
                **state,
                "application_results": state["application_results"] + [result],
            }

        except Exception as e:
            error_result = {
                "job_id": state["current_application"]["job_id"],
                "success": False,
                "error": f"Application processing failed: {str(e)}",
            }

            return {
                **state,
                "application_results": state["application_results"] + [error_result],
                "errors": state["errors"] + [str(e)],
            }

    def _record_result(self, state: JobApplicationState) -> JobApplicationState:
        """Update the application index to move to next application."""
        return {
            **state,
            "current_application_index": state["current_application_index"] + 1,
        }

    def _has_more_applications(self, state: JobApplicationState) -> str:
        """Check if there are more applications to process."""
        if state["current_application_index"] < len(state["applications"]):
            return "continue"
        return "finish"

    def execute(
        self,
        applications: List[ApplicationRequest],
        cv_analysis: CVAnalysis,
        authenticated_browser_manager: IBrowserManager,
    ) -> List[dict]:
        """Execute the job application workflow with pre-authenticated browser."""
        initial_state = JobApplicationState(
            applications=applications,
            cv_analysis=cv_analysis,
            browser_manager=authenticated_browser_manager,
            current_application_index=0,
            application_results=[],
            current_application=None,
            job_application_agent=None,
            errors=[],
        )

        result = self.graph.invoke(initial_state)
        return result["application_results"]
