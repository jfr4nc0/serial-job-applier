import time
from typing import Any, Dict, List

from langgraph.graph import END, StateGraph
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from linkedin_mcp.linkedin.model.job_search_state import JobSearchState
from linkedin_mcp.linkedin.services.browser_manager_service import (
    BrowserManagerService as BrowserManager,
)
from linkedin_mcp.types import JobResult


class JobSearchGraph:
    """LangGraph workflow for LinkedIn job search RPA."""

    def __init__(self):
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create the job search workflow graph."""
        workflow = StateGraph(JobSearchState)

        # Add nodes for job search workflow
        workflow.add_node("build_search_url", self._build_search_url)
        workflow.add_node("navigate_to_search", self._navigate_to_search)
        workflow.add_node("extract_jobs_from_page", self._extract_jobs_from_page)
        workflow.add_node("check_pagination", self._check_pagination)
        workflow.add_node("navigate_next_page", self._navigate_next_page)

        # Define the workflow flow
        workflow.set_entry_point("build_search_url")
        workflow.add_edge("build_search_url", "navigate_to_search")
        workflow.add_edge("navigate_to_search", "extract_jobs_from_page")
        workflow.add_edge("extract_jobs_from_page", "check_pagination")

        # Conditional edge to check if we should continue to next page
        workflow.add_conditional_edges(
            "check_pagination",
            self._should_continue_pagination,
            {"continue": "navigate_next_page", "finish": END},
        )

        workflow.add_edge("navigate_next_page", "extract_jobs_from_page")

        return workflow.compile()

    def _build_search_url(self, state: JobSearchState) -> Dict[str, Any]:
        """Build the LinkedIn job search URL with filters."""
        base_url = "https://www.linkedin.com/jobs/search/"

        # Build search parameters
        params = []

        if state["job_title"]:
            params.append(f"keywords={state['job_title'].replace(' ', '%20')}")

        if state["location"]:
            params.append(f"location={state['location'].replace(' ', '%20')}")

        if state["easy_apply"]:
            params.append("f_LF=f_AL")  # Easy Apply filter

        # Construct the final URL
        search_url = base_url
        if params:
            search_url += "?" + "&".join(params)

        return {
            **state,
            "search_url": search_url,
            "current_page": 1,
        }

    def _navigate_to_search(self, state: JobSearchState) -> Dict[str, Any]:
        """Navigate to the job search results page."""
        try:
            state["browser_manager"].driver.get(state["search_url"])

            # Wait for results to load
            WebDriverWait(state["browser_manager"].driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-search-card"))
            )

            state["browser_manager"].random_delay(2, 4)

            return {
                **state,
            }

        except Exception as e:
            return {
                **state,
                "errors": state["errors"] + [f"Failed to navigate to search: {str(e)}"],
            }

    def _extract_jobs_from_page(self, state: JobSearchState) -> Dict[str, Any]:
        """Extract job listings from the current page."""
        try:
            driver = state["browser_manager"].driver
            job_cards = driver.find_elements(By.CLASS_NAME, "job-search-card")

            page_jobs = []

            for card in job_cards:
                try:
                    # Extract job ID from data attributes or href
                    job_link = card.find_element(By.CSS_SELECTOR, "h3 a")
                    job_url = job_link.get_attribute("href")

                    # Extract job ID from URL
                    job_id = None
                    if "/view/" in job_url:
                        job_id = int(job_url.split("/view/")[1].split("/")[0])

                    if not job_id:
                        continue

                    # Extract job description (summary from search results)
                    try:
                        description_element = card.find_element(
                            By.CSS_SELECTOR, ".job-search-card__snippet"
                        )
                        job_description = description_element.text.strip()
                    except NoSuchElementException:
                        job_description = "No description available"

                    # Only collect jobs if we haven't reached the limit
                    if len(state["collected_jobs"]) + len(page_jobs) < state["limit"]:
                        page_jobs.append(
                            JobResult(
                                id_job=job_id,
                                job_description=job_description,
                            )
                        )

                except Exception as e:
                    # Skip problematic job cards
                    continue

            return {
                **state,
                "collected_jobs": state["collected_jobs"] + page_jobs,
                "total_found": state["total_found"] + len(page_jobs),
            }

        except Exception as e:
            return {
                **state,
                "errors": state["errors"] + [f"Failed to extract jobs: {str(e)}"],
            }

    def _check_pagination(self, state: JobSearchState) -> Dict[str, Any]:
        """Check if there are more pages and if we should continue."""
        return state

    def _should_continue_pagination(self, state: JobSearchState) -> str:
        """Determine if we should continue to the next page."""
        # Stop if we've collected enough jobs
        if len(state["collected_jobs"]) >= state["limit"]:
            return "finish"

        # Stop if we've processed too many pages (safety limit)
        if state["current_page"] >= 10:
            return "finish"

        # Check if next page button exists
        try:
            driver = state["browser_manager"].driver
            next_button = driver.find_element(
                By.CSS_SELECTOR,
                "button[aria-label='View next page'], .artdeco-pagination__button--next",
            )

            # Check if the button is enabled
            if next_button.is_enabled() and not next_button.get_attribute("disabled"):
                return "continue"

        except NoSuchElementException:
            pass

        return "finish"

    def _navigate_next_page(self, state: JobSearchState) -> Dict[str, Any]:
        """Navigate to the next page of search results."""
        try:
            driver = state["browser_manager"].driver

            # Find and click the next page button
            next_button = driver.find_element(
                By.CSS_SELECTOR,
                "button[aria-label='View next page'], .artdeco-pagination__button--next",
            )

            next_button.click()
            state["browser_manager"].random_delay(3, 5)

            # Wait for new results to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-search-card"))
            )

            return {
                **state,
                "current_page": state["current_page"] + 1,
            }

        except Exception as e:
            return {
                **state,
                "errors": state["errors"]
                + [f"Failed to navigate to next page: {str(e)}"],
            }

    def execute(
        self,
        job_title: str,
        location: str,
        easy_apply: bool,
        limit: int,
        authenticated_browser_manager: BrowserManager,
    ) -> List[JobResult]:
        """Execute the job search workflow with pre-authenticated browser."""
        initial_state = JobSearchState(
            job_title=job_title,
            location=location,
            easy_apply=easy_apply,
            limit=limit,
            browser_manager=authenticated_browser_manager,
            current_page=1,
            collected_jobs=[],
            search_url=None,
            total_found=0,
            errors=[],
        )

        result = self.graph.invoke(initial_state)
        return result["collected_jobs"]
