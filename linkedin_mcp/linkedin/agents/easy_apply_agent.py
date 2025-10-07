from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from linkedin_mcp.linkedin.interfaces.agents import IJobApplicationAgent
from linkedin_mcp.linkedin.interfaces.services import IBrowserManager
from linkedin_mcp.linkedin.model.types import ApplicationRequest, CVAnalysis
from linkedin_mcp.linkedin.providers.llm_client import get_llm_client


class EasyApplyState(Dict):
    """State for the EasyApply agent workflow."""

    job_id: int
    monthly_salary: int
    cv_analysis: CVAnalysis
    browser_manager: IBrowserManager
    current_step: str
    form_questions: List[Dict[str, Any]]
    form_answers: Dict[str, Any]
    success: bool
    error: str


class EasyApplyAgent(IJobApplicationAgent):
    """
    AI-powered agent for handling LinkedIn Easy Apply forms using Qwen model.
    Analyzes form questions and provides intelligent answers based on CV data.
    """

    def __init__(self):
        self.graph = self._build_graph()
        # Initialize LLM model for form analysis
        self.model = get_llm_client()
        self.form_prompt = ChatPromptTemplate.from_template(
            """
        You are an AI assistant helping to fill out a LinkedIn job application form.

        Candidate Profile:
        - Skills: {skills}
        - Experience Years: {experience_years}
        - Previous Roles: {previous_roles}
        - Education: {education}
        - Certifications: {certifications}
        - Technologies: {technologies}
        - Key Achievements: {key_achievements}

        Form Question: {question}
        Question Type: {question_type}
        Available Options: {options}
        Expected Monthly Salary: ${monthly_salary}

        Instructions:
        1. If it's a salary question, use the expected monthly salary: ${monthly_salary}
        2. If it's about experience, use the experience years: {experience_years}
        3. For skills/technology questions, reference the relevant skills and technologies
        4. For education questions, use the education information
        5. For multiple choice, select the most appropriate option from the available choices
        6. For text fields, provide a concise, professional answer (max 200 characters)
        7. For yes/no questions, answer based on the candidate's profile

        Provide ONLY the answer value, nothing else. For multiple choice, provide the exact option text.

        Question: {question}
        """
        )

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for Easy Apply form handling."""
        workflow = StateGraph(EasyApplyState)

        # Add nodes
        workflow.add_node("navigate_to_job", self.navigate_to_job_node)
        workflow.add_node("click_easy_apply", self.click_easy_apply_node)
        workflow.add_node("analyze_form", self.analyze_form_node)
        workflow.add_node("fill_form", self.fill_form_node)
        workflow.add_node("submit_application", self.submit_application_node)

        # Define workflow flow
        workflow.set_entry_point("navigate_to_job")
        workflow.add_edge("navigate_to_job", "click_easy_apply")
        workflow.add_edge("click_easy_apply", "analyze_form")
        workflow.add_edge("analyze_form", "fill_form")
        workflow.add_edge("fill_form", "submit_application")
        workflow.add_edge("submit_application", END)

        return workflow.compile()

    def navigate_to_job_node(self, state: EasyApplyState) -> Dict[str, Any]:
        """Navigate to the specific job posting."""
        try:
            job_url = f"https://www.linkedin.com/jobs/view/{state['job_id']}/"
            state["browser_manager"].driver.get(job_url)

            # Wait for page to load
            WebDriverWait(state["browser_manager"].driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            state["browser_manager"].random_delay(2, 4)

            return {
                **state,
                "current_step": "navigated_to_job",
            }

        except Exception as e:
            return {
                **state,
                "success": False,
                "error": f"Failed to navigate to job: {str(e)}",
                "current_step": "navigation_failed",
            }

    def click_easy_apply_node(self, state: EasyApplyState) -> Dict[str, Any]:
        """Click the Easy Apply button."""
        try:
            driver = state["browser_manager"].driver

            # Multiple selectors for Easy Apply button
            easy_apply_selectors = [
                "button[aria-label*='Easy Apply']",
                "button[data-control-name='jobdetails_topcard_inapply']",
                ".jobs-apply-button--top-card button",
                "button.jobs-apply-button",
                "button:contains('Easy Apply')",
            ]

            easy_apply_button = None
            for selector in easy_apply_selectors:
                try:
                    if ":contains" in selector:
                        # Use XPath for text content search
                        easy_apply_button = driver.find_element(
                            By.XPATH, f"//button[contains(text(), 'Easy Apply')]"
                        )
                    else:
                        easy_apply_button = driver.find_element(
                            By.CSS_SELECTOR, selector
                        )
                    break
                except NoSuchElementException:
                    continue

            if not easy_apply_button:
                return {
                    **state,
                    "success": False,
                    "error": "Easy Apply button not found",
                    "current_step": "easy_apply_not_found",
                }

            # Click the Easy Apply button
            easy_apply_button.click()
            state["browser_manager"].random_delay(3, 5)

            return {
                **state,
                "current_step": "easy_apply_clicked",
            }

        except Exception as e:
            return {
                **state,
                "success": False,
                "error": f"Failed to click Easy Apply: {str(e)}",
                "current_step": "easy_apply_click_failed",
            }

    def analyze_form_node(self, state: EasyApplyState) -> Dict[str, Any]:
        """Analyze the Easy Apply form to extract questions and field types."""
        try:
            driver = state["browser_manager"].driver

            # Wait for form modal to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".jobs-easy-apply-modal, .artdeco-modal")
                )
            )

            form_questions = []

            # Look for different types of form fields
            # Text inputs
            text_inputs = driver.find_elements(
                By.CSS_SELECTOR, "input[type='text'], textarea"
            )
            for input_field in text_inputs:
                label = self._get_field_label(driver, input_field)
                if label:
                    form_questions.append(
                        {
                            "element": input_field,
                            "type": "text",
                            "question": label,
                            "options": None,
                        }
                    )

            # Select dropdowns
            selects = driver.find_elements(By.CSS_SELECTOR, "select")
            for select in selects:
                label = self._get_field_label(driver, select)
                options = [
                    option.text
                    for option in select.find_elements(By.TAG_NAME, "option")
                    if option.text.strip()
                ]
                if label:
                    form_questions.append(
                        {
                            "element": select,
                            "type": "select",
                            "question": label,
                            "options": options,
                        }
                    )

            # Radio buttons
            radio_groups = {}
            radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            for radio in radios:
                name = radio.get_attribute("name")
                if name not in radio_groups:
                    label = self._get_field_label(driver, radio)
                    radio_groups[name] = {
                        "elements": [],
                        "type": "radio",
                        "question": label or f"Radio group: {name}",
                        "options": [],
                    }
                radio_groups[name]["elements"].append(radio)

                # Get radio button label
                radio_label = self._get_radio_label(driver, radio)
                if radio_label:
                    radio_groups[name]["options"].append(radio_label)

            # Add radio groups to form questions
            for group_data in radio_groups.values():
                form_questions.append(group_data)

            return {
                **state,
                "form_questions": form_questions,
                "current_step": "form_analyzed",
            }

        except Exception as e:
            return {
                **state,
                "success": False,
                "error": f"Failed to analyze form: {str(e)}",
                "current_step": "form_analysis_failed",
            }

    def fill_form_node(self, state: EasyApplyState) -> Dict[str, Any]:
        """Fill the form using AI-generated answers based on CV analysis."""
        try:
            cv_analysis = state["cv_analysis"]
            form_answers = {}

            for question_data in state["form_questions"]:
                question = question_data["question"]
                question_type = question_data["type"]
                options = question_data.get("options", [])

                try:
                    # Get AI-generated answer
                    chain = self.form_prompt | self.model
                    response = chain.invoke(
                        {
                            "skills": ", ".join(cv_analysis["skills"]),
                            "experience_years": cv_analysis["experience_years"],
                            "previous_roles": ", ".join(cv_analysis["previous_roles"]),
                            "education": ", ".join(cv_analysis["education"]),
                            "certifications": ", ".join(cv_analysis["certifications"]),
                            "technologies": ", ".join(cv_analysis["technologies"]),
                            "key_achievements": ", ".join(
                                cv_analysis["key_achievements"]
                            ),
                            "monthly_salary": state["monthly_salary"],
                            "question": question,
                            "question_type": question_type,
                            "options": ", ".join(options) if options else "None",
                        }
                    )

                    answer = (
                        response.content.strip()
                        if hasattr(response, "content")
                        else str(response).strip()
                    )

                    # Fill the form field based on type
                    if question_type == "text":
                        question_data["element"].clear()
                        question_data["element"].send_keys(answer)

                    elif question_type == "select":
                        # Find the best matching option
                        best_option = self._find_best_option_match(answer, options)
                        if best_option:
                            select_element = question_data["element"]
                            for option in select_element.find_elements(
                                By.TAG_NAME, "option"
                            ):
                                if option.text == best_option:
                                    option.click()
                                    break

                    elif question_type == "radio":
                        # Find the best matching radio option
                        best_option = self._find_best_option_match(answer, options)
                        if best_option:
                            for i, radio_element in enumerate(
                                question_data["elements"]
                            ):
                                if i < len(options) and options[i] == best_option:
                                    radio_element.click()
                                    break

                    form_answers[question] = answer
                    state["browser_manager"].random_delay(1, 2)

                except Exception as e:
                    print(f"Error filling question '{question}': {str(e)}")
                    form_answers[question] = f"Error: {str(e)}"

            return {
                **state,
                "form_answers": form_answers,
                "current_step": "form_filled",
            }

        except Exception as e:
            return {
                **state,
                "success": False,
                "error": f"Failed to fill form: {str(e)}",
                "current_step": "form_fill_failed",
            }

    def submit_application_node(self, state: EasyApplyState) -> Dict[str, Any]:
        """Submit the Easy Apply application."""
        try:
            driver = state["browser_manager"].driver

            # Look for submit button
            submit_selectors = [
                "button[aria-label*='Submit application']",
                "button[data-control-name='continue_unify']",
                "button.artdeco-button--primary",
                "button:contains('Submit')",
                "button:contains('Send application')",
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    if ":contains" in selector:
                        # Use XPath for text content search
                        submit_button = driver.find_element(
                            By.XPATH,
                            f"//button[contains(text(), 'Submit') or contains(text(), 'Send application')]",
                        )
                    else:
                        submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue

            if not submit_button:
                return {
                    **state,
                    "success": False,
                    "error": "Submit button not found",
                    "current_step": "submit_button_not_found",
                }

            # Click submit button
            submit_button.click()
            state["browser_manager"].random_delay(3, 5)

            # Wait for confirmation or success message
            try:
                WebDriverWait(driver, 10).until(
                    EC.any_of(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ".artdeco-inline-feedback--success")
                        ),
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ".jobs-easy-apply-confirmation")
                        ),
                        EC.presence_of_element_located(
                            (By.XPATH, "//*[contains(text(), 'Application sent')]")
                        ),
                    )
                )

                return {
                    **state,
                    "success": True,
                    "current_step": "application_submitted",
                }

            except TimeoutException:
                # Application might still be successful even without confirmation
                return {
                    **state,
                    "success": True,
                    "current_step": "application_submitted_no_confirmation",
                    "error": "Application submitted but confirmation not detected",
                }

        except Exception as e:
            return {
                **state,
                "success": False,
                "error": f"Failed to submit application: {str(e)}",
                "current_step": "application_submit_failed",
            }

    def _get_field_label(self, driver, element) -> str:
        """Extract label text for a form field."""
        try:
            # Try to find associated label
            element_id = element.get_attribute("id")
            if element_id:
                try:
                    label = driver.find_element(
                        By.CSS_SELECTOR, f"label[for='{element_id}']"
                    )
                    return label.text.strip()
                except NoSuchElementException:
                    pass

            # Try to find parent label
            try:
                parent = element.find_element(By.XPATH, "..")
                label = parent.find_element(By.TAG_NAME, "label")
                return label.text.strip()
            except NoSuchElementException:
                pass

            # Try placeholder as fallback
            placeholder = element.get_attribute("placeholder")
            if placeholder:
                return placeholder.strip()

            # Try aria-label as fallback
            aria_label = element.get_attribute("aria-label")
            if aria_label:
                return aria_label.strip()

            return ""

        except Exception:
            return ""

    def _get_radio_label(self, driver, radio_element) -> str:
        """Get the label text for a radio button."""
        try:
            # Try to find associated label
            radio_id = radio_element.get_attribute("id")
            if radio_id:
                try:
                    label = driver.find_element(
                        By.CSS_SELECTOR, f"label[for='{radio_id}']"
                    )
                    return label.text.strip()
                except NoSuchElementException:
                    pass

            # Try parent element text
            try:
                parent = radio_element.find_element(By.XPATH, "..")
                text = parent.text.strip()
                if text and text not in ["", radio_element.get_attribute("value")]:
                    return text
            except Exception:
                pass

            # Fallback to value attribute
            return radio_element.get_attribute("value") or ""

        except Exception:
            return ""

    def _find_best_option_match(self, answer: str, options: List[str]) -> str:
        """Find the best matching option from available choices."""
        if not options:
            return ""

        answer_lower = answer.lower()

        # Direct match
        for option in options:
            if answer_lower == option.lower():
                return option

        # Partial match
        for option in options:
            if answer_lower in option.lower() or option.lower() in answer_lower:
                return option

        # Fallback to first option if no match
        return options[0] if options else ""

    def apply_to_job(
        self,
        job_id: str,
        application_request: ApplicationRequest,
        cv_analysis: CVAnalysis,
        browser_manager: IBrowserManager,
    ) -> Dict[str, Any]:
        """
        Apply to a single job using the Easy Apply workflow.

        Args:
            job_id: LinkedIn job ID
            application_request: Application details including salary expectations
            cv_analysis: Structured CV analysis for form filling
            browser_manager: Browser automation manager

        Returns:
            Dict with job_id, success status, and optional error message
        """
        initial_state = EasyApplyState(
            job_id=job_id,
            monthly_salary=application_request.monthly_salary,
            cv_analysis=cv_analysis,
            browser_manager=browser_manager,
            current_step="starting",
            form_questions=[],
            form_answers={},
            success=False,
            error="",
        )

        try:
            final_state = self.graph.invoke(initial_state)

            return {
                "job_id": job_id,
                "success": final_state.get("success", False),
                "error": final_state.get("error"),
                "form_answers": final_state.get("form_answers", {}),
                "current_step": final_state.get("current_step", "unknown"),
            }

        except Exception as e:
            return {
                "job_id": job_id,
                "success": False,
                "error": f"EasyApply workflow failed: {str(e)}",
                "form_answers": {},
                "current_step": "workflow_failed",
            }

    def is_easy_apply_available(
        self, job_id: str, browser_manager: IBrowserManager
    ) -> bool:
        """Check if Easy Apply is available for the job."""
        try:
            driver = browser_manager.get_driver()
            browser_manager.navigate_to_job(job_id)

            # Look for Easy Apply button
            easy_apply_button = driver.find_elements(
                By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]"
            )
            return len(easy_apply_button) > 0
        except Exception:
            return False
