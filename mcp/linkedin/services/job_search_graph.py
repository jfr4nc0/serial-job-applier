import re
import time
from typing import List, TypedDict
from urllib.parse import parse_qs, urlparse

from langgraph import END, StateGraph
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC

from mcp.linkedin.services.browser_manager import BrowserManager


class JobSearchState(TypedDict):
    job_title: str
    location: str
    easy_apply: bool
    browser_manager: BrowserManager
    job_listings: List[dict]
    current_page: int
    max_pages: int
    limit: int
    errors: List[str]


class JobSearchGraph:
    """LangGraph workflow for LinkedIn job search RPA."""

    def __init__(self):
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create the job search workflow graph."""
        workflow = StateGraph(JobSearchState)

        # Add nodes for each RPA step
        workflow.add_node("enter_search_criteria", self._enter_search_criteria)
        workflow.add_node("click_easy_apply_filter", self._click_easy_apply_filter)
        workflow.add_node("extract_jobs", self._extract_jobs)
        workflow.add_node("check_pagination", self._check_pagination)
        workflow.add_node("cleanup", self._cleanup)

        # Define the flow
        workflow.set_entry_point("enter_search_criteria")

        # Conditional edge for easy apply filter
        workflow.add_conditional_edges(
            "enter_search_criteria",
            self._should_apply_easy_filter,
            {"apply_filter": "click_easy_apply_filter", "skip_filter": "extract_jobs"},
        )

        workflow.add_edge("click_easy_apply_filter", "extract_jobs")
        workflow.add_edge("extract_jobs", "check_pagination")

        # Conditional edge for pagination
        workflow.add_conditional_edges(
            "check_pagination",
            self._should_continue_pagination,
            {"continue": "extract_jobs", "finish": "cleanup"},
        )

        workflow.add_edge("cleanup", END)

        return workflow.compile()

    def _enter_search_criteria(self, state: JobSearchState) -> JobSearchState:
        """Enter job title and location in search fields."""
        try:
            browser_manager = state["browser_manager"]
            driver = browser_manager.driver

            # Wait for the job search box to be present
            job_title_input = browser_manager.wait_for_element(
                By.CSS_SELECTOR, 'input[data-testid="typeahead-input"]'
            )

            # Clear and enter job title
            job_title_input.clear()
            job_title_input.send_keys(state["job_title"])
            browser_manager.random_delay(1, 2)

            # Find location input field (next to the location icon)
            location_input = driver.find_element(
                By.CSS_SELECTOR,
                'input[placeholder*="Location"], input[aria-label*="Location"], input[data-testid*="location"]',
            )

            # Clear and enter location
            location_input.clear()
            location_input.send_keys(state["location"])
            browser_manager.random_delay(1, 2)

            # Wait for location suggestions and select the first one
            try:
                # Wait for dropdown suggestions to appear
                time.sleep(2)

                # Try to select the first location suggestion
                location_suggestions = driver.find_elements(
                    By.CSS_SELECTOR,
                    '[role="listbox"] [role="option"], .basic-typeahead__item',
                )

                if location_suggestions:
                    location_suggestions[0].click()
                    browser_manager.random_delay(1, 2)
                else:
                    # If no suggestions, just press Enter
                    location_input.send_keys(Keys.ENTER)

            except Exception as e:
                # If location selection fails, continue anyway
                print(f"Location selection warning: {e}")

            # Click the Search button
            try:
                search_button = browser_manager.wait_for_clickable(
                    By.CSS_SELECTOR, "button.jobs-search-box__submit-button"
                )
                search_button.click()
            except TimeoutException:
                # Try alternative search button selectors
                alternative_selectors = [
                    "button.artdeco-button--secondary",
                    '[data-testid="search-button"]',
                    'button[aria-label*="Search"]',
                    'button[type="button"]',
                ]

                button_found = False
                for selector in alternative_selectors:
                    try:
                        buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        for button in buttons:
                            if "search" in button.text.lower():
                                button.click()
                                button_found = True
                                break
                        if button_found:
                            break
                    except NoSuchElementException:
                        continue

                if not button_found:
                    # Last resort: press Enter on the location field
                    location_input.send_keys(Keys.ENTER)

            browser_manager.random_delay(3, 5)

            return state

        except TimeoutException:
            state["errors"].append(
                "Search form elements not found - page structure may have changed"
            )
            return state
        except Exception as e:
            state["errors"].append(f"Failed to enter search criteria: {str(e)}")
            return state

    def _should_apply_easy_filter(self, state: JobSearchState) -> str:
        """Determine if we should apply the Easy Apply filter."""
        return "apply_filter" if state["easy_apply"] else "skip_filter"

    def _click_easy_apply_filter(self, state: JobSearchState) -> JobSearchState:
        """Click the Easy Apply filter button."""
        try:
            browser_manager = state["browser_manager"]
            driver = browser_manager.driver

            # Wait for the page to load after search
            browser_manager.random_delay(2, 3)

            # Find the Easy Apply filter button
            try:
                easy_apply_filter = browser_manager.wait_for_clickable(
                    By.ID, "searchFilter_applyWithLinkedin"
                )
                easy_apply_filter.click()
                browser_manager.random_delay(2, 3)

            except TimeoutException:
                # Try alternative selectors for Easy Apply filter
                alternative_selectors = [
                    'button[aria-label*="Easy Apply"]',
                    '.search-reusables__filter-pill-button[aria-label*="Easy Apply"]',
                    'button.artdeco-pill[aria-label*="Easy Apply"]',
                    "button.artdeco-pill--choice",
                ]

                filter_found = False
                for selector in alternative_selectors:
                    try:
                        filter_button = driver.find_element(By.CSS_SELECTOR, selector)
                        filter_button.click()
                        filter_found = True
                        browser_manager.random_delay(2, 3)
                        break

                    except NoSuchElementException:
                        continue

                # Last resort: search for buttons containing "Easy Apply" text
                if not filter_found:
                    try:
                        buttons = driver.find_elements(By.CSS_SELECTOR, "button")
                        for button in buttons:
                            if "easy apply" in button.text.lower():
                                button.click()
                                filter_found = True
                                browser_manager.random_delay(2, 3)
                                break
                    except Exception:
                        pass

                if not filter_found:
                    state["errors"].append("Easy Apply filter button not found")

            return state

        except Exception as e:
            state["errors"].append(f"Failed to apply Easy Apply filter: {str(e)}")
            return state

    def _extract_jobs(self, state: JobSearchState) -> JobSearchState:
        """Extract job listings from current page."""
        try:
            browser_manager = state["browser_manager"]
            driver = browser_manager.driver

            # Wait for the job results to load
            browser_manager.random_delay(3, 5)

            # Find the job results container
            try:
                results_container = browser_manager.wait_for_element(
                    By.CSS_SELECTOR, 'div[data-results-list-top-scroll-sentinel=""]'
                )
            except TimeoutException:
                # Try alternative selectors for job results
                alternative_containers = [
                    ".jobs-search__results-list",
                    ".jobs-search-results-list",
                    ".scaffold-layout__list-container",
                    "ul.jobs-search__results-list",
                ]

                results_container = None
                for selector in alternative_containers:
                    try:
                        results_container = driver.find_element(
                            By.CSS_SELECTOR, selector
                        )
                        break
                    except NoSuchElementException:
                        continue

                if not results_container:
                    state["errors"].append("Job results container not found")
                    return state

            # Find the job list within the container
            try:
                job_list = results_container.find_element(By.TAG_NAME, "ul")
                job_items = job_list.find_elements(By.TAG_NAME, "li")
            except NoSuchElementException:
                # Try direct approach if ul/li structure is different
                job_items = driver.find_elements(
                    By.CSS_SELECTOR,
                    ".jobs-search-results__list-item, .job-card-container, [data-occludable-job-id]",
                )

            if not job_items:
                state["errors"].append("No job listings found on page")
                return state

            # Calculate how many more jobs we need
            current_count = len(state["job_listings"])
            remaining_needed = state["limit"] - current_count

            if remaining_needed <= 0:
                # Already have enough jobs
                return state

            # Extract jobs from the current page (limit per page based on remaining needed)
            jobs_to_extract = min(
                len(job_items), remaining_needed, 25
            )  # Max 25 per page
            extracted_jobs = []

            for i, job_item in enumerate(job_items[:jobs_to_extract]):
                try:
                    job_data = self._extract_single_job(job_item, browser_manager, i)
                    if job_data:
                        extracted_jobs.append(job_data)

                        # Check if we've reached the limit
                        if (
                            len(state["job_listings"]) + len(extracted_jobs)
                            >= state["limit"]
                        ):
                            break

                except Exception as e:
                    print(f"Failed to extract job {i}: {str(e)}")
                    continue

            # Add extracted jobs to state
            state["job_listings"].extend(extracted_jobs)

            return state

        except Exception as e:
            state["errors"].append(f"Failed to extract jobs: {str(e)}")
            return state

    def _extract_single_job(self, job_item, browser_manager, job_index: int) -> dict:
        """Extract data from a single job listing."""
        try:
            driver = browser_manager.driver

            # Click on the job item to load details
            job_item.click()
            browser_manager.random_delay(2, 4)

            # Extract job_id from URL
            current_url = driver.current_url
            job_id = self._extract_job_id_from_url(current_url)

            if not job_id:
                print(f"Could not extract job_id from URL: {current_url}")
                return None

            # Extract job description
            job_description = self._extract_job_description(browser_manager)

            if not job_description:
                print(f"Could not extract job description for job_id: {job_id}")
                job_description = "Description not available"

            return {"id": job_id, "description": job_description}

        except Exception as e:
            print(f"Error extracting job {job_index}: {str(e)}")
            return None

    def _extract_job_id_from_url(self, url: str) -> int:
        """Extract job_id from LinkedIn job URL."""
        try:
            # Parse URL to get query parameters
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)

            # Look for currentJobId parameter
            if "currentJobId" in query_params:
                job_id = query_params["currentJobId"][0]
                return int(job_id)

            # Alternative: extract from URL path patterns
            # Pattern like /jobs/view/4294645063/
            path_match = re.search(r"/jobs/view/(\d+)", url)
            if path_match:
                return int(path_match.group(1))

            # Another pattern: ?jobId=123456
            job_id_match = re.search(r"jobId=(\d+)", url)
            if job_id_match:
                return int(job_id_match.group(1))

            return None

        except Exception as e:
            print(f"Error extracting job_id from URL {url}: {str(e)}")
            return None

    def _extract_job_description(self, browser_manager) -> str:
        """Extract job description from the job details panel."""
        try:
            driver = browser_manager.driver

            # Wait for job description to load
            try:
                description_container = browser_manager.wait_for_element(
                    By.CSS_SELECTOR,
                    ".jobs-box__html-content, #job-details, .jobs-description-content__text--stretch",
                )
            except TimeoutException:
                # Try alternative selectors
                alternative_selectors = [
                    ".job-view-description",
                    ".jobs-description",
                    ".job-details-description",
                    '[class*="job-description"]',
                    '[class*="description-content"]',
                ]

                description_container = None
                for selector in alternative_selectors:
                    try:
                        description_container = driver.find_element(
                            By.CSS_SELECTOR, selector
                        )
                        break
                    except NoSuchElementException:
                        continue

                if not description_container:
                    return "Description container not found"

            # Extract text content, removing extra whitespace
            description_text = (
                description_container.get_attribute("innerText")
                or description_container.text
            )

            if not description_text.strip():
                # Try getting innerHTML and clean it up
                description_html = description_container.get_attribute("innerHTML")
                if description_html:
                    # Basic HTML tag removal
                    description_text = re.sub(r"<[^>]+>", " ", description_html)
                    description_text = re.sub(r"\s+", " ", description_text).strip()

            return (
                description_text.strip()
                if description_text
                else "Description not available"
            )

        except Exception as e:
            print(f"Error extracting job description: {str(e)}")
            return "Error extracting description"

    def _check_pagination(self, state: JobSearchState) -> JobSearchState:
        """Check if there are more pages to process and navigate to next page if needed."""
        try:
            browser_manager = state["browser_manager"]
            driver = browser_manager.driver

            # Check if we've reached the limit
            if len(state["job_listings"]) >= state["limit"]:
                # We have enough jobs, no need to continue
                return state

            # Check if we've reached max pages
            if state["current_page"] >= state["max_pages"]:
                # Reached maximum pages limit
                return state

            # Look for the next page button
            try:
                # Try to find the next page button with the chevron-right icon
                next_button = browser_manager.wait_for_clickable(
                    By.CSS_SELECTOR,
                    'button[aria-label*="Next"], button[data-test-icon="chevron-right-small"]',
                )

                # Check if the button is enabled (not disabled)
                if next_button.get_attribute(
                    "disabled"
                ) or "disabled" in next_button.get_attribute("class"):
                    # No more pages available
                    return state

                # Click the next page button
                next_button.click()
                browser_manager.random_delay(3, 5)

                # Increment current page
                state["current_page"] += 1

                return state

            except TimeoutException:
                # Try alternative selectors for next page button
                alternative_selectors = [
                    'button[aria-label*="next page"]',
                    'button[aria-label*="Next page"]',
                    'a[aria-label*="Next"]',
                    ".artdeco-pagination__button--next",
                    '[data-testid="pagination-next"]',
                    'button:has(svg[data-test-icon="chevron-right-small"])',
                ]

                next_button_found = False
                for selector in alternative_selectors:
                    try:
                        if ":has(" in selector:
                            # Handle :has() pseudo-selector differently
                            buttons = driver.find_elements(By.CSS_SELECTOR, "button")
                            for button in buttons:
                                try:
                                    svg = button.find_element(
                                        By.CSS_SELECTOR,
                                        'svg[data-test-icon="chevron-right-small"]',
                                    )
                                    if svg and not (
                                        button.get_attribute("disabled")
                                        or "disabled" in button.get_attribute("class")
                                    ):
                                        button.click()
                                        next_button_found = True
                                        break
                                except NoSuchElementException:
                                    continue
                        else:
                            next_button = driver.find_element(By.CSS_SELECTOR, selector)
                            if not (
                                next_button.get_attribute("disabled")
                                or "disabled" in next_button.get_attribute("class")
                            ):
                                next_button.click()
                                next_button_found = True

                        if next_button_found:
                            browser_manager.random_delay(3, 5)
                            state["current_page"] += 1
                            break

                    except NoSuchElementException:
                        continue

                if not next_button_found:
                    # No next page button found - we're on the last page
                    print("No next page button found - reached end of results")

                return state

        except Exception as e:
            print(f"Error during pagination check: {str(e)}")
            return state

    def _cleanup(self, state: JobSearchState) -> JobSearchState:
        """Clean up browser resources."""
        # RPA step implementation will go here
        pass

    def _should_continue_pagination(self, state: JobSearchState) -> str:
        """Determine if we should continue to next page."""
        # Check if we have enough jobs
        if len(state["job_listings"]) >= state["limit"]:
            return "finish"

        # Check if we've reached max pages
        if state["current_page"] >= state["max_pages"]:
            return "finish"

        # Check for errors
        if len(state["errors"]) > 0:
            return "finish"

        # Continue if we need more jobs and haven't reached limits
        return "continue"

    def execute(
        self,
        job_title: str,
        location: str,
        easy_apply: bool,
        authenticated_browser_manager,
        limit: int = 50,
    ) -> List[dict]:
        """Execute the job search workflow with pre-authenticated browser."""
        initial_state = JobSearchState(
            job_title=job_title,
            location=location,
            easy_apply=easy_apply,
            browser_manager=authenticated_browser_manager,
            job_listings=[],
            current_page=1,
            max_pages=10,  # Allow up to 10 pages
            limit=limit,
            errors=[],
        )

        result = self.graph.invoke(initial_state)
        return result["job_listings"]
