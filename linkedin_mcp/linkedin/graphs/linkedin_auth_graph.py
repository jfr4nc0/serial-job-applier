from langgraph.graph import END, StateGraph
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from linkedin_mcp.linkedin.interfaces.services import IBrowserManager
from linkedin_mcp.linkedin.model.types import AuthState


class LinkedInAuthGraph:
    """LangGraph workflow for LinkedIn authentication."""

    def __init__(self):
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create the authentication workflow graph."""
        workflow = StateGraph(AuthState)

        # Add nodes for authentication steps
        workflow.add_node("navigate_to_login", self._navigate_to_login)
        workflow.add_node("fill_credentials", self._fill_credentials)
        workflow.add_node("submit_login", self._submit_login)
        workflow.add_node("verify_authentication", self._verify_authentication)

        # Define the flow
        workflow.set_entry_point("navigate_to_login")
        workflow.add_edge("navigate_to_login", "fill_credentials")
        workflow.add_edge("fill_credentials", "submit_login")
        workflow.add_edge("submit_login", "verify_authentication")
        workflow.add_edge("verify_authentication", END)

        return workflow.compile()

    def _navigate_to_login(self, state: AuthState) -> AuthState:
        """Navigate to LinkedIn jobs page."""
        try:
            driver = state["browser_manager"].driver
            driver.get("https://www.linkedin.com/jobs/")
            state["browser_manager"].random_delay(2, 4)
            return state
        except Exception as e:
            state["error"] = f"Failed to navigate to LinkedIn: {str(e)}"
            return state

    def _fill_credentials(self, state: AuthState) -> AuthState:
        """Fill email and password fields."""
        try:
            browser_manager = state["browser_manager"]

            # Wait for and fill email field
            email_field = browser_manager.wait_for_element(By.ID, "session_key")
            email_field.clear()
            email_field.send_keys(state["email"])
            browser_manager.random_delay(1, 2)

            # Wait for and fill password field
            password_field = browser_manager.wait_for_element(By.ID, "session_password")
            password_field.clear()
            password_field.send_keys(state["password"])
            browser_manager.random_delay(1, 2)

            return state

        except TimeoutException:
            state["error"] = "Login form not found - page structure may have changed"
            return state
        except Exception as e:
            state["error"] = f"Failed to fill credentials: {str(e)}"
            return state

    def _submit_login(self, state: AuthState) -> AuthState:
        """Click the Sign In button."""
        try:
            browser_manager = state["browser_manager"]

            # Find and click the Sign In button
            sign_in_btn = browser_manager.wait_for_clickable(
                By.CSS_SELECTOR, 'button[data-id="sign-in-form__submit-btn"]'
            )
            sign_in_btn.click()
            browser_manager.random_delay(3, 5)

            return state

        except TimeoutException:
            state["error"] = "Sign In button not found"
            return state
        except Exception as e:
            state["error"] = f"Failed to submit login: {str(e)}"
            return state

    def _verify_authentication(self, state: AuthState) -> AuthState:
        """Verify that authentication was successful."""
        try:
            driver = state["browser_manager"].driver
            current_url = driver.current_url

            # Check if we're redirected away from login page
            if "/jobs/" in current_url and "/login" not in current_url:
                state["authenticated"] = True
            else:
                state["authenticated"] = False
                state["error"] = "Login failed - still on login page"

            return state

        except Exception as e:
            state["authenticated"] = False
            state["error"] = f"Authentication verification error: {str(e)}"
            return state

    def execute(
        self, email: str, password: str, browser_manager: "IBrowserManager"
    ) -> AuthState:
        """Execute the authentication workflow."""
        initial_state = AuthState(
            email=email,
            password=password,
            browser_manager=browser_manager,
            authenticated=False,
            error="",
        )

        result = self.graph.invoke(initial_state)
        return result
